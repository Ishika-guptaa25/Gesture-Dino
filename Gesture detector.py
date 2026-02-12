import cv2
import mediapipe as mp
import numpy as np
import json
import threading
from collections import deque
from enum import Enum


class GestureType(Enum):
    IDLE = "idle"
    JUMP = "jump"
    DUCK = "duck"


class GestureDetector:
    def __init__(self, history_size=10, jump_threshold=0.3, duck_threshold=0.3):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

        self.gesture_history = deque(maxlen=history_size)
        self.jump_threshold = jump_threshold
        self.duck_threshold = duck_threshold
        self.current_gesture = GestureType.IDLE
        self.frame_count = 0

    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)

    def get_shoulder_height(self, landmarks):
        """Get average height of shoulders"""
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        return (left_shoulder.y + right_shoulder.y) / 2

    def get_wrist_height(self, landmarks):
        """Get average height of wrists"""
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        return (left_wrist.y + right_wrist.y) / 2

    def get_hip_height(self, landmarks):
        """Get average height of hips"""
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        return (left_hip.y + right_hip.y) / 2

    def detect_jump(self, landmarks):
        """
        Jump detection: Both arms raised above shoulders
        Jump is detected when wrists are significantly above shoulder height
        """
        shoulder_height = self.get_shoulder_height(landmarks)
        wrist_height = self.get_wrist_height(landmarks)

        # Wrists should be above shoulders for jump
        return wrist_height < (shoulder_height - self.jump_threshold)

    def detect_duck(self, landmarks):
        """
        Duck detection: Body bent down, hips lower than normal
        Detected when hip height increases (moves down) relative to shoulder
        """
        shoulder_height = self.get_shoulder_height(landmarks)
        hip_height = self.get_hip_height(landmarks)

        # Hips should be above shoulders (lower y value) when normal
        # If hips are below shoulders or very close, it's a duck
        return hip_height > (shoulder_height + self.duck_threshold)

    def smoothed_gesture(self):
        """
        Return smoothed gesture based on history to reduce false positives
        A gesture is confirmed if it appears in at least 60% of recent frames
        """
        if len(self.gesture_history) < 3:
            return GestureType.IDLE

        recent = list(self.gesture_history)[-5:]
        jump_count = sum(1 for g in recent if g == GestureType.JUMP)
        duck_count = sum(1 for g in recent if g == GestureType.DUCK)

        if jump_count >= 3:
            return GestureType.JUMP
        elif duck_count >= 3:
            return GestureType.DUCK
        else:
            return GestureType.IDLE

    def process_frame(self, frame):
        """
        Process a single frame and detect gestures
        Returns: annotated frame, detected gesture
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)

        annotated_frame = frame.copy()
        current_frame_gesture = GestureType.IDLE

        if results.landmarks:
            landmarks = results.landmarks

            # Detect gestures
            if self.detect_jump(landmarks):
                current_frame_gesture = GestureType.JUMP
            elif self.detect_duck(landmarks):
                current_frame_gesture = GestureType.DUCK

            # Add to history
            self.gesture_history.append(current_frame_gesture)

            # Get smoothed gesture
            self.current_gesture = self.smoothed_gesture()

            # Draw pose landmarks on frame
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                results.landmarks,
                self.mp_pose.CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(200, 180, 255), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(200, 180, 255), thickness=2)
            )

        # Draw gesture indicator on frame
        self._draw_gesture_indicator(annotated_frame)

        self.frame_count += 1
        return annotated_frame, self.current_gesture

    def _draw_gesture_indicator(self, frame):
        """Draw gesture indicator text on frame"""
        height, width, _ = frame.shape

        gesture_text = self.current_gesture.value.upper()
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.5
        font_color = (255, 255, 255)
        font_thickness = 3

        # Background color based on gesture
        if self.current_gesture == GestureType.JUMP:
            bg_color = (255, 182, 193)  # Light pink for jump
        elif self.current_gesture == GestureType.DUCK:
            bg_color = (180, 231, 216)  # Light teal for duck
        else:
            bg_color = (200, 200, 200)  # Gray for idle

        text_size = cv2.getTextSize(gesture_text, font, font_scale, font_thickness)[0]
        padding = 10

        # Draw rounded rectangle background
        x, y = 20, 40
        cv2.rectangle(
            frame,
            (x - padding, y - text_size[1] - padding),
            (x + text_size[0] + padding, y + padding),
            bg_color,
            -1
        )

        # Draw text
        cv2.putText(
            frame,
            gesture_text,
            (x, y),
            font,
            font_scale,
            font_color,
            font_thickness
        )

        # Draw frame info
        info_text = f"Frame: {self.frame_count}"
        cv2.putText(frame, info_text, (20, height - 20), font, 0.6, (150, 150, 150), 1)


class WebcamGestureApp:
    def __init__(self, window_name="Gesture Dino Control"):
        self.detector = GestureDetector()
        self.window_name = window_name
        self.running = True
        self.gesture_callback = None

    def set_gesture_callback(self, callback):
        """Set callback function to be called when gesture is detected"""
        self.gesture_callback = callback

    def run(self):
        """Run the webcam gesture detection app"""
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: Could not open webcam")
            return

        # Set camera properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        print("Starting gesture detection. Press 'q' to quit.")

        prev_gesture = GestureType.IDLE

        while self.running:
            ret, frame = cap.read()

            if not ret:
                print("Failed to read frame from webcam")
                break

            # Mirror frame for intuitive interaction
            frame = cv2.flip(frame, 1)

            # Process frame
            annotated_frame, gesture = self.detector.process_frame(frame)

            # Call gesture callback if gesture changed
            if gesture != prev_gesture and gesture != GestureType.IDLE:
                if self.gesture_callback:
                    self.gesture_callback(gesture.value)
                print(f"Detected gesture: {gesture.value}")

            prev_gesture = gesture

            # Display frame
            cv2.imshow(self.window_name, annotated_frame)

            # Break on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def stop(self):
        """Stop the app"""
        self.running = False


def gesture_callback(gesture_name):
    """Example callback function"""
    print(f"Gesture detected: {gesture_name}")


if __name__ == "__main__":
    app = WebcamGestureApp()
    app.set_gesture_callback(gesture_callback)
    app.run()