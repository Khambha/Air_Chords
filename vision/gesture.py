# vision/gesture.py
# Left wheel  → root note (C D E F G A B)
# Right wheel → chord quality (maj min dom7 maj7 min7 sus2 sus4 dim aug)

import numpy as np
import math
from dataclasses import dataclass
from config import LEFT_WHEEL_CENTER, RIGHT_WHEEL_CENTER
from audio.scales import ROOT_NOTES, CHORD_QUALITIES


@dataclass
class WheelState:
    side: str           # "left" or "right"
    angle_deg: float
    sector: int         # index into ROOT_NOTES or CHORD_QUALITIES
    is_pinching: bool
    pinch_dist: float
    tip_pos: tuple


def _angle_clockwise_from_top(cx, cy, tx, ty) -> float:
    """0° = top, clockwise."""
    dx, dy = tx - cx, ty - cy
    return (math.degrees(math.atan2(dy, dx)) + 90) % 360


def _sector_from_angle(angle: float, n: int) -> int:
    sector_deg = 360.0 / n
    return int((angle + sector_deg / 2) % 360 / sector_deg) % n


class GestureMapper:
    def map(self, hands: dict) -> dict[str, WheelState]:
        states = {}

        for side, hand in hands.items():
            cx, cy = (LEFT_WHEEL_CENTER if side == "left"
                      else RIGHT_WHEEL_CENTER)
            angle = _angle_clockwise_from_top(cx, cy,
                                               hand.index_tip[0],
                                               hand.index_tip[1])
            if side == "left":
                n = len(ROOT_NOTES)
            else:
                n = len(CHORD_QUALITIES)

            sector = _sector_from_angle(angle, n)

            states[side] = WheelState(
                side=side,
                angle_deg=angle,
                sector=sector,
                is_pinching=hand.is_pinching,
                pinch_dist=hand.pinch_dist,
                tip_pos=hand.index_tip,
            )

        return states