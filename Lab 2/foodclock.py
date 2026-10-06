# This code was debugged and structured with assistance from ChatGPT (OpenAI, September 2026 version)
# This code was also based on the following files in the repository: image.py, screen_clock.py, screen_test.py

import time
import digitalio
import board

from time import strftime
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# ============================================================
# DISPLAY SETUP
# ============================================================
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

BAUDRATE = 64000000

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
# DISPLAY DIMENSIONS
# ============================================================
# Swap height/width to rotate it to landscape!
# ============================================================
WIDTH = 240
HEIGHT = 135

rotation = 90

# ============================================================
# BACKLIGHT & BUTTONS
# ============================================================
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# ============================================================
# IMAGE LOADING FUNCTION
# ============================================================
def load_layer(filename):
    image = Image.open(filename).convert("RGBA")

    return image

# ============================================================
# LUNCH IMAGES
# ============================================================
lunch_bowl = load_layer(
    "foodclock_images/spaghetti/lunch_bowl.png"
)

lunch_noodles = load_layer(
    "foodclock_images/spaghetti/pasta.png"
)

lunch_sauce = load_layer(
    "foodclock_images/spaghetti/sauce.png"
)

lunch_meatballs = load_layer(
    "foodclock_images/spaghetti/meatballs.png"
)

lunch_basil = load_layer(
    "foodclock_images/spaghetti/basil.png"
)

# ============================================================
# DINNER IMAGES
# ============================================================
dinner_bowl = load_layer(
    "foodclock_images/bibimbap/dinner_bowl.png"
)

dinner_rice = load_layer(
    "foodclock_images/bibimbap/rice.png"
)

dinner_carrots = load_layer(
    "foodclock_images/bibimbap/carrots.png"
)

dinner_spinach = load_layer(
    "foodclock_images/bibimbap/spinach.png"
)

dinner_egg = load_layer(
    "foodclock_images/bibimbap/egg.png"
)

dinner_sauce = load_layer(
    "foodclock_images/bibimbap/gochujang.png"
)

# ============================================================
# OTHER IMAGE ASSETS
# ============================================================
silver_platter = load_layer(
    "foodclock_images/silver_platter.png"
)

bon_appetit = load_layer(   
    "foodclock_images/bon_appetit.png"
)

sparkle = load_layer(
    "foodclock_images/sparkle.png"
)

# ============================================================
# BUILD FOOD SCENES
# ============================================================
spaghetti = lunch_bowl.copy()
spaghetti = Image.alpha_composite(spaghetti, lunch_noodles)
spaghetti = Image.alpha_composite(spaghetti, lunch_sauce)
spaghetti = Image.alpha_composite(spaghetti, lunch_meatballs)
spaghetti = Image.alpha_composite(spaghetti, lunch_basil)

bibimbap = dinner_bowl.copy()
bibimbap = Image.alpha_composite(bibimbap, dinner_rice)
bibimbap = Image.alpha_composite(bibimbap, dinner_carrots)
bibimbap = Image.alpha_composite(bibimbap, dinner_spinach)
bibimbap = Image.alpha_composite(bibimbap, dinner_egg)
bibimbap = Image.alpha_composite(bibimbap, dinner_sauce)

# ============================================================
# KITCHEN CLOSED SCENE SETTINGS
# ============================================================
def kitchen_closed():
    # Create a blank black image
    scene = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 255)
    )

    draw = ImageDraw.Draw(scene)

    # Load a font
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        24
    )

    text = "KITCHEN CLOSED"

    # Find the size of the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    x = (WIDTH - text_width) // 2
    y = (HEIGHT - text_height) // 2

    # Draw the text
    draw.text(
        (x, y),
        text,
        font=font,
        fill=(255, 255, 255, 255)
    )

    return scene

# ============================================================
# TEST MODE SETUP
# ============================================================
test_mode = False
test_hour = 7

buttonA_last = False


# ============================================================
# MEAL CLOCK START
# ============================================================
def get_scene():
    global test_mode
    global test_hour

    if test_mode:
        hour = test_hour
    else:
        hour = datetime.now().hour

    # =========================
    # MAKING LUNCH: 7 AM–1 PM
    # =========================
    if 7 <= hour < 8:
        return lunch_bowl

    elif 8 <= hour < 9:
        scene = lunch_bowl.copy()
        scene = Image.alpha_composite(scene, lunch_noodles)
        return scene

    elif 9 <= hour < 10:
        scene = lunch_bowl.copy()
        scene = Image.alpha_composite(scene, lunch_noodles)
        scene = Image.alpha_composite(scene, lunch_sauce)
        return scene

    elif 10 <= hour < 11:
        scene = lunch_bowl.copy()
        scene = Image.alpha_composite(scene, lunch_noodles)
        scene = Image.alpha_composite(scene, lunch_sauce)
        scene = Image.alpha_composite(scene, lunch_meatballs)
        return scene

    elif 11 <= hour < 12:
        return silver_platter

    elif 12 <= hour < 13:
        scene = lunch_bowl.copy()
        scene = Image.alpha_composite(scene, lunch_noodles)
        scene = Image.alpha_composite(scene, lunch_sauce)
        scene = Image.alpha_composite(scene, lunch_meatballs)
        scene = Image.alpha_composite(scene, lunch_basil)
        scene = Image.alpha_composite(scene, bon_appetit)
        scene = Image.alpha_composite(scene, sparkle)
        return scene

    # =========================
    # MAKING BIBIMBAP: 1 PM–9 PM
    # =========================
    elif 13 <= hour < 14:
        return dinner_bowl

    elif 14 <= hour < 15:
        scene = dinner_bowl.copy()
        scene = Image.alpha_composite(scene, dinner_rice)
        return scene

    elif 15 <= hour < 16:
        scene = dinner_bowl.copy()
        scene = Image.alpha_composite(scene, dinner_rice)
        scene = Image.alpha_composite(scene, dinner_carrots)
        return scene

    elif 16 <= hour < 17:
        scene = dinner_bowl.copy()
        scene = Image.alpha_composite(scene, dinner_rice)
        scene = Image.alpha_composite(scene, dinner_spinach)
        scene = Image.alpha_composite(scene, dinner_carrots)
        return scene

    elif 17 <= hour < 18:
        scene = dinner_bowl.copy()
        scene = Image.alpha_composite(scene, dinner_rice)
        scene = Image.alpha_composite(scene, dinner_carrots)
        scene = Image.alpha_composite(scene, dinner_spinach)
        scene = Image.alpha_composite(scene, dinner_egg)
        return scene

    elif 18 <= hour < 19:
        scene = dinner_bowl.copy()
        scene = Image.alpha_composite(scene, dinner_rice)
        scene = Image.alpha_composite(scene, dinner_carrots)
        scene = Image.alpha_composite(scene, dinner_spinach)
        scene = Image.alpha_composite(scene, dinner_egg)
        return scene

    elif 19 <= hour < 20:
        return silver_platter

    elif 20 <= hour < 21:
        scene = dinner_bowl.copy()
        scene = Image.alpha_composite(scene, dinner_rice)
        scene = Image.alpha_composite(scene, dinner_carrots)
        scene = Image.alpha_composite(scene, dinner_spinach)
        scene = Image.alpha_composite(scene, dinner_egg)
        scene = Image.alpha_composite(scene, dinner_sauce)
        scene = Image.alpha_composite(scene, bon_appetit)
        scene = Image.alpha_composite(scene, sparkle)
        return scene

    # =========================
    # KITCHEN IS CLOSED: 9 PM–7AM
    # =========================
    else:
        return kitchen_closed()

while True:

   # Check top button
    buttonA_pressed = not buttonA.value

    if buttonA_pressed and not buttonA_last:

        # Turn test mode on
        test_mode = True

        # Advance one hour
        test_hour += 1

        # Loop back around after 23
        if test_hour >= 24:
            test_hour = 0

    buttonA_last = buttonA_pressed

    # Get the appropriate food scene
    scene = get_scene()

    # Rotate for display
    scene = scene.rotate(rotation, expand=True)

    # Show it
    disp.image(scene)

    # Small delay to prevent button bouncing
    time.sleep(0.1)
