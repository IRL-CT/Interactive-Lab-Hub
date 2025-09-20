import time
import subprocess
import digitalio
import board
import datetime
import numpy as np
import sounddevice as sd
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

try:
    print("Attempting to initialize the ST7789 display...")
    # Create the ST7789 display object:
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
    print("Display initialized successfully!")
# Displaying Image
    image = Image.new("RGB", (width, height))
# Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
    disp.image(image)
    image = Image.open("pianohands.jpg")

# Alternatively load a TTF font. 
    font = ImageFont.truetype("Musicografi.ttf", 18)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # This block will run no matter what, ensuring pins are released.
    print("Deinitializing GPIO pins...")
    if cs_pin:
        cs_pin.deinit()
    if dc_pin:
        dc_pin.deinit()
    if reset_pin:
        reset_pin.deinit()
    print("Cleanup complete.") 
#Note Setup
note_freqs = {
    '1': 440.00,  # A
    '2': 466.16,  # Bb
    '3': 493.88,  # B
    '4': 523.25,  # C
    '5': 554.37,  # C#
    '6': 587.33,  # D
    '7': 622.25,  # Eb
    '8': 659.25,  # E
    '9': 698.46,  # F
    '10': 739.99, # F#
    '11': 783.99, # G
    '12': 830.61  # Ab
}
def play_tone(frequency, duration=0.4, fs=44100):
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    sd.play(wave, samplerate=fs)
    sd.wait()

def get_time_digits(hour, minute):
    """
    Converts the current hour and minute into a list of digit strings.
    For example, 1:05 PM becomes ['1', '0', '5']. 12:30 PM becomes ['1', '2', '3', '0'].
    """
    # Convert 24-hour time to 12-hour format for the audible part
    if hour == 0:
        hour_12 = 12  # Midnight is 12 AM
    elif hour > 12:
        hour_12 = hour - 12
    else:
        hour_12 = hour

    # Format into a single string, e.g., 7:05 -> "705", 12:34 -> "1234"
    # The minute is zero-padded to always have two digits.
    time_str = f"{hour_12}{minute:02d}"
    
    # Return a list of the individual characters (digits)
    return list(time_str)

print("Starting Audio Clock. Press Ctrl+C to exit.")
# Main Loop
while True:
    try:
        # Get Current time
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute

        # --- Display Logic ---
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        # Format time for display (e.g., "01:05 PM")
        time_display_str = now.strftime("%I:%M %p")
        
        # Get bounding box of the text
        (font_width, font_height) = large_font.getsize(time_display_str)
        
        # Draw the time centered on the screen
        draw.text(
            (width // 2 - font_width // 2, height // 2 - font_height // 2),
            time_display_str,
            font=large_font,
            fill=255,
        )

        # Display image.
        if disp:
            disp.image(image)
            disp.show()
        
        # Also print to console for debugging
        print(f"Current Time: {time_display_str}")
        
        # --- Audio Logic ---
        # Get the sequence of digits for the current time
        time_digits = get_time_digits(hour, minute)
        
        print(f"Playing tones for digits: {time_digits}")

        # A slightly longer pause before starting the sequence
        time.sleep(0.5)

        # Loop through each digit and play its corresponding note
        for digit in time_digits:
            frequency = NOTE_FREQS[digit]
            play_tone(frequency, duration=0.3)
            time.sleep(0.1) # A short pause between notes

        # Wait until the start of the next minute
        # This makes the clock announce the time once every minute
        seconds_to_wait = 60 - now.second
        print(f"Waiting for {seconds_to_wait} seconds until the next minute...\n")
        time.sleep(seconds_to_wait)

    except KeyboardInterrupt:
        print("\nExiting clock.")
        # Clear the display on exit
        if disp:
            disp.fill(0)
            disp.show()
        break
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(10) # Wait before retrying

