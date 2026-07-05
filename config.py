# config.py

CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS_TARGET = 30

MP_MAX_HANDS = 2
MP_MIN_DETECTION_CONFIDENCE = 0.80
MP_MIN_TRACKING_CONFIDENCE = 0.80

# Pinch parameters
# Left hand (trigger/pulse): Tuned for maximum responsiveness and quick pulsing
PINCH_THRESHOLD_LEFT = 0.055
PINCH_RELEASE_LEFT = 0.060

# Right hand (quality select): Tuned standard
PINCH_THRESHOLD_RIGHT = 0.048
PINCH_RELEASE_RIGHT = 0.065

SAMPLE_RATE = 44100
AUDIO_BUFFER = 512
MASTER_VOLUME = 0.65
CHORD_FADE_MS = 200
CHORD_ATTACK_MS = 20

DEFAULT_OCTAVE = 4

LEFT_WHEEL_CENTER  = (0.22, 0.52)
RIGHT_WHEEL_CENTER = (0.78, 0.52)
WHEEL_RADIUS_RATIO = 0.23

# Modern, refined color scheme (BGR format)
COLOR_ACTIVE       = (120, 240, 100) # Crisp Neon Green
COLOR_INACTIVE     = (48, 42, 38)    # Sleek Slate Dark Gray
COLOR_PINCH        = (250, 190, 30)  # Cyber Cyan/Blue
COLOR_HOVER        = (220, 110, 160) # Electric Violet
COLOR_TEXT         = (248, 246, 244) # Warm Off-White
COLOR_DIM_TEXT     = (150, 142, 135) # Muted Silver-Gray
COLOR_BG_BAR       = (24, 18, 14)    # Deep Obsidian Blue/Black
COLOR_GLOW         = (255, 140, 0)   # Blue glow overlay
