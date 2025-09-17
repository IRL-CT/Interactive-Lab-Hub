import time
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
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Note Setup
note_freqs = {
    1: 440.00,   # A
    2: 466.16,   # Bb
    3: 493.88,   # B
    4: 523.25,   # C
    5: 554.37,   # C#
    6: 587.33,   # D
    7: 622.25,   # Eb
    8: 659.25,   # E
    9: 698.46,   # F
    10: 739.99,  # F#
    11: 783.99,  # G
    12: 830.61   # Ab
}

def number_to_notes(n):
    """Convert a number into notes by its digits (0 skipped)."""
    digits = [int(d) for d in str(n)]
    notes = []
    for d in digits:
        if d == 0:
            continue
        pitch = ((d - 1) % 12) + 1
        notes.append(note_freqs[pitch])
    return notes

def play_tone(frequency, duration=0.4, fs=44100):
    """Generate and play a sine wave for the given frequency."""
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    sd.play(wave, samplerate=fs)
    sd.wait()

# Main Loop
last_minute = None
while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=400)

    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 
now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute

    # Only update & play when the minute changes
    if minute != last_minute:
        last_minute = minute

        # Clear display
        draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

        # Draw current time
        time_text = now.strftime("%H:%M")
        draw.text((10, 50), time_text, font=font, fill="#FFFFFF")

        # Show on screen
        disp.image(image, rotation)

        # Get notes for hour + minute
        notes = number_to_notes(hour) + number_to_notes(minute)
        print(f"{time_text} → Notes {notes}")

        # Play notes
        for freq in notes:
            play_tone(freq)
    # Display image.
    disp.image(image, rotation)
    time.sleep(1)
