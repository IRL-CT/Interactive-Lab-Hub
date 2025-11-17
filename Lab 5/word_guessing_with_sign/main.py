import csv
import random
import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import board
import busio
import adafruit_ssd1306
from sign_detector import camera

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
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

buttonA = digitalio.DigitalInOut(board.D23)  # GPI023 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)  # GPI024 (PIN 18)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

# start with a blank screen
oled.fill(0)
# we just blanked the framebuffer. to push the framebuffer onto the display, we call show()
oled.show()

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
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

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True


# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
# Simulated camera() function (replace with your actual camera input)
#def camera():
#    return input("Enter a letter: ").strip().lower()


# ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

# Read a random word from CSV
def get_random_word(filename="words.csv"):
    with open(filename, "r") as f:
        reader = csv.DictReader(f)
        words = [row["word"].strip().lower() for row in reader]
    return random.choice(words)


def retry_window():
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    text = "Retry?"
    alabel = "No"
    blabel = "Yes"

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[0]

    alabel_bbox = draw.textbbox((0, 0), alabel, font=font2)
    alabel_width = alabel_bbox[2] - alabel_bbox[0]
    alabel_height = alabel_bbox[3] - alabel_bbox[0]

    blabel_bbox = draw.textbbox((0, 0), blabel, font=font2)
    blabel_width = blabel_bbox[2] - blabel_bbox[0]
    blabel_height = blabel_bbox[3] - blabel_bbox[0]

    draw.text((width // 2 - text_width // 2, height // 2 - text_height // 2), text, font=font, fill="#FFFFFF")
    draw.text((0, height - alabel_height), alabel, font=font2, fill="#FFFFFF")
    draw.text((0, 0), blabel, font=font2, fill="#FFFFFF")
    disp.image(image, rotation)
    time.sleep(0.1)


# Simulated Pi screen display (replace with your actual display function)
def piscreen_display(text):
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[0]

    draw.text((width // 2 - text_width // 2, height // 2 - text_height // 2), text, font=font, fill="#FFFFFF")

    disp.image(image, rotation)
    time.sleep(0.1)


count = 0


def hangman():
    global count
    oled_display(count)
    word = get_random_word()
    guessed = ["_"] * len(word)
    max_wrong = 6

    piscreen_display(" ".join(guessed))

    while count < max_wrong and "_" in guessed:
        guess = camera()
        if not guess or len(guess) != 1 or not guess.isalpha():
            piscreen_display("Invalid input.\nEnter a\nsingle letter.")
            continue

        print(guess)
        if guess in word:
            for i, ch in enumerate(word):
                if ch == guess:
                    guessed[i] = guess
            piscreen_display("Correct!")
        else:
            count += 1
            piscreen_display(f"Wrong!")
            oled_display(count)

        piscreen_display(" ".join(guessed))

    if "_" not in guessed:
        piscreen_display(f"You win!")
    else:
        piscreen_display(f"Game over\nWord: {word}")
    time.sleep(5)


def oled_display(count):
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

    # Draw different parts depending on count
    if count >= 0:
        draw.line((90, 45, 90, 5), fill=255)  # base
        draw.line((90, 5, 20, 5), fill=255)  # pole
        draw.line((20, 5, 20, 40), fill=255)  # top bar
        draw.line((20, 20, 30, 20), fill=255)  # rope
    if count >= 1:
        draw.ellipse((30, 15, 40, 25), outline=255)  # head
    if count >= 2:
        draw.line((40, 20, 60, 20), fill=255)  # body
    if count >= 3:
        draw.line((45, 20, 50, 12), fill=255)  # left arm
    if count >= 4:
        draw.line((45, 20, 50, 28), fill=255)  # right arm
    if count >= 5:
        draw.line((60, 20, 70, 12), fill=255)  # left leg
    if count >= 6:
        draw.line((60, 20, 70, 28), fill=255)  # right leg

    oled.image(image)
    oled.show()


running = True
while running:
    hangman()
    print("retry")
    while True:
        a_pressed = not buttonA.value
        b_pressed = not buttonB.value
        retry_window()
        if a_pressed:
            print("pressed")
            count = 0
            break  # restart by breaking out to re-run hangman()
        elif b_pressed:
            running = False
            break
        time.sleep(0.1)
