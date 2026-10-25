# Seasonal Clock - Bar
# Seasons change every 15 seconds
# Winter: 0-15 seconds
# Spring: 15-30 seconds
# Summer: 30-45 seconds
# Fall: 45-60 seconds

import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import math # Import math for sun rays

# --- Hardware Configuration ---

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

# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load font for text display
# NOTE: Ensure this font path is correct for your system or use a fallback.
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
except IOError:
    print("Defaulting to built-in font.")
    font = ImageFont.load_default()
    small_font = ImageFont.load_default()


# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Button setup
buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
# Use internal pull-ups; buttons then read LOW when pressed.
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# Seasonal colors and names
seasons = {
    'spring': {'color': (34, 139, 34), 'name': 'SPRING', 'symbol': '🌸'},  # Green
    'summer': {'color': (255, 165, 0), 'name': 'SUMMER', 'symbol': '☀️'},  # Orange
    'fall': {'color': (139, 69, 19), 'name': 'FALL', 'symbol': '🍂'},      # Brown
    'winter': {'color': (135, 206, 235), 'name': 'WINTER', 'symbol': '❄️'}  # Light Blue
}

# --- Utility Functions ---

def get_season_from_seconds(seconds):
    """Convert seconds within a minute to season based on 15s intervals"""
    if 0 <= seconds < 15:
        return 'winter'
    elif 15 <= seconds < 30:
        return 'spring'
    elif 30 <= seconds < 45:
        return 'summer'
    else: # 45 <= seconds < 60
        return 'fall'

def get_seasonal_progress(seconds):
    """Get progress within the current season (0.0 to 1.0)"""
    # Calculate seconds into the current 15s cycle
    current_cycle_seconds = seconds % 15
    return current_cycle_seconds / 15.0

def calculate_total_seasons(hour, minute, second):
    """Calculate total seasons passed since midnight (based on 15s seasons)"""
    total_seconds = hour * 3600 + minute * 60 + second
    total_seasons = int(total_seconds / 15)
    return total_seasons

# --- Drawing Utility Functions (No changes needed, kept for completeness) ---

def draw_snowflake(draw, x, y, color):
    """Draw a simple snowflake"""
    # Simple 4-point snowflake
    draw.line([(x, y-3), (x, y+3)], fill=color, width=1)
    draw.line([(x-3, y), (x+3, y)], fill=color, width=1)
    draw.line([(x-2, y-2), (x+2, y+2)], fill=color, width=1)
    draw.line([(x-2, y+2), (x+2, y-2)], fill=color, width=1)

def draw_flower(draw, x, y, color):
    """Draw a simple flower"""
    # Flower petals
    draw.ellipse((x-3, y-3, x+3, y+3), fill=(255, 192, 203))  # Pink petals
    draw.ellipse((x-2, y-4, x+2, y+4), fill=(255, 192, 203))
    draw.ellipse((x-4, y-2, x+4, y+2), fill=(255, 192, 203))
    # Center
    draw.ellipse((x-1, y-1, x+1, y+1), fill=(255, 255, 0))

def draw_leaf(draw, x, y, color):
    """Draw a simple autumn leaf"""
    # Simple leaf shape
    draw.ellipse((x-2, y-3, x+2, y+3), fill=color)
    draw.line([(x, y-3), (x, y+3)], fill=(101, 67, 33), width=1)  # Leaf vein

def draw_seasonal_scene(draw, season, progress, season_color):
    """Draw detailed seasonal scenes"""
    center_x = width // 2
    center_y = height // 2
    
    # Scene Drawing Logic (as in original script)
    if season == 'winter':
        # Winter scene: Snow-covered landscape
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(200, 220, 255))
        for i in range(8):
            x_flake = (i * 30 + int(progress * 20)) % width
            y_flake = (i * 25 + int(progress * 15)) % (ground_y - 20)
            draw_snowflake(draw, x_flake, y_flake, season_color)
        tree_x = center_x - 20
        tree_y = ground_y - 30
        draw.rectangle((tree_x, tree_y, tree_x + 8, ground_y), fill=(101, 67, 33))
        draw.line([(tree_x, tree_y), (tree_x - 15, tree_y - 20)], fill=(101, 67, 33), width=3)
        draw.line([(tree_x + 8, tree_y), (tree_x + 23, tree_y - 20)], fill=(101, 67, 33), width=3)
        draw.text((center_x - 10, center_y - 10), seasons[season]['symbol'], font=font, fill=season_color)
        
    elif season == 'spring':
        # Spring scene: Blooming flowers and green grass
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(34, 139, 34))
        flower_positions = [(30, ground_y - 10), (80, ground_y - 15), (130, ground_y - 8)]
        for fx, fy in flower_positions:
            draw_flower(draw, fx, fy, season_color)
        tree_x = center_x - 15
        tree_y = ground_y - 40
        draw.rectangle((tree_x, tree_y, tree_x + 6, ground_y), fill=(101, 67, 33))
        draw.ellipse((tree_x - 20, tree_y - 25, tree_x + 26, tree_y + 5), fill=(255, 192, 203))
        draw.text((center_x - 10, center_y + 10), seasons[season]['symbol'], font=font, fill=season_color)
        
    elif season == 'summer':
        # Summer scene: Bright sun and lush vegetation
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(50, 205, 50))
        sun_x = width - 40
        sun_y = 30
        draw.ellipse((sun_x - 15, sun_y - 15, sun_x + 15, sun_y + 15), fill=(255, 255, 0))
        for angle in range(0, 360, 45):
            ray_x = sun_x + int(25 * math.cos(math.radians(angle)))
            ray_y = sun_y + int(25 * math.sin(math.radians(angle)))
            draw.line([(sun_x, sun_y), (ray_x, ray_y)], fill=(255, 255, 0), width=2)
        tree_x = center_x - 20
        tree_y = ground_y - 50
        draw.rectangle((tree_x, tree_y, tree_x + 8, ground_y), fill=(101, 67, 33))
        draw.ellipse((tree_x - 25, tree_y - 30, tree_x + 33, tree_y + 10), fill=(0, 128, 0))
        draw.text((center_x - 10, center_y - 10), seasons[season]['symbol'], font=font, fill=season_color)
        
    elif season == 'fall':
        # Fall scene: Autumn leaves and harvest colors
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(160, 82, 45))
        for i in range(6):
            x_leaf = (i * 40 + int(progress * 30)) % width
            y_leaf = (i * 30 + int(progress * 25)) % (ground_y - 10)
            draw_leaf(draw, x_leaf, y_leaf, season_color)
        tree_x = center_x - 20
        tree_y = ground_y - 45
        draw.rectangle((tree_x, tree_y, tree_x + 8, ground_y), fill=(101, 67, 33))
        draw.ellipse((tree_x - 22, tree_y - 28, tree_x + 30, tree_y + 8), fill=(255, 140, 0))
        draw.text((center_x - 10, center_y + 10), seasons[season]['symbol'], font=font, fill=season_color)


def draw_seasonal_clock(draw, season, progress, total_seasons):
    """Draw the seasonal clock visualization"""
    # Clear the screen with season color (dimmed)
    season_color = seasons[season]['color']
    bg_color = tuple(int(c * 0.1) for c in season_color)  # Dimmed background
    draw.rectangle((0, 0, width, height), outline=0, fill=bg_color)
    
    # Draw season name at top
    season_name = seasons[season]['name']
    draw.text((x + 10, top + 5), season_name, font=font, fill=season_color)
    
    # Draw detailed seasonal illustrations
    draw_seasonal_scene(draw, season, progress, season_color)
    
    # Draw progress bar
    bar_width = width - 20
    bar_height = 15
    bar_x = 10
    bar_y = bottom - 60
    
    # Background bar
    draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
                   outline=season_color, fill=(0, 0, 0))
    
    # Progress fill
    fill_width = int(bar_width * progress)
    draw.rectangle((bar_x, bar_y, bar_x + fill_width, bar_y + bar_height),
                   outline=season_color, fill=season_color)
    
    # Draw total seasons passed
    seasons_text = f"Seasons: {total_seasons}"
    draw.text((x + 10, bottom - 40), seasons_text, font=small_font, fill=(255, 255, 255))
    
    # Draw progress percentage
    progress_text = f"{int(progress * 100)}%"
    draw.text((x + 10, bottom - 25), progress_text, font=small_font, fill=season_color)

# --- Main Loop Logic ---

# Interactive mode variables
interactive_mode = False
speed_multiplier = 1.0
last_button_check_time = 0 # Variable to track last button action time
DEBOUNCE_TIME = 0.5 # Debounce time in seconds

print("Seasonal Clock Started!")
print("Button A: Toggle interactive mode")
print("Button B: Change time speed (0.5x, 1x, 2x, 4x, 8x)")
print("Both buttons: Reset to real time")

# Variable to simulate fast-forwarded time
start_time = time.time()
interactive_time_offset = 0.0

while True:
    current_time_sec = time.time()
    
    # Check button states
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)
    
    # Handle button interactions with debouncing
    if (current_time_sec - last_button_check_time) > DEBOUNCE_TIME:
        
        if a_pressed and b_pressed:
            # Both buttons: Reset to real time
            interactive_mode = False
            speed_multiplier = 1.0
            interactive_time_offset = 0.0 # Reset offset
            print("Reset to real time")
            last_button_check_time = current_time_sec
            
        elif a_pressed and not b_pressed:
            # Button A: Toggle interactive mode
            interactive_mode = not interactive_mode
            if interactive_mode:
                 # Set initial offset when enabling interactive mode
                interactive_time_offset = time.time() - start_time 
            print(f"Interactive mode: {'ON' if interactive_mode else 'OFF'}")
            last_button_check_time = current_time_sec
            
        elif b_pressed and not a_pressed:
            # Button B: Change speed
            if interactive_mode:
                # Store the current progress time
                elapsed_interactive_time = (time.time() - start_time) * speed_multiplier + interactive_time_offset
                
                # Cycle speed multiplier
                if speed_multiplier == 1.0:
                    speed_multiplier = 2.0
                elif speed_multiplier == 2.0:
                    speed_multiplier = 4.0
                elif speed_multiplier == 4.0:
                    speed_multiplier = 8.0
                elif speed_multiplier == 8.0:
                    speed_multiplier = 0.5
                else: # speed_multiplier == 0.5
                    speed_multiplier = 1.0
                    
                # Calculate new offset to maintain perceived time across speed change
                interactive_time_offset = elapsed_interactive_time - (time.time() - start_time) * speed_multiplier

                print(f"Speed multiplier: {speed_multiplier}x")
                last_button_check_time = current_time_sec

    # Determine which time source to use
    if interactive_mode:
        # Calculate time as if it passed at the speed multiplier
        elapsed_time = (current_time_sec - start_time) * speed_multiplier + interactive_time_offset
        total_seconds_of_day = int(elapsed_time) % (24 * 3600) # Keep within a single day
    else:
        # Use real system time
        current_localtime = time.localtime(current_time_sec)
        total_seconds_of_day = current_localtime.tm_hour * 3600 + current_localtime.tm_min * 60 + current_localtime.tm_sec

    # Calculate season-specific variables
    second_in_minute = total_seconds_of_day % 60
    
    season = get_season_from_seconds(second_in_minute)
    progress = get_seasonal_progress(second_in_minute)
    total_seasons = int(total_seconds_of_day / 15) # 15 seconds per season
    
    # Draw and Display
    draw_seasonal_clock(draw, season, progress, total_seasons)
    disp.image(image, rotation)
    
    # Small delay for continuous drawing and main loop speed control
    time.sleep(0.05)