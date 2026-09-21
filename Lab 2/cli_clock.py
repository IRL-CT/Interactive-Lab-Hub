import time
import os
import digitalio
import board

from PIL import Image
import adafruit_rgb_display.st7789 as st7789


# ============================================================
# DISPLAY SETUP
# ============================================================

cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

BAUDRATE = 24000000

spi = board.SPI()

disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)


# ============================================================
# SCREEN SIZE
# ============================================================

if disp.rotation % 180 == 90:
    height = disp.width
    width = disp.height
else:
    width = disp.width
    height = disp.height


# ============================================================
# BACKLIGHT
# ============================================================

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True


# ============================================================
# SETTINGS
# ============================================================

# Folder containing all animation frames
IMAGE_FOLDER = "images"

# Animation speed
# 0.15 = about 6.7 frames per second
#
# Try 0.10 later if you want faster/smoother animation.
FRAME_DELAY = 0.15

# Every animation currently has 5 frames
FRAMES_PER_ANIMATION = 5


# ============================================================
# HOUR -> ANIMATION
# ============================================================
#
# p1  = 8 AM
# p2  = 9 AM
# p3  = 10 AM
# p4  = 11 AM
# p5  = 12 PM
# p6  = 1 PM
# p7  = 2 PM
# p8  = 3 PM
# p9  = 4 PM
# p10 = 5 PM
# p11 = 6 PM
# p12 = 7 PM
# p13 = 8 PM
# p14 = 9 PM
# p15 = 10 PM
# p16 = 11 PM
# p17 = 12 AM
# p18 = 1 AM
# p19 = 2 AM - 7 AM
#
# ============================================================

hour_to_animation = {

    # Morning
    8: 1,
    9: 2,
    10: 3,
    11: 4,

    # Afternoon
    12: 5,
    13: 6,
    14: 7,
    15: 8,
    16: 9,
    17: 10,

    # Evening
    18: 11,
    19: 12,
    20: 13,
    21: 14,
    22: 15,
    23: 16,

    # Midnight / early morning
    0: 17,
    1: 18,

    # Sleeping animation
    2: 19,
    3: 19,
    4: 19,
    5: 19,
    6: 19,
    7: 19,
}


# ============================================================
# LOAD AND RESIZE IMAGE
# ============================================================

def load_image(filename):

    filepath = os.path.join(
        IMAGE_FOLDER,
        filename
    )

    print("Loading:", filepath)

    # Open PNG
    image = Image.open(filepath).convert("RGB")

    # Calculate aspect ratios
    image_ratio = image.width / image.height
    screen_ratio = width / height

    # --------------------------------------------------------
    # RESIZE WHILE KEEPING ASPECT RATIO
    # --------------------------------------------------------

    if screen_ratio < image_ratio:

        scaled_width = (
            image.width * height // image.height
        )

        scaled_height = height

    else:

        scaled_width = width

        scaled_height = (
            image.height * width // image.width
        )

    image = image.resize(
        (scaled_width, scaled_height),
        Image.BICUBIC
    )


    # --------------------------------------------------------
    # CENTER CROP
    # --------------------------------------------------------

    x = scaled_width // 2 - width // 2
    y = scaled_height // 2 - height // 2

    image = image.crop(
        (
            x,
            y,
            x + width,
            y + height
        )
    )

    return image


# ============================================================
# PRELOAD ALL ANIMATIONS
# ============================================================
#
# Filenames are automatically generated:
#
# p1f1.png
# p1f2.png
# p1f3.png
# p1f4.png
# p1f5.png
#
# p2f1.png
# ...
#
# p19f5.png
#
# ============================================================

print()
print("Loading animation frames...")
print()

loaded_animations = {}


# There are 19 animations
for animation_number in range(1, 20):

    loaded_animations[animation_number] = []


    # Each animation has 5 frames
    for frame_number in range(
        1,
        FRAMES_PER_ANIMATION + 1
    ):

        # Automatically create filename
        #
        # Example:
        # animation_number = 3
        # frame_number = 2
        #
        # filename = p3f2.png

        filename = (
            f"p{animation_number}"
            f"f{frame_number}.png"
        )


        # Load and resize the frame
        frame = load_image(filename)


        # Store frame in memory
        loaded_animations[
            animation_number
        ].append(frame)


print()
print("==============================")
print("All animations loaded!")
print("==============================")
print()


# ============================================================
# MAIN CLOCK
# ============================================================

current_hour = None

# Start each animation on frame 1
current_frame = 0


while True:

    # --------------------------------------------------------
    # GET CURRENT HOUR
    # --------------------------------------------------------

    # Returns 0 - 23
    #
    # Example:
    # 8 AM  -> 8
    # 4 PM  -> 16
    # 12 AM -> 0

    hour = int(
        time.strftime("%H")
    )


    # --------------------------------------------------------
    # CHECK IF THE HOUR CHANGED
    # --------------------------------------------------------

    if hour != current_hour:

        current_hour = hour

        # Restart new animation from frame 1
        current_frame = 0

        animation_number = (
            hour_to_animation[hour]
        )

        print()
        print("==============================")
        print("Hour:", hour)
        print(
            "Playing animation:",
            "p" + str(animation_number)
        )
        print("==============================")
        print()


    # --------------------------------------------------------
    # FIND ANIMATION FOR CURRENT TIME
    # --------------------------------------------------------

    animation_number = (
        hour_to_animation[hour]
    )

    animation = (
        loaded_animations[animation_number]
    )


    # --------------------------------------------------------
    # GET CURRENT ANIMATION FRAME
    # --------------------------------------------------------

    frame = animation[current_frame]


    # --------------------------------------------------------
    # DISPLAY FRAME
    # --------------------------------------------------------

    # No clock text.
    # No black box.
    # Just the animation.

    disp.image(frame)


    # --------------------------------------------------------
    # MOVE TO NEXT FRAME
    # --------------------------------------------------------

    current_frame += 1


    # --------------------------------------------------------
    # LOOP ANIMATION
    # --------------------------------------------------------

    if current_frame >= len(animation):

        current_frame = 0


    # --------------------------------------------------------
    # ANIMATION SPEED
    # --------------------------------------------------------

    time.sleep(FRAME_DELAY)