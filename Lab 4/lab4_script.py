from digitalio import DigitalInOut
import busio
import board
import time
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.ili9341 as ili9341
import adafruit_rgb_display.st7789 as st7789  # pylint: disable=unused-import
import adafruit_rgb_display.hx8357 as hx8357  # pylint: disable=unused-import
import adafruit_rgb_display.st7735 as st7735  # pylint: disable=unused-import
import adafruit_rgb_display.ssd1351 as ssd1351  # pylint: disable=unused-import
import adafruit_rgb_display.ssd1331 as ssd1331  # pylint: disable=unused-import
import adafruit_ssd1306
import qwiic_proximity
import adafruit_mpr121
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility
from adafruit_seesaw import seesaw, rotaryio, digitalio
import qwiic_joystick

# Configuration for CS and DC pins (these are PiTFT defaults):
cs_pin = DigitalInOut(board.D5)
dc_pin = DigitalInOut(board.D25)
reset_pin = DigitalInOut(board.D24)

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 24000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# pylint: disable=line-too-long
# Create the display:
# disp = st7789.ST7789(spi, rotation=90,                            # 2.0" ST7789
# disp = st7789.ST7789(spi, height=240, y_offset=80, rotation=180,  # 1.3", 1.54" ST7789
# disp = st7789.ST7789(spi, rotation=90, width=135, height=240, x_offset=53, y_offset=40, # 1.14" ST7789
# disp = hx8357.HX8357(spi, rotation=180,                           # 3.5" HX8357
# disp = st7735.ST7735R(spi, rotation=90,                           # 1.8" ST7735R
# disp = st7735.ST7735R(spi, rotation=270, height=128, x_offset=2, y_offset=3,   # 1.44" ST7735R
# disp = st7735.ST7735R(spi, rotation=90, bgr=True,                 # 0.96" MiniTFT ST7735R
# disp = ssd1351.SSD1351(spi, rotation=180,                         # 1.5" SSD1351
# disp = ssd1351.SSD1351(spi, height=96, y_offset=32, rotation=180, # 1.27" SSD1351
# disp = ssd1331.SSD1331(spi, rotation=180,                         # 0.96" SSD1331
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
# pylint: enable=line-too-long

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
if disp.rotation % 180 == 90:
    height = disp.width  # we swap height/width to rotate it to landscape!
    width = disp.height
else:
    width = disp.width  # we swap height/width to rotate it to landscape!
    height = disp.height
image = Image.new("RGB", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image)

# light setup
i2c = busio.I2C(board.SCL, board.SDA)
apds = APDS9960(i2c)
apds.enable_color = True

# prox setup
oProx = qwiic_proximity.QwiicProximity()
if oProx.connected == False:
    time.sleep(0.05)
oProx.begin()

# joystick setup
myJoystick = qwiic_joystick.QwiicJoystick(i2c)
myJoystick.begin()

# rot setup
seesaw = seesaw.Seesaw(i2c, addr=0x36)

# oled setup
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
font = ImageFont.load_default()
# start with a blank screen
oled.fill(0)
oled.show()

seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF

seesaw.pin_mode(24, seesaw.INPUT_PULLUP)
button = digitalio.DigitalIO(seesaw, 24)
button_held = False

encoder = rotaryio.IncrementalEncoder(seesaw)
last_position = -encoder.position

# initialize capacity twizzer
mpr121 = adafruit_mpr121.MPR121(i2c, address=0x5A)

def display(image_name):
    image = Image.open(image_name)
    backlight = DigitalInOut(board.D22)
    backlight.switch_to_output()
    backlight.value = True


    # Scale the image to the smaller screen dimension
    image_ratio = image.width / image.height
    screen_ratio = width / height
    if screen_ratio < image_ratio:
        scaled_width = image.width * height // image.height
        scaled_height = height
    else:
        scaled_width = width
        scaled_height = image.height * width // image.width
    image = image.resize((scaled_width, scaled_height), Image.BICUBIC)

    # Crop and center the image
    x = scaled_width // 2 - width // 2
    y = scaled_height // 2 - height // 2
    image = image.crop((x, y, x + width, y + height))

    # Display image.
    disp.image(image)


def draw_hp_bar(hp: int, max_hp: int = 5):
    """
    Draw an HP bar with 'hp' filled blocks and 'max_hp' total blocks.
    """
    # Create a blank image for drawing
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    # Draw "HP" text
    draw.text((0, 10), "HP", font=font, fill=1)

    # Define HP bar layout
    block_width = 18
    block_height = 10
    spacing = 2
    start_x = 30
    start_y = 10

    # Draw filled / empty HP blocks
    for i in range(max_hp):
        x = start_x + i * (block_width + spacing)
        if i < hp:
            draw.rectangle([x, start_y, x + block_width, start_y + block_height], fill=1)
        else:
            draw.rectangle([x, start_y, x + block_width, start_y + block_height], outline=1)

    # Push the image to the display
    oled.image(image)
    oled.show()

def display_text(text: str):
    """
    Display a single line of text on the OLED.
    """
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    draw.text((0, 10), text, font=font, fill=1)
    oled.image(image)
    oled.show()

def joystick():
    # if |x - 512| + |y - 512| > 200 return True
    x = myJoystick.horizontal
    y = myJoystick.vertical
    if abs(x - 512) + abs(y - 512) > 200:
        return True
    else:
        return False

def prox_sensor():
    val = oProx.get_proximity()
    return val <= 10.0


def light_sensor():
    # wait for color data to be ready
    while not apds.color_data_ready:
        time.sleep(0.005)
    r, g, b, c = apds.color_data
    if c <= 100:
        return True
    else:
        return False

def rotary():
    # negate the position to make clockwise rotation positive
    global last_position
    position = -encoder.position
    diff = abs(last_position - position)
    last_position = position
    if diff >= 5:
        return True
    else:
        return False


trigger = False
hp=5
while True:
    draw_hp_bar(hp)

    # 0 = lightning, 1= fireball, 2 = earthquake, 3 = slime
    if mpr121[0].value:
        display("lightning.png")
        start_time = time.time()
        trigger = False
        while time.time() - start_time < 2:
            if joystick() or prox_sensor() or rotary():
                trigger = False
                break
            if light_sensor():
                trigger = True
                display("victory.png")
                break
        if not trigger:
            hp -= 1
            draw_hp_bar(hp)

    if mpr121[1].value:
        display("fireball.png")
        start_time = time.time()
        trigger = False
        while time.time() - start_time < 2:
            if light_sensor() or prox_sensor() or rotary():
                trigger = False
                break
            if joystick():
                trigger = True
                display("victory.png")
                break
        if not trigger:
            hp -= 1
            draw_hp_bar(hp)

    if mpr121[2].value:
        display("earthquake.png")
        start_time = time.time()
        trigger = False
        while time.time() - start_time < 2:
            if joystick() or light_sensor() or rotary():
                trigger = False
                break
            if prox_sensor():
                trigger = True
                display("victory.png")
                break
        if not trigger:
            hp -= 1
            draw_hp_bar(hp)

    if mpr121[3].value:
        display("slime.png")
        start_time = time.time()
        trigger = False
        while time.time() - start_time < 2:
            if joystick() or light_sensor() or prox_sensor():
                trigger = False
                break
            if rotary():
                trigger = True
                display("victory.png")
                break

        if not trigger:
            hp -= 1
            draw_hp_bar(hp)

    if hp == 0:
            display("skeleton.png")

