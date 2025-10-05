import time
import digitalio
import board
from PIL import Image
import adafruit_rgb_display.st7789 as st7789

# --- Display and Pin Configuration ---
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Configure SPI and the display
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

# --- Backlight Setup ---
# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# --- Image Setup and Display ---
# Get display dimensions and rotation
height = disp.width
width = disp.height
rotation = 90
image_path = 'duck.png'

try:
    # 1. Open and convert the image
    img = Image.open(image_path).convert('RGB')
    
    # 2. Resize the image to fit the display while maintaining aspect ratio
    img.thumbnail((width, height), Image.Resampling.LANCZOS)
    
    # 3. Create a new blank image and paste the resized image onto it to center it
    display_image = Image.new("RGB", (width, height), (0, 0, 0))
    paste_x = (width - img.width) // 2
    paste_y = (height - img.height) // 2
    display_image.paste(img, (paste_x, paste_y))

    # 4. Display the image
    disp.image(display_image, rotation)

    # 5. Keep the script running forever so the image stays on the screen
    print(f"Displaying '{image_path}' indefinitely. Press Ctrl+C to stop.")
    while True:
        time.sleep(1) # Sleep to keep the CPU usage low

except FileNotFoundError:
    print(f"Error: Image file not found at '{image_path}'")
except Exception as e:
    print(f"An error occurred: {e}")