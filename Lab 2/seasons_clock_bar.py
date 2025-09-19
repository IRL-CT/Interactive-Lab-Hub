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
height = disp.width  # we swap height/width to rotate it to landscape!
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
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Button setup (from screen_test.py)
buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
# Use internal pull-ups; buttons then read LOW when pressed.
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# Seasonal colors and names
seasons = {
    'spring': {'color': (34, 139, 34), 'name': 'SPRING', 'symbol': '🌸'},  # Green
    'summer': {'color': (255, 165, 0), 'name': 'SUMMER', 'symbol': '☀️'},  # Orange
    'fall': {'color': (139, 69, 19), 'name': 'FALL', 'symbol': '🍂'},      # Brown
    'winter': {'color': (135, 206, 235), 'name': 'WINTER', 'symbol': '❄️'}  # Light Blue
}

def get_season_from_seconds(seconds):
    """Convert seconds within a minute to season"""
    if 0 <= seconds < 15:      # Winter: 0-15 seconds
        return 'winter'
    elif 15 <= seconds < 30:   # Spring: 15-30 seconds  
        return 'spring'
    elif 30 <= seconds < 45:   # Summer: 30-45 seconds
        return 'summer'
    else:                      # Fall: 45-60 seconds
        return 'fall'

def get_seasonal_progress(seconds):
    """Get progress within the current season (0.0 to 1.0)"""
    if 0 <= seconds < 15:      # Winter: 0-15 seconds
        return seconds / 15.0
    elif 15 <= seconds < 30:   # Spring: 15-30 seconds
        return (seconds - 15) / 15.0
    elif 30 <= seconds < 45:   # Summer: 30-45 seconds
        return (seconds - 30) / 15.0
    else:                      # Fall: 45-60 seconds
        return (seconds - 45) / 15.0

def calculate_total_seasons(hour, minute, second):
    """Calculate total seasons passed since midnight"""
    # 4 seasons per minute (60 seconds / 15 seconds per season)
    total_seconds = hour * 3600 + minute * 60 + second
    total_seasons = int(total_seconds / 15)  # 15 seconds per season
    return total_seasons

def draw_seasonal_clock(draw, season, progress, total_seasons):
    """Draw the seasonal clock visualization with detailed seasonal illustrations"""
    # Clear the screen with season color (dimmed)
    season_color = seasons[season]['color']
    bg_color = tuple(int(c * 0.1) for c in season_color)  # Dimmed background
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

def draw_seasonal_scene(draw, season, progress, season_color):
    """Draw detailed seasonal scenes"""
    center_x = width // 2
    center_y = height // 2
    
    if season == 'winter':
        # Winter scene: Snow-covered landscape
        # Draw snow-covered ground
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(200, 220, 255))
        
        # Draw snowflakes
        for i in range(8):
            x = (i * 30 + int(progress * 20)) % width
            y = (i * 25 + int(progress * 15)) % (ground_y - 20)
            draw_snowflake(draw, x, y, season_color)
        
        # Draw bare tree
        tree_x = center_x - 20
        tree_y = ground_y - 30
        draw.rectangle((tree_x, tree_y, tree_x + 8, ground_y), fill=(101, 67, 33))  # Trunk
        # Branches
        draw.line([(tree_x, tree_y), (tree_x - 15, tree_y - 20)], fill=(101, 67, 33), width=3)
        draw.line([(tree_x + 8, tree_y), (tree_x + 23, tree_y - 20)], fill=(101, 67, 33), width=3)
        
        # Draw winter symbol
        draw.text((center_x - 10, center_y - 10), '❄️', font=font, fill=season_color)
        
    elif season == 'spring':
        # Spring scene: Blooming flowers and green grass
        # Draw green ground
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(34, 139, 34))
        
        # Draw flowers
        flower_positions = [(30, ground_y - 10), (80, ground_y - 15), (130, ground_y - 8)]
        for fx, fy in flower_positions:
            draw_flower(draw, fx, fy, season_color)
        
        # Draw blooming tree
        tree_x = center_x - 15
        tree_y = ground_y - 40
        draw.rectangle((tree_x, tree_y, tree_x + 6, ground_y), fill=(101, 67, 33))  # Trunk
        # Blooming branches
        draw.ellipse((tree_x - 20, tree_y - 25, tree_x + 26, tree_y + 5), fill=(255, 192, 203))  # Pink blossoms
        
        # Draw spring symbol
        draw.text((center_x - 10, center_y + 10), '🌸', font=font, fill=season_color)
        
    elif season == 'summer':
        # Summer scene: Bright sun and lush vegetation
        # Draw bright ground
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(50, 205, 50))
        
        # Draw sun
        sun_x = width - 40
        sun_y = 30
        draw.ellipse((sun_x - 15, sun_y - 15, sun_x + 15, sun_y + 15), fill=(255, 255, 0))
        # Sun rays
        for angle in range(0, 360, 45):
            import math
            ray_x = sun_x + int(25 * math.cos(math.radians(angle)))
            ray_y = sun_y + int(25 * math.sin(math.radians(angle)))
            draw.line([(sun_x, sun_y), (ray_x, ray_y)], fill=(255, 255, 0), width=2)
        
        # Draw lush tree
        tree_x = center_x - 20
        tree_y = ground_y - 50
        draw.rectangle((tree_x, tree_y, tree_x + 8, ground_y), fill=(101, 67, 33))  # Trunk
        # Full green canopy
        draw.ellipse((tree_x - 25, tree_y - 30, tree_x + 33, tree_y + 10), fill=(0, 128, 0))
        
        # Draw summer symbol
        draw.text((center_x - 10, center_y - 10), '☀️', font=font, fill=season_color)
        
    elif season == 'fall':
        # Fall scene: Autumn leaves and harvest colors
        # Draw brown/orange ground
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(160, 82, 45))
        
        # Draw falling leaves
        for i in range(6):
            x = (i * 40 + int(progress * 30)) % width
            y = (i * 30 + int(progress * 25)) % (ground_y - 10)
            draw_leaf(draw, x, y, season_color)
        
        # Draw autumn tree
        tree_x = center_x - 20
        tree_y = ground_y - 45
        draw.rectangle((tree_x, tree_y, tree_x + 8, ground_y), fill=(101, 67, 33))  # Trunk
        # Autumn colored canopy
        draw.ellipse((tree_x - 22, tree_y - 28, tree_x + 30, tree_y + 8), fill=(255, 140, 0))
        
        # Draw fall symbol
        draw.text((center_x - 10, center_y + 10), '🍂', font=font, fill=season_color)

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
    draw.ellipse((x-3, y-3, x+3, y+3), fill=(255, 192, 203))  # Pink petals
    draw.ellipse((x-2, y-4, x+2, y+4), fill=(255, 192, 203))
    draw.ellipse((x-4, y-2, x+4, y+2), fill=(255, 192, 203))
    # Center
    draw.ellipse((x-1, y-1, x+1, y+1), fill=(255, 255, 0))

def draw_leaf(draw, x, y, color):
    """Draw a simple autumn leaf"""
    # Simple leaf shape
    draw.ellipse((x-2, y-3, x+2, y+3), fill=color)
    draw.line([(x, y-3), (x, y+3)], fill=(101, 67, 33), width=1)  # Leaf vein

# Interactive mode variables
interactive_mode = False
speed_multiplier = 1.0

print("Seasonal Clock Started!")
print("Button A: Toggle interactive mode")
print("Button B: Change time speed")
print("Both buttons: Reset to real time")

while True:
    # Get current time
    current_time = time.localtime()
    hour = current_time.tm_hour
    minute = current_time.tm_min
    second = current_time.tm_sec
    
    # Check button states
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)
    
    # Handle button interactions
    if a_pressed and b_pressed:
        # Both buttons: Reset to real time
        interactive_mode = False
        speed_multiplier = 1.0
        print("Reset to real time")
    elif a_pressed and not b_pressed:
        # Button A: Toggle interactive mode
        interactive_mode = not interactive_mode
        print(f"Interactive mode: {'ON' if interactive_mode else 'OFF'}")
    elif b_pressed and not a_pressed:
        # Button B: Change speed
        if interactive_mode:
            speed_multiplier = speed_multiplier * 2.0
            if speed_multiplier > 8.0:
                speed_multiplier = 0.5
            print(f"Speed multiplier: {speed_multiplier}x")
    
    # Calculate total seasons passed
    total_seasons = calculate_total_seasons(hour, minute, second)
    
    # Modify time if in interactive mode
    if interactive_mode:
        # Create a modified second based on speed
        modified_second = (second + int(time.time() * speed_multiplier)) % 60
        season = get_season_from_seconds(modified_second)
        progress = get_seasonal_progress(modified_second)
        # For interactive mode, also modify the total seasons calculation
        modified_total_seconds = hour * 3600 + minute * 60 + modified_second
        total_seasons = int(modified_total_seconds / 15)
    else:
        # Use real time
        season = get_season_from_seconds(second)
        progress = get_seasonal_progress(second)
    
    # Draw the seasonal clock
    draw_seasonal_clock(draw, season, progress, total_seasons)
    
    # Display image
    disp.image(image, rotation)
    
    # Small delay for button debouncing and display refresh
    time.sleep(0.1)

# Seasonal Clock - Time measured through seasons
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
height = disp.width  # we swap height/width to rotate it to landscape!
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
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Button setup (from screen_test.py)
buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
# Use internal pull-ups; buttons then read LOW when pressed.
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# Seasonal colors and names
seasons = {
    'spring': {'color': (34, 139, 34), 'name': 'SPRING', 'symbol': '🌸'},  # Green
    'summer': {'color': (255, 165, 0), 'name': 'SUMMER', 'symbol': '☀️'},  # Orange
    'fall': {'color': (139, 69, 19), 'name': 'FALL', 'symbol': '🍂'},      # Brown
    'winter': {'color': (135, 206, 235), 'name': 'WINTER', 'symbol': '❄️'}  # Light Blue
}

def get_season_from_seconds(seconds):
    """Convert seconds within a minute to season"""
    if 0 <= seconds < 15:      # Winter: 0-15 seconds
        return 'winter'
    elif 15 <= seconds < 30:   # Spring: 15-30 seconds  
        return 'spring'
    elif 30 <= seconds < 45:   # Summer: 30-45 seconds
        return 'summer'
    else:                      # Fall: 45-60 seconds
        return 'fall'

def get_seasonal_progress(seconds):
    """Get progress within the current season (0.0 to 1.0)"""
    if 0 <= seconds < 15:      # Winter: 0-15 seconds
        return seconds / 15.0
    elif 15 <= seconds < 30:   # Spring: 15-30 seconds
        return (seconds - 15) / 15.0
    elif 30 <= seconds < 45:   # Summer: 30-45 seconds
        return (seconds - 30) / 15.0
    else:                      # Fall: 45-60 seconds
        return (seconds - 45) / 15.0

def calculate_total_seasons(hour, minute, second):
    """Calculate total seasons passed since midnight"""
    # 4 seasons per minute (60 seconds / 15 seconds per season)
    total_seconds = hour * 3600 + minute * 60 + second
    total_seasons = int(total_seconds / 15)  # 15 seconds per season
    return total_seasons

def draw_seasonal_clock(draw, season, progress, total_seasons):
    """Draw the seasonal clock visualization with detailed seasonal illustrations"""
    # Clear the screen with season color (dimmed)
    season_color = seasons[season]['color']
    bg_color = tuple(int(c * 0.1) for c in season_color)  # Dimmed background
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

def draw_seasonal_scene(draw, season, progress, season_color):
    """Draw detailed seasonal scenes"""
    center_x = width // 2
    center_y = height // 2
    
    if season == 'winter':
        # Winter scene: Snow-covered landscape
        # Draw snow-covered ground
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(200, 220, 255))
        
        # Draw snowflakes
        for i in range(8):
            x = (i * 30 + int(progress * 20)) % width
            y = (i * 25 + int(progress * 15)) % (ground_y - 20)
            draw_snowflake(draw, x, y, season_color)
        
        # Draw bare tree
        tree_x = center_x - 20
        tree_y = ground_y - 30
        draw.rectangle((tree_x, tree_y, tree_x + 8, ground_y), fill=(101, 67, 33))  # Trunk
        # Branches
        draw.line([(tree_x, tree_y), (tree_x - 15, tree_y - 20)], fill=(101, 67, 33), width=3)
        draw.line([(tree_x + 8, tree_y), (tree_x + 23, tree_y - 20)], fill=(101, 67, 33), width=3)
        
        # Draw winter symbol
        draw.text((center_x - 10, center_y - 10), '❄️', font=font, fill=season_color)
        
    elif season == 'spring':
        # Spring scene: Blooming flowers and green grass
        # Draw green ground
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(34, 139, 34))
        
        # Draw flowers
        flower_positions = [(30, ground_y - 10), (80, ground_y - 15), (130, ground_y - 8)]
        for fx, fy in flower_positions:
            draw_flower(draw, fx, fy, season_color)
        
        # Draw blooming tree
        tree_x = center_x - 15
        tree_y = ground_y - 40
        draw.rectangle((tree_x, tree_y, tree_x + 6, ground_y), fill=(101, 67, 33))  # Trunk
        # Blooming branches
        draw.ellipse((tree_x - 20, tree_y - 25, tree_x + 26, tree_y + 5), fill=(255, 192, 203))  # Pink blossoms
        
        # Draw spring symbol
        draw.text((center_x - 10, center_y + 10), '🌸', font=font, fill=season_color)
        
    elif season == 'summer':
        # Summer scene: Bright sun and lush vegetation
        # Draw bright ground
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(50, 205, 50))
        
        # Draw sun
        sun_x = width - 40
        sun_y = 30
        draw.ellipse((sun_x - 15, sun_y - 15, sun_x + 15, sun_y + 15), fill=(255, 255, 0))
        # Sun rays
        for angle in range(0, 360, 45):
            import math
            ray_x = sun_x + int(25 * math.cos(math.radians(angle)))
            ray_y = sun_y + int(25 * math.sin(math.radians(angle)))
            draw.line([(sun_x, sun_y), (ray_x, ray_y)], fill=(255, 255, 0), width=2)
        
        # Draw lush tree
        tree_x = center_x - 20
        tree_y = ground_y - 50
        draw.rectangle((tree_x, tree_y, tree_x + 8, ground_y), fill=(101, 67, 33))  # Trunk
        # Full green canopy
        draw.ellipse((tree_x - 25, tree_y - 30, tree_x + 33, tree_y + 10), fill=(0, 128, 0))
        
        # Draw summer symbol
        draw.text((center_x - 10, center_y - 10), '☀️', font=font, fill=season_color)
        
    elif season == 'fall':
        # Fall scene: Autumn leaves and harvest colors
        # Draw brown/orange ground
        ground_y = height - 40
        draw.rectangle((0, ground_y, width, height), fill=(160, 82, 45))
        
        # Draw falling leaves
        for i in range(6):
            x = (i * 40 + int(progress * 30)) % width
            y = (i * 30 + int(progress * 25)) % (ground_y - 10)
            draw_leaf(draw, x, y, season_color)
        
        # Draw autumn tree
        tree_x = center_x - 20
        tree_y = ground_y - 45
        draw.rectangle((tree_x, tree_y, tree_x + 8, ground_y), fill=(101, 67, 33))  # Trunk
        # Autumn colored canopy
        draw.ellipse((tree_x - 22, tree_y - 28, tree_x + 30, tree_y + 8), fill=(255, 140, 0))
        
        # Draw fall symbol
        draw.text((center_x - 10, center_y + 10), '🍂', font=font, fill=season_color)

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
    draw.ellipse((x-3, y-3, x+3, y+3), fill=(255, 192, 203))  # Pink petals
    draw.ellipse((x-2, y-4, x+2, y+4), fill=(255, 192, 203))
    draw.ellipse((x-4, y-2, x+4, y+2), fill=(255, 192, 203))
    # Center
    draw.ellipse((x-1, y-1, x+1, y+1), fill=(255, 255, 0))

def draw_leaf(draw, x, y, color):
    """Draw a simple autumn leaf"""
    # Simple leaf shape
    draw.ellipse((x-2, y-3, x+2, y+3), fill=color)
    draw.line([(x, y-3), (x, y+3)], fill=(101, 67, 33), width=1)  # Leaf vein

# Interactive mode variables
interactive_mode = False
speed_multiplier = 1.0

print("Seasonal Clock Started!")
print("Button A: Toggle interactive mode")
print("Button B: Change time speed")
print("Both buttons: Reset to real time")

while True:
    # Get current time
    current_time = time.localtime()
    hour = current_time.tm_hour
    minute = current_time.tm_min
    second = current_time.tm_sec
    
    # Check button states
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)
    
    # Handle button interactions
    if a_pressed and b_pressed:
        # Both buttons: Reset to real time
        interactive_mode = False
        speed_multiplier = 1.0
        print("Reset to real time")
    elif a_pressed and not b_pressed:
        # Button A: Toggle interactive mode
        interactive_mode = not interactive_mode
        print(f"Interactive mode: {'ON' if interactive_mode else 'OFF'}")
    elif b_pressed and not a_pressed:
        # Button B: Change speed
        if interactive_mode:
            speed_multiplier = speed_multiplier * 2.0
            if speed_multiplier > 8.0:
                speed_multiplier = 0.5
            print(f"Speed multiplier: {speed_multiplier}x")
    
    # Calculate total seasons passed
    total_seasons = calculate_total_seasons(hour, minute, second)
    
    # Modify time if in interactive mode
    if interactive_mode:
        # Create a modified second based on speed
        modified_second = (second + int(time.time() * speed_multiplier)) % 60
        season = get_season_from_seconds(modified_second)
        progress = get_seasonal_progress(modified_second)
        # For interactive mode, also modify the total seasons calculation
        modified_total_seconds = hour * 3600 + minute * 60 + modified_second
        total_seasons = int(modified_total_seconds / 15)
    else:
        # Use real time
        season = get_season_from_seconds(second)
        progress = get_seasonal_progress(second)
    
    # Draw the seasonal clock
    draw_seasonal_clock(draw, season, progress, total_seasons)
    
    # Display image
    disp.image(image, rotation)
    
    # Small delay for button debouncing and display refresh
    time.sleep(0.1)