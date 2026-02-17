import cv2
import mediapipe as mp
import numpy as np


class GestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
            max_num_hands=1
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

        self.frame_rgb = None      # latest processed frame (RGB) for blit
        self.gesture   = "none"    # "open" | "pinch" | "none"

    # ── helpers ──────────────────────────────────────────
    def _dist(self, a, b):
        return np.hypot(a.x - b.x, a.y - b.y)

    def _finger_up(self, lm, tip, pip):
        """True if finger is extended (tip above pip)."""
        return lm[tip].y < lm[pip].y

    # ── main update call ─────────────────────────────────
    def update(self):
        """Call once per frame. Updates self.gesture and self.frame_rgb."""
        ok, frame = self.cap.read()
        if not ok:
            self.frame_rgb = None
            self.gesture   = "none"
            return

        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        self.gesture = "none"

        if results.multi_hand_landmarks:
            lm   = results.multi_hand_landmarks[0].landmark
            h, w = frame.shape[:2]

            # ── Thumb + index distance (pinch measure) ──
            thumb_tip  = lm[4]
            index_tip  = lm[8]
            pinch_dist = self._dist(thumb_tip, index_tip)

            # ── Are fingers open? ──
            index_up  = self._finger_up(lm, 8,  6)
            middle_up = self._finger_up(lm, 12, 10)
            ring_up   = self._finger_up(lm, 16, 14)
            pinky_up  = self._finger_up(lm, 20, 18)

            fingers_open = sum([index_up, middle_up, ring_up, pinky_up])

            if pinch_dist < 0.06:               # thumb & index close → PINCH
                self.gesture = "pinch"
            elif fingers_open >= 3:              # most fingers open → OPEN
                self.gesture = "open"

            # ── Draw overlay ──
            thumb_px  = (int(thumb_tip.x * w), int(thumb_tip.y * h))
            index_px  = (int(index_tip.x * w), int(index_tip.y * h))

            color = (80, 200, 120) if self.gesture == "open" else (220, 80, 80)
            cv2.circle(frame, thumb_px,  9, color, -1)
            cv2.circle(frame, index_px,  9, color, -1)
            cv2.line(frame, thumb_px, index_px, color, 2)

            label = "OPEN → JUMP" if self.gesture == "open" else (
                    "PINCH → RUN" if self.gesture == "pinch" else "")
            cv2.putText(frame, label, (8, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        # Store as RGB for pygame
        self.frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ── public getters ───────────────────────────────────
    def is_open(self):
        return self.gesture == "open"

    def is_pinch(self):
        return self.gesture == "pinch"

    def get_frame(self):
        return self.frame_rgb      # numpy HxWx3 RGB

    def close(self):
        self.cap.release()