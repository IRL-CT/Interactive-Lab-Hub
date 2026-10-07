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
# BUTTON
# ============================================================
#
# Confirmed physical button:
# GPIO23
#
# Button is active LOW:
#
# Not pressed = HIGH
# Pressed     = LOW
#
# ============================================================

button = digitalio.DigitalInOut(board.D23)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP


# ============================================================
# SETTINGS
# ============================================================

IMAGE_FOLDER = "images"

# Animation speed
FRAME_DELAY = 0.15

# Number of frames in every animation
FRAMES_PER_ANIMATION = 5

# After 60 seconds without pressing the button,
# return to the correct real-time animation.
DEMO_TIMEOUT = 60


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
    8: 1,
    9: 2,
    10: 3,
    11: 4,

    12: 5,
    13: 6,
    14: 7,
    15: 8,
    16: 9,
    17: 10,

    18: 11,
    19: 12,
    20: 13,
    21: 14,
    22: 15,
    23: 16,

    0: 17,
    1: 18,

    2: 19,
    3: 19,
    4: 19,
    5: 19,
    6: 19,
    7: 19,
}


# ============================================================
# LOAD IMAGE
# ============================================================

def load_image(filename):

    filepath = os.path.join(
        IMAGE_FOLDER,
        filename
    )

    print("Loading:", filepath)

    image = Image.open(filepath).convert("RGB")

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
# LOAD ALL 19 ANIMATIONS
# ============================================================

print()
print("Loading animation frames...")
print()

loaded_animations = {}


for animation_number in range(1, 20):

    loaded_animations[animation_number] = []

    for frame_number in range(
        1,
        FRAMES_PER_ANIMATION + 1
    ):

        filename = (
            f"p{animation_number}"
            f"f{frame_number}.png"
        )

        frame = load_image(filename)

        loaded_animations[
            animation_number
        ].append(frame)


print()
print("==============================")
print("All animations loaded!")
print("==============================")
print()


# ============================================================
# CLOCK / DEMO STATE
# ============================================================

current_frame = 0

# False = normal clock mode
# True  = manually browsing animations
demo_mode = False

# Animation being shown during demo mode
demo_animation = None

# Time of most recent button press
last_button_press_time = 0

# Used to detect a new button press
last_button_state = True


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    # --------------------------------------------------------
    # CURRENT REAL TIME
    # --------------------------------------------------------

    hour = int(time.strftime("%H"))

    real_animation = hour_to_animation[hour]


    # --------------------------------------------------------
    # READ BUTTON
    # --------------------------------------------------------

    button_state = button.value


    # --------------------------------------------------------
    # DETECT BUTTON PRESS
    # --------------------------------------------------------
    #
    # HIGH -> LOW means the button was just pressed.
    #
    # This prevents holding the button from rapidly
    # switching through all 19 animations.
    #
    # --------------------------------------------------------

    if last_button_state and not button_state:

        # --------------------------------------------
        # FIRST PRESS
        # --------------------------------------------

        if not demo_mode:

            demo_mode = True

            # Start from the animation AFTER the
            # real current animation.
            demo_animation = real_animation + 1

            if demo_animation > 19:
                demo_animation = 1

        # --------------------------------------------
        # ADDITIONAL PRESSES
        # --------------------------------------------

        else:

            demo_animation += 1

            if demo_animation > 19:
                demo_animation = 1


        # Restart the selected animation at frame 1
        current_frame = 0

        # Restart the 1-minute timeout
        last_button_press_time = time.monotonic()


        print()
        print("==============================")
        print("DEMO MODE")
        print("Showing animation: p" + str(demo_animation))
        print("==============================")
        print()


    # Save button state for next loop
    last_button_state = button_state


    # --------------------------------------------------------
    # CHECK DEMO TIMEOUT
    # --------------------------------------------------------

    if demo_mode:

        time_since_press = (
            time.monotonic() - last_button_press_time
        )

        if time_since_press >= DEMO_TIMEOUT:

            demo_mode = False
            demo_animation = None
            current_frame = 0

            print()
            print("==============================")
            print("DEMO TIMEOUT")
            print("Returning to normal clock mode")
            print(
                "Current animation: p"
                + str(real_animation)
            )
            print("==============================")
            print()


    # --------------------------------------------------------
    # CHOOSE ANIMATION
    # --------------------------------------------------------

    if demo_mode:

        animation_number = demo_animation

    else:

        animation_number = real_animation


    # --------------------------------------------------------
    # GET ANIMATION
    # --------------------------------------------------------

    animation = loaded_animations[
        animation_number
    ]


    # --------------------------------------------------------
    # GET CURRENT FRAME
    # --------------------------------------------------------

    frame = animation[current_frame]


    # --------------------------------------------------------
    # DISPLAY FRAME
    # --------------------------------------------------------

    disp.image(frame)


    # --------------------------------------------------------
    # NEXT FRAME
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