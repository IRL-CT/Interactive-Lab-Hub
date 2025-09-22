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

height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

draw = ImageDraw.Draw(image)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

# image cofig
#image = Image.open("pianohands.jpg").resize((width, height))

#load a TTF font.
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)

# Note system
note_map = {
    0: None,
    1: "c1", 2: "c1s", 3: "d1", 4: "d1s", 5: "e1", 6: "f1",
    7: "f1s", 8: "g1", 9: "g1s", 10: "a1", 11: "a1s", 12: "b1"
}
# image system
image_map = {
    1: "1piano", 2: "2piano", 3: "3piano", 4: "4piano", 5: "5piano", 6: "6piano",
    7: "7piano", 8: "8piano", 9: "9piano", 10: "10piano", 11: "11piano", 12: "12piano"
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
    print(now)
    hour = now.tm_hour % 12 or 12
    minute = now.tm_min
    
    tens = (minute // 10)
    ones = (minute % 10)
    print(f"Digits - Hour: {hour}, Tens: {tens}, Ones: {ones}")

    # Map all numbers to notes
    notes_to_play = [note_map[5], note_map[hour], note_map[tens], note_map[ones]]

    print("Playing notes:", notes_to_play)

    for n in notes_to_play:
        print("Playing note:", n)
        play_note(n)
        time.sleep(0.5)

# display time
def show_time_on_screen():
    # Create a new image for the time display, starting with the background
    time_image = background_image.copy()
    draw = ImageDraw.Draw(time_image)

    # Get current time
    now = time.localtime()
    time_text = f"{now.tm_hour:02d}:{now.tm_min:02d}"

    # Calculate text position to center it
    text_width, text_height = draw.textsize(time_text, font=font)
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2

    # Draw a semi-transparent black box behind the text for better readability
    draw.rectangle(
        (text_x - 10, text_y - 10, text_x + text_width + 10, text_y + text_height + 10),
        fill=(0, 0, 0, 128)
    )
    # Draw the time text
    draw.text((text_x, text_y), time_text, font=font, fill=(255, 255, 255))
    
    # Update display
    disp.image(time_image, rotation)

# --- Main Loop ---
last_minute = -1

while True:    
    now = time.localtime()
    
    # Get the current hour in 12-hour format
    current_hour_24 = datetime.now().hour
    current_hour_12 = current_hour_24 % 12
    if current_hour_12 == 0:
        current_hour_12 = 12

    # Load the corresponding image from the map
    image_file = image_map[current_hour_12]
    
    # Open and resize the image to fit the display
    clock_img = Image.open(image_file).resize((width, height)).convert("RGB")

    draw = ImageDraw.Draw(clock_img)

    current_time = time.strftime("%M: %S %p")
    
    # Get the bounding box of the text to calculate its size
    text_bbox = draw.textbbox((0, 0), current_time, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Calculate the bottom-right position
    # Subtract text size from image size, then add a small margin (e.g., 5 pixels)
    x = width - text_width - 5
    y = height - text_height - 5
    # Position the text on top of the image (you may need to adjust these coordinates)
    draw.text((0, 0), current_time, font=font, fill="white")
    disp.image(clock_img, rotation)
    
    if now.tm_min != last_minute:
        play_time_as_notes()
        last_minute = now.tm_min

    time.sleep(30)
