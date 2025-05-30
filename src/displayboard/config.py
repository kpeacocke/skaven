import logging
from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR.parent / "assets"
SOUNDS_DIR = ASSETS_DIR / "sounds"
VIDEO_DIR = ASSETS_DIR / "video"

# --- Logging ---
LOG_LEVEL_DEFAULT = logging.INFO
LOG_LEVEL_VERBOSE = logging.DEBUG
LOG_LEVEL_WARNING = logging.WARNING  # Added for default level in main
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# --- Timing ---
LOOP_WAIT_TIMEOUT = 0.1  # General timeout for event.wait() in loops
MAIN_LOOP_SLEEP_S = 1.0  # Sleep interval for main loop when video is disabled

# --- Video ---
VIDEO_FILE = VIDEO_DIR / "main_loop.mp4"
PROCESS_WAIT_TIMEOUT = 5  # Seconds to wait for video process to terminate

# --- Audio ---
AUDIO_EXTENSIONS = [".wav", ".ogg", ".mp3"]
SOUND_VOLUME_DEFAULT = 0.75
SOUND_NUM_CHANNELS = 16

# --- Ambient Loop ---
AMBIENT_CHANNEL = 0
AMBIENT_FADE_MS = 3000

# --- Chains Loop ---
CHAINS_SLEEP_MIN = 15
CHAINS_SLEEP_MAX = 120
CHAINS_VOLUME_MIN = 0.0
CHAINS_VOLUME_MAX = 0.5

# --- Main Loop ---
MAIN_LOOP_SLEEP_MIN = 20
MAIN_LOOP_SLEEP_MAX = 40
MAIN_LOOP_VOLUME_MIN = 0.0
MAIN_LOOP_VOLUME_MAX = 1.0

# --- Rats Loop ---
RATS_FADEOUT_MS = 500
RATS_SLEEP_MIN = 2
RATS_SLEEP_MAX = 6
RATS_CHANNEL_START = 1
RATS_CHANNEL_END = 5  # Exclusive, so channels are 1, 2, 3, 4

# --- Main Sound Loop (Screams) ---
MAIN_SCREAM_INTERVAL_S = 120
MAIN_AMBIENT_FADEOUT_MS = 2000
MAIN_RATS_FADEOUT_MS = 1000
MAIN_SHUTDOWN_WAIT_S = 2

# --- Lighting ---
LED_COUNT = 30
LED_PIN_BCM = (
    21  # BCM pin number for GPIO21 (changed from 18; 18 is now reserved for bell)
)
LED_BRIGHTNESS = 0.4
LED_ORDER = "GRB"  # Color order for NeoPixels

# --- Flicker/Breathe Effect ---
LIGHTING_UPDATE_INTERVAL = 0.05  # Seconds between updates
LIGHTING_BREATHE_FREQUENCY = 0.5  # Controls speed of breathing effect
LIGHTING_BREATHE_MIN_BRIGHTNESS = 0.2  # Minimum brightness (0.0 to 1.0)
# Range of brightness variation (max = min + range)
LIGHTING_BREATHE_RANGE = 0.8
# Chance (0.0 to 1.0) for a pixel to flicker
LIGHTING_FLICKER_PROBABILITY = 0.2
LIGHTING_FLICKER_R_MIN = 0
LIGHTING_FLICKER_R_MAX = 30
LIGHTING_FLICKER_G_MIN = 50
LIGHTING_FLICKER_G_MAX = 255
LIGHTING_FLICKER_B_MIN = 0
LIGHTING_FLICKER_B_MAX = 20
LIGHTING_BASE_G = 50  # Base green value when not flickering

# --- Bell ---
BELL_SOUND_FILE = SOUNDS_DIR / "bell" / "screamingBell.mp3"
BELL_SERVO_PIN = 18
BELL_SERVO_MIN_PULSE = 0.0005
BELL_SERVO_MAX_PULSE = 0.0025
BELL_SOUND_START_POS_MIN = 0
BELL_SOUND_START_POS_MAX = 90
BELL_SOUND_VOLUME_MIN = 0.3
BELL_SOUND_VOLUME_MAX = 1.0
BELL_SWING_COUNT_MIN = 1
BELL_SWING_COUNT_MAX = 5
BELL_SWING_POS_MIN = -1.0
BELL_SWING_POS_MAX = 1.0
BELL_SWING_SLEEP_MIN = 0.3
BELL_SWING_SLEEP_MAX = 0.6
BELL_LOOP_WAIT_MIN_S = 10.0
BELL_LOOP_WAIT_MAX_S = 40.0
BELL_TRIGGER_PROBABILITY = 0.8
BELL_GPIO_PIN_FACTORY = "pigpio"

# --- Add other constants below as needed ---
