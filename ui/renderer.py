# ui/renderer.py

import cv2
import numpy as np
import math
import time
from config import (LEFT_WHEEL_CENTER, RIGHT_WHEEL_CENTER,
                    COLOR_ACTIVE, COLOR_INACTIVE, COLOR_PINCH,
                    COLOR_HOVER, COLOR_TEXT, COLOR_DIM_TEXT, COLOR_BG_BAR, COLOR_GLOW)


def _px(nx, ny, w, h):
    return int(nx * w), int(ny * h)


def draw_rounded_rect(img, pt1, pt2, color, thickness, radius=10):
    """Draw a rounded rectangle using cv2 lines and ellipses."""
    x1, y1 = pt1
    x2, y2 = pt2
    w = x2 - x1
    h = y2 - y1
    r = min(radius, w // 2, h // 2)
    
    if thickness < 0:
        cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1)
        cv2.circle(img, (x1 + r, y1 + r), r, color, -1)
        cv2.circle(img, (x2 - r, y1 + r), r, color, -1)
        cv2.circle(img, (x1 + r, y2 - r), r, color, -1)
        cv2.circle(img, (x2 - r, y2 - r), r, color, -1)
    else:
        cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness, cv2.LINE_AA)
        
        cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness, cv2.LINE_AA)
        cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness, cv2.LINE_AA)
        cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness, cv2.LINE_AA)
        cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness, cv2.LINE_AA)


def draw_wheel(frame, cx_norm, cy_norm, radius_px,
               labels: list, active_sector: int,
               is_pinching: bool, title: str,
               pulse_trigger_time: float = 0.0,
               locked_sector: int = None):
    h, w = frame.shape[:2]
    cx, cy = int(cx_norm * w), int(cy_norm * h)
    n = len(labels)
    sector_deg = 360.0 / n

    # Outer decorative orbit ring
    cv2.circle(frame, (cx, cy), radius_px + 8, COLOR_INACTIVE, 1, cv2.LINE_AA)

    # Render sectors
    for i in range(n):
        start_a = -90 + i * sector_deg - sector_deg / 2
        end_a   = start_a + sector_deg - 1.5

        is_locked = (locked_sector is not None and i == locked_sector)

        if is_locked:
            color = COLOR_ACTIVE
            alpha = 0.45
            overlay = frame.copy()
            # Outer glow arc for locked sector
            cv2.ellipse(overlay, (cx, cy), (radius_px + 4, radius_px + 4),
                        0, start_a, end_a, color, 4, cv2.LINE_AA)
            cv2.ellipse(overlay, (cx, cy), (radius_px, radius_px),
                        0, start_a, end_a, color, -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        elif i == active_sector:
            color = COLOR_PINCH if is_pinching else COLOR_HOVER
            alpha = 0.40 if is_pinching else 0.25
            
            # Draw glow backing arc
            overlay = frame.copy()
            cv2.ellipse(overlay, (cx, cy), (radius_px + 4, radius_px + 4),
                        0, start_a, end_a, color, 3, cv2.LINE_AA)
            cv2.ellipse(overlay, (cx, cy), (radius_px, radius_px),
                        0, start_a, end_a, color, -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        else:
            color = COLOR_INACTIVE
            alpha = 0.15
            overlay = frame.copy()
            cv2.ellipse(overlay, (cx, cy), (radius_px, radius_px),
                        0, start_a, end_a, color, -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Sector border
        cv2.ellipse(frame, (cx, cy), (radius_px, radius_px),
                    0, start_a, end_a, (60, 56, 52), 1, cv2.LINE_AA)

        # Label position
        mid_rad = math.radians(start_a + sector_deg / 2)
        lx = int(cx + radius_px * 0.68 * math.cos(mid_rad))
        ly = int(cy + radius_px * 0.68 * math.sin(mid_rad))

        lbl = labels[i]
        font_scale = 0.58 if len(lbl) <= 3 else 0.46
        txt_color  = COLOR_ACTIVE if is_locked else (COLOR_TEXT if i == active_sector else COLOR_DIM_TEXT)
        thickness  = 2 if (i == active_sector or is_locked) else 1

        # Center the text
        (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX,
                                       font_scale, thickness)
        
        # Shadow for sector text
        cv2.putText(frame, lbl, (lx - tw // 2 + 1, ly + th // 2 + 1),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (10, 10, 15), thickness, cv2.LINE_AA)
        cv2.putText(frame, lbl, (lx - tw // 2, ly + th // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, txt_color, thickness, cv2.LINE_AA)

    # Concentric multi-layer center hub
    hub_r = int(radius_px * 0.22)
    current_color = COLOR_PINCH if is_pinching else COLOR_HOVER
    hub_color = COLOR_ACTIVE if locked_sector is not None else current_color
    
    # Outer thin ring
    cv2.circle(frame, (cx, cy), hub_r, hub_color, 1, cv2.LINE_AA)
    # Inner dark hub
    cv2.circle(frame, (cx, cy), int(hub_r * 0.75), (28, 24, 22), -1)
    cv2.circle(frame, (cx, cy), int(hub_r * 0.75), (60, 56, 52), 1, cv2.LINE_AA)
    
    # Center dot / Lock icon
    if locked_sector is not None:
        # Draw padlock shackle loop
        cv2.ellipse(frame, (cx, cy - 1), (3, 4), 180, 0, 180, COLOR_ACTIVE, 1, cv2.LINE_AA)
        # Draw padlock body
        cv2.rectangle(frame, (cx - 5, cy - 1), (cx + 5, cy + 5), COLOR_ACTIVE, -1)
    else:
        # Center dot
        dot_color = current_color if is_pinching else (80, 75, 70)
        cv2.circle(frame, (cx, cy), int(hub_r * 0.35), dot_color, -1)

    # Expanding pulse ripple animation (Left wheel only, if pulse_trigger_time is set)
    if pulse_trigger_time > 0.0:
        elapsed = time.perf_counter() - pulse_trigger_time
        if elapsed < 0.5:
            progress = elapsed / 0.5
            ripple_r = int(radius_px + progress * 70)
            ripple_color = COLOR_PINCH
            alpha = (1.0 - progress) * 0.7
            
            overlay = frame.copy()
            cv2.circle(overlay, (cx, cy), ripple_r, ripple_color, 2, cv2.LINE_AA)
            cv2.circle(overlay, (cx, cy), ripple_r + 4, ripple_color, 1, cv2.LINE_AA)
            cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)

    # Wheel title capsule below
    (tw, th), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
    tx1, ty1 = cx - tw // 2 - 10, cy + radius_px + 22
    tx2, ty2 = cx + tw // 2 + 10, cy + radius_px + 42
    
    # Draw dark backing capsule
    draw_rounded_rect(frame, (tx1, ty1), (tx2, ty2), (32, 28, 24), -1, radius=6)
    draw_rounded_rect(frame, (tx1, ty1), (tx2, ty2), COLOR_INACTIVE, 1, radius=6)
    
    cv2.putText(frame, title,
                (cx - tw // 2, cy + radius_px + 36),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, COLOR_TEXT, 1, cv2.LINE_AA)


def draw_pointer_line(frame, cx_norm, cy_norm, tip_norm,
                      radius_px, w, h, is_pinching):
    """Draw a line from wheel center to finger tip with futuristic HUD look."""
    cx = int(cx_norm * w)
    cy = int(cy_norm * h)
    tx = int(tip_norm[0] * w)
    ty = int(tip_norm[1] * h)
    color = COLOR_PINCH if is_pinching else COLOR_HOVER
    
    # Backing glow line
    overlay = frame.copy()
    cv2.line(overlay, (cx, cy), (tx, ty), color, 5, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.22, frame, 0.78, 0, frame)
    
    # Sharp center line
    cv2.line(frame, (cx, cy), (tx, ty), COLOR_TEXT if not is_pinching else COLOR_PINCH, 1, cv2.LINE_AA)
    
    # Aiming Reticle Cursor
    dot_color = COLOR_PINCH if is_pinching else COLOR_TEXT
    
    # Inner center dot
    cv2.circle(frame, (tx, ty), 4, dot_color, -1)
    
    # Reticle outer ring (shrinks slightly when pinched)
    ring_r = 10 if is_pinching else 15
    cv2.circle(frame, (tx, ty), ring_r, dot_color, 1, cv2.LINE_AA)
    
    # Crosshair ticks
    tick = 4
    cv2.line(frame, (tx, ty - ring_r), (tx, ty - ring_r - tick), dot_color, 1, cv2.LINE_AA)
    cv2.line(frame, (tx, ty + ring_r), (tx, ty + ring_r + tick), dot_color, 1, cv2.LINE_AA)
    cv2.line(frame, (tx - ring_r, ty), (tx - ring_r - tick, ty), dot_color, 1, cv2.LINE_AA)
    cv2.line(frame, (tx + ring_r, ty), (tx + ring_r + tick, ty), dot_color, 1, cv2.LINE_AA)


def draw_chord_banner(frame, root: str, quality: str,
                      left_pinching: bool, w, h):
    """Futuristic Glassmorphic Chord Status Panel at the bottom center."""
    card_w, card_h = 360, 78
    x1, y1 = (w - card_w) // 2, h - card_h - 22
    x2, y2 = x1 + card_w, y1 + card_h
    
    # Translucent glass panel
    overlay = frame.copy()
    draw_rounded_rect(overlay, (x1, y1), (x2, y2), COLOR_BG_BAR, -1, radius=12)
    
    border_color = COLOR_PINCH if left_pinching else COLOR_INACTIVE
    border_thick = 2 if left_pinching else 1
    draw_rounded_rect(overlay, (x1, y1), (x2, y2), border_color, border_thick, radius=12)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    chord_str = f"{root} {quality}"
    
    # Header label
    if left_pinching:
        state_str = "ACTIVE CHORD"
        state_color = COLOR_PINCH
    else:
        state_str = "READY CHORD"
        state_color = COLOR_DIM_TEXT
        
    cv2.putText(frame, state_str, (x1 + 18, y1 + 25), font, 0.42, state_color, 1, cv2.LINE_AA)
    
    # Green status LED dot
    if left_pinching:
        (sw, _), _ = cv2.getTextSize(state_str, font, 0.42, 1)
        cv2.circle(frame, (x1 + 18 + sw + 10, y1 + 20), 4, COLOR_ACTIVE, -1, cv2.LINE_AA)
    
    # Big Chord Name
    cv2.putText(frame, chord_str, (x1 + 18, y1 + 60), font, 1.1, COLOR_TEXT, 2, cv2.LINE_AA)
    
    # Help Tip Prompt (on the right)
    if not left_pinching:
        prompt_str = "Pinch Left to Pulse"
        (pw, _), _ = cv2.getTextSize(prompt_str, font, 0.42, 1)
        cv2.putText(frame, prompt_str, (x2 - pw - 18, y1 + 25), font, 0.42, COLOR_DIM_TEXT, 1, cv2.LINE_AA)


def draw_single_pinch_hint(frame, side: str, label: str, w, h):
    """Deprecated: Kept for backwards compatibility stub."""
    pass


def draw_hud(frame, octave, waveform, fps, w, h):
    """Refined Top Dashboard HUD."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 42), COLOR_BG_BAR, -1)
    cv2.line(overlay, (0, 42), (w, 42), COLOR_INACTIVE, 1, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # Brand/Status
    info = f"GESTURECHORD  |  OCTAVE: {octave}  |  WAVE: {waveform.upper()}"
    cv2.putText(frame, info, (16, 26), font, 0.46, COLOR_TEXT, 1, cv2.LINE_AA)

    # Right side: FPS
    fps_str = f"FPS: {fps:.0f}"
    (fw, _), _ = cv2.getTextSize(fps_str, font, 0.46, 1)
    
    # Active indicator light next to FPS
    cv2.circle(frame, (w - fw - 24, 21), 4, COLOR_ACTIVE, -1, cv2.LINE_AA)
    cv2.putText(frame, fps_str, (w - fw - 12, 26), font, 0.46, COLOR_TEXT, 1, cv2.LINE_AA)

    # Control Keys Pill Box
    hints = "Q: Quit   W: Wave   +/-: Octave"
    (hw, _), _ = cv2.getTextSize(hints, font, 0.38, 1)
    
    cx1 = w - fw - 42 - hw - 14
    cx2 = cx1 + hw + 16
    cy1, cy2 = 8, 32
    
    # Draw small dark rounded pill for hints
    draw_rounded_rect(frame, (cx1, cy1), (cx2, cy2), (32, 28, 24), -1, radius=6)
    draw_rounded_rect(frame, (cx1, cy1), (cx2, cy2), COLOR_INACTIVE, 1, radius=6)
    
    cv2.putText(frame, hints, (cx1 + 8, 22), font, 0.38, COLOR_DIM_TEXT, 1, cv2.LINE_AA)