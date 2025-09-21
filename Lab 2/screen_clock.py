import time
import os
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

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
image = Image.open("pianohands.jpg")


# Alternatively load a TTF font.
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Scale the image to the smaller screen dimension
image_ratio = image.width / image.height
screen_ratio = width / height
if screen_ratio < image_ratio:
    scaled_height = height
else:
    scaled_width = width
    scaled_height = image.height * width // image.width
image = image.resize((scaled_width, scaled_height), Image.BICUBIC)

# Crop and center the image
x = scaled_width // 2 - width // 2
y = scaled_height // 2 - height // 2
image = image.crop((x, y, x + width, y + height))

# Setup button on gpio23
button = digitalio.DigitalInOut(board.D23)
button.switch_to_input(pull=digitalio.Pull.UP)

# Note system
note_map = {
    1: "a1", 2: "a1s", 3: "b1", 4: "c1", 5: "c1s", 6: "d1",
    7: "d1s", 8: "e1", 9: "f1", 10: "f1s", 11: "g1", 12: "g1s"
}

#play note file
def play_note(note_key):
    filename = f"{note_key}.wav"
    try:
        subprocess.run(["aplay", "-q", filename])
    except Exception as e:
        print(f"Error playing {filename}: {e}")

#time to notes
def play_time_as_notes():
    now = time.localtime()
    hour = now.tm_hour % 12 or 12
    minute = now.tm_min
    
    tens = (minute // 10) % 12 or 12
    ones = (minute % 12) or 12
    
    notes_to_play = [note_map[hour], note_map[tens], note_map[ones]]
    print("Playing notes:", notes_to_play)

    for n in notes_to_play:
        play_note(n)

# display time
def show_time_on_screen():
    now = time.localtime()
    time_text = f"{now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}"

    # Clear screen
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

    # Draw time in the center
    text_width, text_height = draw.textsize(time_text, font=font)
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), time_text, font=font, fill=(255, 255, 255))

    # Update display
    disp.image(image, rotation)

while True:    

    # Get time and display it
    current_time = time.strftime("%H:%M:%S")
    # Draw time 
    y = 3
    x = 1 
    draw.text((x, y), current_time, font=font, fill="#FFFFFF")
    # Display image.
    disp.image(image, rotation)
    play_time_as_notes()
    #button press
    if not button.value:
        if not button.value:  # LOW when pressed
            show_time_on_screen()
            time.sleep(0.3)  # debounce
    else:
        time.sleep(0.05)

    time.sleep(30)
