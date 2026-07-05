
import cv2
import sys
import time
import math
from collections import deque

from config import (CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT,
                    LEFT_WHEEL_CENTER, RIGHT_WHEEL_CENTER, WHEEL_RADIUS_RATIO)
from audio.synth import ChordSynth
from audio.scales import ROOT_NOTES, CHORD_QUALITIES, get_chord_freqs_explicit
from vision.hand_tracker import HandTracker
from vision.gesture import GestureMapper
from ui.renderer import (draw_wheel, draw_pointer_line, draw_hud,
                          draw_chord_banner, draw_single_pinch_hint)

WAVEFORMS = ["organ", "sine", "triangle"]

def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        sys.exit(1)

    tracker = HandTracker()
    synth   = ChordSynth()
    mapper  = GestureMapper()

    octave    = 4
    wave_idx  = 0
    fps_buf   = deque(maxlen=30)

    # Track last pinch state to avoid re-triggering same chord
    prev_left_pinching = False
    pulse_trigger_time = 0.0
    last_chord_id      = None
    
    # Locked sector status (touches middle of circle)
    left_locked  = None
    right_locked = None

    print("GestureChord v2 — running. Q to quit.")

    while True:
        t0 = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            break

        frame   = cv2.flip(frame, 1)
        h, w    = frame.shape[:2]
        rad_px  = int(h * WHEEL_RADIUS_RATIO)

        # ── Detect & map ──────────────────────────────────────────────────
        hands  = tracker.process(frame)
        states = mapper.map(hands)

        left_ws  = states.get("left")
        right_ws = states.get("right")

        # Resolve left hand sector & lock status
        if left_ws:
            dist_to_center = math.hypot(left_ws.tip_pos[0] - LEFT_WHEEL_CENTER[0],
                                        left_ws.tip_pos[1] - LEFT_WHEEL_CENTER[1])
            left_pinching = left_ws.is_pinching
            
            if left_pinching:
                if dist_to_center < 0.055:
                    left_locked = left_ws.sector
                else:
                    if left_locked is not None and left_ws.sector != left_locked:
                        left_locked = None
            
            active_left_sector = left_locked if left_locked is not None else left_ws.sector
        else:
            left_pinching = False
            active_left_sector = left_locked if left_locked is not None else 0

        # Resolve right hand sector & lock status
        if right_ws:
            dist_to_center = math.hypot(right_ws.tip_pos[0] - RIGHT_WHEEL_CENTER[0],
                                        right_ws.tip_pos[1] - RIGHT_WHEEL_CENTER[1])
            right_pinching = right_ws.is_pinching
            
            if right_pinching:
                if dist_to_center < 0.055:
                    right_locked = right_ws.sector
                else:
                    if right_locked is not None and right_ws.sector != right_locked:
                        right_locked = None
            
            active_right_sector = right_locked if right_locked is not None else right_ws.sector
        else:
            right_pinching = False
            active_right_sector = right_locked if right_locked is not None else 0

        root_label    = ROOT_NOTES[active_left_sector]
        quality_label = CHORD_QUALITIES[active_right_sector]

        # ── Audio logic ───────────────────────────────────────────────────
        chord_id = f"{root_label}_{quality_label}_{octave}"

        if left_pinching and not prev_left_pinching:
            # New chord trigger
            freqs = get_chord_freqs_explicit(root_label, quality_label, octave)
            synth.stop_all()
            synth.play_chord(chord_id, freqs)
            last_chord_id = chord_id
            pulse_trigger_time = time.perf_counter()
            print(f"  > Playing: {root_label} {quality_label} (oct {octave})")

        elif not left_pinching and prev_left_pinching:
            # Released
            synth.stop_all()

        elif left_pinching and chord_id != last_chord_id:
            # Chord changed while still pinching — retrigger
            freqs = get_chord_freqs_explicit(root_label, quality_label, octave)
            synth.stop_all()
            synth.play_chord(chord_id, freqs)
            last_chord_id = chord_id
            pulse_trigger_time = time.perf_counter()
            print(f"  > Changed: {root_label} {quality_label} (oct {octave})")

        prev_left_pinching = left_pinching

        # ── Render ────────────────────────────────────────────────────────
        # Left wheel — root notes
        draw_wheel(frame,
                   LEFT_WHEEL_CENTER[0], LEFT_WHEEL_CENTER[1], rad_px,
                   labels=ROOT_NOTES,
                   active_sector=active_left_sector,
                   is_pinching=left_pinching,
                   title="ROOT NOTE",
                   pulse_trigger_time=pulse_trigger_time,
                   locked_sector=left_locked)

        # Right wheel — chord quality
        draw_wheel(frame,
                   RIGHT_WHEEL_CENTER[0], RIGHT_WHEEL_CENTER[1], rad_px,
                   labels=CHORD_QUALITIES,
                   active_sector=active_right_sector,
                   is_pinching=right_pinching,
                   title="CHORD TYPE",
                   locked_sector=right_locked)

        # Pointer lines
        if left_ws:
            draw_pointer_line(frame,
                              LEFT_WHEEL_CENTER[0], LEFT_WHEEL_CENTER[1],
                              left_ws.tip_pos, rad_px, w, h, left_pinching)
        if right_ws:
            draw_pointer_line(frame,
                              RIGHT_WHEEL_CENTER[0], RIGHT_WHEEL_CENTER[1],
                              right_ws.tip_pos, rad_px, w, h, right_pinching)

        # Big chord name when left hand pinches or is ready
        draw_chord_banner(frame, root_label, quality_label, left_pinching, w, h)

        # HUD
        fps_buf.append(1.0 / max(time.perf_counter() - t0, 1e-6))
        draw_hud(frame, octave, WAVEFORMS[wave_idx],
                 sum(fps_buf) / len(fps_buf), w, h)

        cv2.imshow("GestureChord", frame)

        # ── Keys ──────────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            break
        elif key == ord('w'):
            wave_idx = (wave_idx + 1) % len(WAVEFORMS)
            synth.waveform = WAVEFORMS[wave_idx]
        elif key in (ord('+'), ord('=')):
            octave = min(6, octave + 1); synth.stop_all()
        elif key == ord('-'):
            octave = max(2, octave - 1); synth.stop_all()

    tracker.close()
    synth.cleanup()
    cap.release()
    cv2.destroyAllWindows()
    print("Closed.")


if __name__ == "__main__":
    main()