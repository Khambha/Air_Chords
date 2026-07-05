# vision/hand_tracker.py
# KEY FIX: track by hand INDEX (0,1) not by Left/Right label.
# After flipping the frame, MediaPipe's Left/Right labels are unreliable
# for determining screen position. We use x-position to assign Left/Right wheel.

import mediapipe as mp
import cv2
import numpy as np
from dataclasses import dataclass
from config import (MP_MAX_HANDS, MP_MIN_DETECTION_CONFIDENCE,
                    MP_MIN_TRACKING_CONFIDENCE, PINCH_THRESHOLD_LEFT,
                    PINCH_RELEASE_LEFT, PINCH_THRESHOLD_RIGHT,
                    PINCH_RELEASE_RIGHT)

mp_hands = mp.solutions.hands


@dataclass
class HandData:
    screen_side: str     # "left" or "right" — based on SCREEN x position
    index_tip: tuple     # normalized (x, y)
    thumb_tip: tuple     # normalized (x, y)
    wrist: tuple         # normalized (x, y)
    pinch_dist: float
    is_pinching: bool


class HandTracker:
    def __init__(self):
        self._hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=MP_MAX_HANDS,
            min_detection_confidence=MP_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MP_MIN_TRACKING_CONFIDENCE,
        )
        # Hysteresis state keyed by screen_side
        self._pinch_state: dict[str, bool] = {"left": False, "right": False}

    def process(self, frame_bgr: np.ndarray) -> dict[str, HandData]:
        """
        Returns dict: {"left": HandData, "right": HandData}
        Hands are assigned left/right purely by their wrist x-position on screen.
        Frame must already be flipped before passing in.
        """
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self._hands.process(rgb)
        rgb.flags.writeable = True

        detected: list[dict] = []
        if results.multi_hand_landmarks:
            for lm_list in results.multi_hand_landmarks:
                lms = lm_list.landmark
                thumb = (lms[4].x,  lms[4].y)
                index = (lms[8].x,  lms[8].y)
                wrist = (lms[0].x,  lms[0].y)
                dist  = float(np.hypot(thumb[0] - index[0],
                                        thumb[1] - index[1]))
                detected.append({
                    "wrist_x": wrist[0],
                    "thumb":   thumb,
                    "index":   index,
                    "wrist":   wrist,
                    "dist":    dist,
                })

        # Sort by wrist x: leftmost hand → screen left wheel
        detected.sort(key=lambda h: h["wrist_x"])

        sides = []
        if len(detected) == 1:
            # Assign based on which half of screen the hand is in
            side = "left" if detected[0]["wrist_x"] < 0.5 else "right"
            sides = [side]
        elif len(detected) >= 2:
            sides = ["left", "right"]

        output: dict[str, HandData] = {}
        for i, side in enumerate(sides):
            d = detected[i]
            # Hysteresis pinch
            prev = self._pinch_state[side]
            thresh = PINCH_THRESHOLD_LEFT if side == "left" else PINCH_THRESHOLD_RIGHT
            release = PINCH_RELEASE_LEFT if side == "left" else PINCH_RELEASE_RIGHT
            
            if not prev and d["dist"] < thresh:
                self._pinch_state[side] = True
            elif prev and d["dist"] > release:
                self._pinch_state[side] = False

            output[side] = HandData(
                screen_side=side,
                index_tip=d["index"],
                thumb_tip=d["thumb"],
                wrist=d["wrist"],
                pinch_dist=d["dist"],
                is_pinching=self._pinch_state[side],
            )

        # Reset pinch state for hands no longer visible
        for side in ["left", "right"]:
            if side not in output:
                self._pinch_state[side] = False

        return output

    def close(self):
        self._hands.close()