"""
Skittle sorter settings. Edit this file, not sorter.py.

Everything you are likely to tune (GPIO pins, servo angles, color thresholds,
timing, which OLED is where) lives here.
"""

# --------------------------------------------------------------------------
# Camera (USB webcam via OpenCV)
# --------------------------------------------------------------------------
CAMERA_INDEX = 0          # /dev/video0. Try 1 if the Pi picks the wrong device.
FRAME_W, FRAME_H = 640, 480

# The Skittle must be held inside this square in the middle of the image.
# Run with --preview once to see the box and aim the camera.
ROI_SIZE = 140            # pixels

# A pixel only counts as "Skittle" if it's colorful and bright enough.
# The white/grey background and most skin tones fall below MIN_SAT.
MIN_SAT = 100             # 0-255. Raise if fingers read as "orange"; lower in dim light.
MIN_VAL = 60              # 0-255. Ignores shadows.
MIN_COVERAGE = 0.08       # fraction of the ROI that must be colorful to count as "a Skittle is there"

STABLE_FRAMES = 6         # same answer this many frames in a row (~1/3 s) before locking the color
MAX_HUE_DIST = 16         # farther than this from every known color -> "unknown" (e.g. purple)

# OpenCV hue runs 0-179 (red wraps around 0/179).
# These defaults are only a starting point. Run:  python3 sorter.py --calibrate
# Calibration writes calibration.json, which overrides these.
HUE_CENTERS = {
    "red":    2,
    "orange": 11,
    "yellow": 26,
    "green":  55,
}
CALIBRATION_FILE = "calibration.json"

COLORS = ["red", "orange", "yellow", "green"]   # display / tally order

# --------------------------------------------------------------------------
# Timing
# --------------------------------------------------------------------------
COUNTDOWN_S = 3.0         # after the color locks, gates move, then "DROP" after this many seconds
DROP_WINDOW_S = 4.0       # gates hold their position this long so the Skittle can fall through
CLEAR_FRAMES = 15         # camera must see nothing for this many frames before the next Skittle

# --------------------------------------------------------------------------
# SparkFun Qwiic OLED (0.91", 128x32, SSD1306) - driven like Lab 4/oled_test.py
# --------------------------------------------------------------------------
# Every one of these boards is fixed at I2C address 0x3C, so two of them
# can't share the bus directly. For a 2nd screen, add a SparkFun Qwiic Mux
# (TCA9548A) and give each screen a mux channel.
#
# Screen 0 shows the live status (color + countdown).
# Screen 1 (optional) shows the running tally.
OLEDS = [
    {"address": 0x3C, "mux_channel": None},
    # With a Qwiic Mux, use these two lines instead of the one above:
    # {"address": 0x3C, "mux_channel": 0},
    # {"address": 0x3C, "mux_channel": 1},
]
MUX_ADDRESS = 0x70        # Qwiic Mux default
OLED_W, OLED_H = 128, 32
OLED_FLIP = False         # True if the screen is mounted upside down

# --------------------------------------------------------------------------
# Motors: 3 micro servos on the SparkFun Servo pHAT (same as Lab 4 Part C)
# --------------------------------------------------------------------------
# Default layout is a binary tree. 3 flaps -> 4 bins:
#
#                    drop column
#                         |
#                   [ TOP  ch 0 ]
#                    /          \
#          [ LEFT ch 1 ]      [ RIGHT ch 2 ]
#            /      \            /      \
#         RED    ORANGE      YELLOW    GREEN
#
# If your mechanism is different (e.g. 3 trap-doors along one chute), you
# only need to change ROUTES below. Each color lists the angle for each servo.
SERVO_CHANNELS = {        # Servo pHAT channel numbers (printed on the board, 0-15)
    "top":   0,
    "left":  1,
    "right": 2,
}
# Angles use pi_servo_hat's scale, same as pi_servo_hat_test.py and
# windmill_coaster.py: about 0-120 is safe for 9g servos (MS18 / SG90).
HOME = {"top": 60, "left": 60, "right": 60}

ROUTES = {
    "red":    {"top": 120, "left": 120},  # top tips left,  left flap tips left  -> far-left bin
    "orange": {"top": 120, "left": 10},   # top tips left,  left flap tips right
    "yellow": {"top": 10,  "right": 120}, # top tips right, right flap tips left
    "green":  {"top": 10,  "right": 10},  # top tips right, right flap tips right -> far-right bin
}
# Servos not listed for a color go to HOME.

SERVO_SETTLE_S = 0.5      # time for servos to reach position
