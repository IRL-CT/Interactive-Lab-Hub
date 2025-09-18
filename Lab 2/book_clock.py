import board
import digitalio
import adafruit_rgb_display.st7789 as st7789
import time

# Set up pins correctly
cs_pin = digitalio.DigitalInOut(board.CE0)   # Chip select
dc_pin = digitalio.DigitalInOut(board.D22)   # Data/command
reset_pin = None                             # Or digitalio.DigitalInOut(board.D27) if wired

# Initialize SPI bus
spi = board.SPI()

# Create the display object
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=64000000
)

rotation = 90
width = disp.width
height = disp.height

# --- Buttons ---
btn_top = digitalio.DigitalInOut(board.D5)   # Button A
btn_top.switch_to_input(pull=digitalio.Pull.UP)

btn_bottom = digitalio.DigitalInOut(board.D6)  # Button B
btn_bottom.switch_to_input(pull=digitalio.Pull.UP)

# --- Drawing setup ---
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

# --- Helper ---
def pages_today(total_pages=24):
    t = localtime()
    seconds_today = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
    return int((seconds_today / 86400.0) * total_pages)

# --- State ---
page_counter = 0
show_counter = False

# --- Page turn animation ---
def page_turn():
    for offset in range(0, width//2, 20):
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
        mid = width // 2

        # static right page
        draw.rectangle((mid + 5, 40, width - 10, 200), outline=(255, 255, 255))

        # animated left page sliding away
        draw.rectangle((10 + offset, 40, mid - 5 + offset, 200), outline=(255, 255, 255))

        disp.image(image, rotation)
        time.sleep(0.05)

# --- Main loop ---
while True:
    if not btn_top.value:  # pressed (LOW)
        page_counter += 1
        page_turn()

    if not btn_bottom.value:  # pressed
        show_counter = not show_counter

    # Clear screen
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

    if show_counter:
        draw.text((50, 120), f"Counter: {page_counter}", font=font, fill=(0, 255, 0))
    else:
        total_pages = 24
        current_page = pages_today(total_pages)
        mid = width // 2

        # Draw book outline
        draw.rectangle((10, 40, mid - 5, 200), outline=(255, 255, 255))
        draw.rectangle((mid + 5, 40, width - 10, 200), outline=(255, 255, 255))

        # Show page numbers
        draw.text((30, 100), f"Page {current_page}", font=font, fill=(255, 255, 0))
        draw.text((mid + 20, 100), f"of {total_pages}", font=font, fill=(0, 255, 255))

        # Progress bar
        progress = current_page / total_pages
        bar_width = int((width - 20) * progress)
        draw.rectangle((10, 210, 10 + bar_width, 230), fill=(150, 75, 0))

    # Push to display
    disp.image(image, rotation)
    time.sleep(0.1)
