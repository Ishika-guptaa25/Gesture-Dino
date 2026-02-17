"""
Gesture Detection
─────────────────
L-shape  (thumb out + index up, rest curled) → JUMP
Fist     (all 5 fingers curled)               → DUCK
Pinch    (thumb tip near index tip)           → RUN (neutral)
"""
import cv2
import mediapipe as mp
import numpy as np


class GestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands    = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.6,
        )
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.gesture   = "none"   # "jump" | "duck" | "run" | "none"
        self.frame_rgb = None

    # ── low-level helpers ────────────────────────────────────
    @staticmethod
    def _dist(a, b):
        return np.hypot(a.x - b.x, a.y - b.y)

    @staticmethod
    def _finger_up(lm, tip, pip):
        """Finger extended = tip above pip (lower y value)."""
        return lm[tip].y < lm[pip].y - 0.02

    @staticmethod
    def _thumb_up(lm):
        """Thumb extended = tip left of ip (for right hand, mirrored feed)."""
        return lm[4].x > lm[3].x + 0.02

    # ── gesture logic ────────────────────────────────────────
    def _classify(self, lm):
        index  = self._finger_up(lm, 8,  6)
        middle = self._finger_up(lm, 12, 10)
        ring   = self._finger_up(lm, 16, 14)
        pinky  = self._finger_up(lm, 20, 18)
        thumb  = self._thumb_up(lm)
        pinch_dist = self._dist(lm[4], lm[8])

        # ── PINCH: thumb tip near index tip ──────────────────
        if pinch_dist < 0.07:
            return "run"

        # ── FIST: all 4 fingers curled (thumb position free) ─
        if not index and not middle and not ring and not pinky:
            return "duck"

        # ── L-SHAPE: thumb out + index up, rest curled ───────
        if thumb and index and not middle and not ring and not pinky:
            return "jump"

        return "none"

    # ── per-frame update ─────────────────────────────────────
    def update(self):
        ok, frame = self.cap.read()
        if not ok:
            self.frame_rgb = None
            return

        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res   = self.hands.process(rgb)

        self.gesture = "none"

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark
            self.gesture = self._classify(lm)

            # ── draw landmarks ──
            h, w = frame.shape[:2]

            COLOR_MAP = {
                "jump": (80,  200, 80),
                "duck": (80,  80,  255),
                "run":  (255, 180, 0),
                "none": (180, 180, 180),
            }
            col = COLOR_MAP[self.gesture]

            # Draw dots for key landmarks
            key_pts = [4, 8, 12, 16, 20, 0]
            for idx in key_pts:
                px = (int(lm[idx].x * w), int(lm[idx].y * h))
                cv2.circle(frame, px, 7, col, -1)

            # Thumb–index line
            t = (int(lm[4].x * w), int(lm[4].y * h))
            i = (int(lm[8].x * w), int(lm[8].y * h))
            cv2.line(frame, t, i, col, 2)

            # Label
            labels = {
                "jump": "L-SHAPE -> JUMP",
                "duck": "FIST    -> DUCK",
                "run":  "PINCH   -> RUN",
                "none": "...",
            }
            cv2.putText(frame, labels[self.gesture],
                        (6, 22), cv2.FONT_HERSHEY_SIMPLEX,
                        0.55, col, 2, cv2.LINE_AA)

        self.frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ── public getters ───────────────────────────────────────
    def is_jump(self):  return self.gesture == "jump"
    def is_duck(self):  return self.gesture == "duck"
    def is_run(self):   return self.gesture == "run"
    def get_frame(self): return self.frame_rgb

    def close(self):
        self.cap.release()