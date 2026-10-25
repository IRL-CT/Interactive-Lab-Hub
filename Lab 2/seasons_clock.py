import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# --- Display and Pin Configuration ---
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

# --- Image Setup ---
height = disp.width
width = disp.height
rotation = 90

# Pre-load all the season images
seasons = ['fall.png', 'winter.png', 'spring.png', 'summer.png']
images = []
for season in seasons:
    img_path = f'images/seasons/{season}'
    img = Image.open(img_path).convert('RGB')
    
    # Resize the image to fit the display while maintaining aspect ratio
    img.thumbnail((width, height), Image.Resampling.LANCZOS)
    
    # Create a new blank image and paste the resized image onto it to center it
    new_img = Image.new("RGB", (width, height), (0, 0, 0))
    paste_x = (width - img.width) // 2
    paste_y = (height - img.height) // 2
    new_img.paste(img, (paste_x, paste_y))
    
    images.append(new_img)

# --- Backlight, Font, and Button Setup ---
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# --- Interval Configuration ---
intervals = [1, 3, 5, 10, 15, 20, 30, 60]
interval_index = intervals.index(15)  # Start at 15 seconds
image_change_interval = intervals[interval_index]
last_button_press_time = time.time()
button_debounce_time = 0.5

# --- Main Loop with Image, Counter, and Button Handling ---
image_index = 0
last_image_change_time = time.time()
seasons_passed = 0

while True:
    current_time = time.time()

    # Handle button presses with debouncing
    if not buttonA.value and (current_time - last_button_press_time) > button_debounce_time:
        # Button A pressed (speed up)
        interval_index = (interval_index + 1) % len(intervals)
        image_change_interval = intervals[interval_index]
        last_button_press_time = current_time
    
    if not buttonB.value and (current_time - last_button_press_time) > button_debounce_time:
        # Button B pressed (slow down)
        interval_index = (interval_index - 1 + len(intervals)) % len(intervals)
        image_change_interval = intervals[interval_index]
        last_button_press_time = current_time

    # Check if it's time to switch the image based on the current interval
    if current_time - last_image_change_time >= image_change_interval:
        image_index = (image_index + 1) % len(images)
        last_image_change_time = current_time
        seasons_passed += 1

    # Create the text string with the seasons counter
    seasons_text = f"Seasons Passed: {seasons_passed}"
    interval_text = f"Interval: {image_change_interval}s"

    # Get the current image to display
    current_image = images[image_index]

    # Create a copy of the current image to draw the text on
    display_image = current_image.copy()
    draw = ImageDraw.Draw(display_image)

    # Calculate text positions
    bbox_seasons = draw.textbbox((0, 0), seasons_text, font=font)
    text_width_seasons = bbox_seasons[2] - bbox_seasons[0]
    text_x_seasons = (width - text_width_seasons) // 2
    text_y_seasons = height - font.size * 2 - 10 # Position for the seasons count

    bbox_interval = draw.textbbox((0, 0), interval_text, font=font)
    text_width_interval = bbox_interval[2] - bbox_interval[0]
    text_x_interval = (width - text_width_interval) // 2
    text_y_interval = height - font.size - 5 # Position for the interval

    # Draw the text on the image copy
    draw.text((text_x_seasons, text_y_seasons), seasons_text, font=font, fill="#FFFFFF")
    draw.text((text_x_interval, text_y_interval), interval_text, font=font, fill="#FFFFFF")

    # Display the final image on the screen
    disp.image(display_image, rotation)

    time.sleep(0.1)