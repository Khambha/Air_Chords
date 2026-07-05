# audio/scales.py

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

# Left wheel: only natural notes shown on wheel
ROOT_NOTES = ["C", "D", "E", "F", "G", "A", "B"]

# Right wheel: chord qualities
CHORD_QUALITIES = ["maj", "min", "dom7", "maj7", "min7", "sus2", "sus4", "dim", "aug"]

CHORD_INTERVALS = {
    "maj":  [0, 4, 7],
    "min":  [0, 3, 7],
    "dom7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "dim":  [0, 3, 6],
    "aug":  [0, 4, 8],
}


def get_chord_freqs_explicit(root: str, quality: str, octave: int) -> list:
    """
    Build chord frequencies directly from root note + quality.
    No scale math — pure interval stacking.
    """
    root_idx = NOTE_NAMES.index(root)
    root_midi = (octave + 1) * 12 + root_idx
    intervals = CHORD_INTERVALS[quality]
    freqs = []
    for iv in intervals:
        midi = root_midi + iv
        f = 440.0 * (2.0 ** ((midi - 69) / 12.0))
        freqs.append(f)
    return freqs