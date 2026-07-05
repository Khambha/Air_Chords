# audio/synth.py

import numpy as np
import pygame
import threading
from config import SAMPLE_RATE, AUDIO_BUFFER, MASTER_VOLUME, CHORD_FADE_MS, CHORD_ATTACK_MS


def _make_wave(freqs: list, duration_samples: int,
               waveform: str, volume: float) -> np.ndarray:
    t = np.linspace(0, duration_samples / SAMPLE_RATE,
                    duration_samples, endpoint=False)
    wave = np.zeros(duration_samples, dtype=np.float32)

    for freq in freqs:
        if waveform == "organ":
            wave += (0.55 * np.sin(2 * np.pi * freq * t) +
                     0.28 * np.sin(2 * np.pi * 2 * freq * t) +
                     0.12 * np.sin(2 * np.pi * 3 * freq * t) +
                     0.05 * np.sin(2 * np.pi * 4 * freq * t)).astype(np.float32)
        elif waveform == "sine":
            wave += np.sin(2 * np.pi * freq * t).astype(np.float32)
        elif waveform == "triangle":
            wave += (2 / np.pi * np.arcsin(
                np.sin(2 * np.pi * freq * t))).astype(np.float32)

    peak = np.max(np.abs(wave))
    if peak > 0:
        wave /= peak

    atk = int(SAMPLE_RATE * CHORD_ATTACK_MS / 1000)
    if 0 < atk < duration_samples:
        wave[:atk] *= np.linspace(0, 1, atk)

    return (wave * volume * MASTER_VOLUME).astype(np.float32)


class ChordSynth:
    def __init__(self):
        pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16,
                               channels=2, buffer=AUDIO_BUFFER)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)
        self._lock = threading.Lock()
        self._channels: dict[str, pygame.mixer.Channel] = {}
        self.waveform = "organ"

    def play_chord(self, chord_id: str, freqs: list, volume: float = 0.82):
        n = SAMPLE_RATE * 4
        wave = _make_wave(freqs, n, self.waveform, volume)
        w16 = (wave * 32767).astype(np.int16)
        stereo = np.column_stack([w16, w16])
        sound = pygame.sndarray.make_sound(stereo)

        with self._lock:
            if chord_id in self._channels:
                self._channels[chord_id].stop()
            ch = pygame.mixer.find_channel(True)
            if ch:
                ch.play(sound, loops=-1, fade_ms=CHORD_ATTACK_MS)
                self._channels[chord_id] = ch

    def stop_chord(self, chord_id: str):
        with self._lock:
            if chord_id in self._channels:
                self._channels.pop(chord_id).fadeout(CHORD_FADE_MS)

    def stop_all(self):
        with self._lock:
            for ch in self._channels.values():
                ch.fadeout(CHORD_FADE_MS)
            self._channels.clear()

    def active_ids(self) -> list:
        with self._lock:
            return list(self._channels.keys())

    def cleanup(self):
        self.stop_all()
        pygame.mixer.quit()