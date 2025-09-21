# ============================================================================
# EMOTION CLOCK
# ============================================================================
# Design Intuition: convert a day into a 6x12 mosaic, where each 20-minute block records a simple mood  
# Metaphor: daily diary rendered as pixel art; nighttime locked as sleep until morning  
# Model: canvas = 6 rows (20-minute blocks) × 12 columns (2-hour blocks)  
# Time Layout: from top to bottom, 6 rows represent 2 hours, then move to the next column
# Status：😊 Happy / 😌 Relax / 😡 Angry / 😢 Sad / 😴 Sleep
# ============================================================================

import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# ============================================================================
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

# Turn on the backlight 
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True
# ============================================================================
buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)

# Use internal pull-ups; buttons then read LOW when pressed.
buttonA.switch_to_input(pull=digitalio.Pull.UP)


# ============================================================================
# Setting up mood emojis
# ============================================================================
class MoodClock:
    def __init__(self):
        # Define Emoji
        self.moods = {
            0: {"emoji": "😊", "name": "Happy", "color": (255, 255, 0)},    # Happy - Yellow
            1: {"emoji": "😌", "name": "Relax", "color": (0, 255, 0)},    # Relax - Green
            2: {"emoji": "😡", "name": "Angry", "color": (0, 0, 255)},    # Angry - Blue
            3: {"emoji": "😢", "name": "Sad", "color": (128, 0, 128)},  # Sad - Purple
            4: {"emoji": "😴", "name": "Sleep", "color": (64, 64, 64)}    # Sleep - Grey
        }
        
        #***#
        # Canvas Setting: 6 rows (20-minute blocks) × 12 columns (2-hour blocks)
        self.grid = [[-1 for _ in range(12)] for _ in range(6)]  # -1 = undefined
        
        # Select the current mood
        self.current_mood = 0
        
        # Overlay mode on/off
        self.overlay_mode = False
        self.overlay_start_time = 0
        
        # Botton Following
        self.button_a_pressed = False
        self.last_button_time = 0
	    #***#
        self.last_time_block = self.get_current_time_block()
        self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        
        # Default Mood = Happy
        self.initialize_current_block()
    
    def get_previous_block_state(self):
        # get previous block state
        current_row, current_col = self.get_current_time_block()
        prev_row = current_row -1
        prev_col = current_col
        if prev_row < 0:
            prev_row =5
            prev_col = current_col - 1
        if prev_col < 0:
                return 4
        prev_state = self.grid[prev_row][prev_col]
        return prev_state if prev_state != -1 else 0


    def initialize_current_block(self):
        #initialize current block
        current_row, current_col = self.get_current_time_block()
        if self.grid[current_row][current_col] == -1:
            inherited_state = self.get_previous_block_state()
            self.grid[current_row][current_col] = inherited_state
    
    def check_time_change(self):
        #check time change
        current_row, current_col = self.get_current_time_block()
        last_row, last_col = self.last_time_block
        if current_row != last_row or current_col != last_col:
            self.last_time_block = (current_row, current_col)
            if self.grid[current_row][current_col] == -1:
                inherited_state = self.get_previous_block_state()
                self.grid[current_row][current_col] = inherited_state
                state_name = self.moods.get(inherited_state, {}).get('name', 'Unknown')
    
    def get_current_time_block(self):
        now = time.localtime()
        hr = now.tm_hour
        min = now.tm_min
        block_col = (hr * 60 + min) // 120  # col inx (0-11)
        block_row = ((hr * 60 + min) % 120) // 20  # row idx(0-5)
        return block_row, block_col
    
    
    # Canvas Setup
    def draw_canvas(self, preview_mood=None):
        # Clean Canvas = Draw with Blank
        draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
        # Calculation
        canvas_width = width - 20  # Indentation
        canvas_height = height - 60  # Space for Title and Status Block
        cell_width = canvas_width // 12
        cell_height = canvas_height // 6
        start_x = 10
        start_y = 30
        # Draw Canvas
        for row in range(6):
            for col in range(12):
                x = start_x + col * cell_width
                y = start_y + row * cell_height
                # Retrive Current Time Block
                current_row, current_col = self.get_current_time_block()
                # Determine Cell Color
                mood_idx = self.grid[row][col]
                if mood_idx == -1:
                    # Unfilled Block
                    if (row == current_row and col == current_col):
                        inherited_state = self.get_previous_block_state()
                        if inherited_state in self.moods:
                            color = self.moods[inherited_state]["color"]
                            mood_idx = inherited_state
                        else:
                            color = (32, 32, 32) 
                            mood_idx = -1
                    else:
                        color = (32, 32, 32)
                        mood_idx = -1
                else:
                    if mood_idx in self.moods:
                        color = self.moods[mood_idx]["color"]
                    else:
                        color = (32, 32, 32)
                        mood_idx = -1
                if (row == current_row and col == current_col) and preview_mood is not None:
                    if preview_mood in self.moods:
                        color = self.moods[preview_mood]["color"]
                        mood_idx = preview_mood
                
                # Drawing
                is_current = (row == current_row and col == current_col)
                # Background Color
                draw.rectangle((x, y, x + cell_width - 1, y + cell_height - 1), outline=(64, 64, 64), fill=color)
                # Draw Mood Emoji
                if mood_idx != -1 and mood_idx in self.moods:
                    emoji = self.moods[mood_idx]["emoji"]
                    emoji_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                    emoji_bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
                    emoji_width = emoji_bbox[2] - emoji_bbox[0]
                    emoji_height = emoji_bbox[3] - emoji_bbox[1]
                    emoji_x = x + (cell_width - emoji_width) // 2
                    emoji_y = y + (cell_height - emoji_height) // 2 - 2  
                    draw.text((emoji_x, emoji_y), emoji, font=emoji_font, fill="#000000")
                # Highlighted Current Block
                if is_current:
                    xborder_1 = max(0, x - 1)
                    xborder_2 = min(width - 1, x + cell_width)
                    yborder_1 = max(0, y - 1)
                    yborder_2 = min(height - 1, y + cell_height)
                    draw.rectangle((xborder_1, yborder_1, xborder_2, yborder_2), outline=(255, 255, 255), width=2)
        # Title
        title = "😊 Mood Clock"
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        draw.text((10, 5), title, font=title_font, fill="#FFD700") 

    def draw_overlay(self):
        # Background Canvas
        self.draw_canvas(preview_mood=self.current_mood)

        # Overlay
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 150))
        overlay_draw = ImageDraw.Draw(overlay)

        # Setup
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        date_font = time_font = ImageFont.truetype(font_path, 22)
        gap = 6

        # Draw Date and Time
        import time as _time
        date_text = _time.strftime("%Y-%m-%d")
        time_text = _time.strftime("%H:%M:%S")
        center_y = height // 2
        date_bbox = overlay_draw.textbbox((0, 0), date_text, font=date_font)
        date_w = date_bbox[2] - date_bbox[0]
        date_h = date_bbox[3] - date_bbox[1]
        date_x = (width - date_w) // 2
        date_y = center_y - 56 - date_h
        overlay_draw.text((date_x, date_y), date_text, font=date_font, fill="#FFFFFF")
        time_bbox = overlay_draw.textbbox((0, 0), time_text, font=time_font)
        time_w = time_bbox[2] - time_bbox[0]
        time_h = time_bbox[3] - time_bbox[1]
        time_x = (width - time_w) // 2
        time_y = date_y + date_h + gap
        overlay_draw.text((time_x, time_y), time_text, font=time_font, fill="#FFFFFF")

        # Emoji Rolling Block
        self.draw_scroll_module(overlay_draw)

        # Convert RGBA to RGB
        rgb_overlay = Image.new("RGB", overlay.size, (0, 0, 0))
        rgb_overlay.paste(overlay, mask=overlay.split()[-1])
        return rgb_overlay

    def draw_scroll_module(self, overlay_draw):
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        small_font = ImageFont.truetype(font_path, 20)
        large_font = ImageFont.truetype(font_path, 38)  

        # Ordered Emojis
        total = len(self.moods)
        cur = self.current_mood % total
        display_moods = [ (cur + off) % total for off in (-2, -1, 0, 1, 2) ]

        # Layout Calculation
        module_y = height // 2
        step = 40                     
        row_width = step * 4          
        start_x = (width - row_width) // 2

        # Draw 
        for i, mood_index in enumerate(display_moods):
            x_center = i * step + start_x
            if i == 2:
                is_center = True
                emoji_font = large_font
                fill_color = "#FFFF00"
            else:
                is_center = False
                emoji_font = small_font
                fill_color = "#AAAAAA"

            # Draw Emoji
            emoji = self.moods[mood_index]["emoji"]
            bbox = overlay_draw.textbbox((0, 0), emoji, font=emoji_font)
            emoji_w = bbox[2] - bbox[0]
            emoji_h = bbox[3] - bbox[1]
            draw_x = x_center - emoji_w // 2
            draw_y = module_y - emoji_h // 2
            overlay_draw.text((draw_x, draw_y), emoji, font=emoji_font, fill=fill_color)
            
            # Name below Emoji
            if is_center:
                mood_name = self.moods[mood_index]["name"]
                name_font = ImageFont.truetype(font_path, 14)
                name_bbox = overlay_draw.textbbox((0, 0), mood_name, font=name_font)
                name_w = name_bbox[2] - name_bbox[0]
                name_x = x_center - name_w // 2
                name_y = module_y + emoji_h // 2 + 10  
                overlay_draw.text((name_x, name_y), mood_name, font=name_font, fill="#FFFFFF")

    # Button function (A)
    def handle_button_press(self):
        current_time = time.time()

        # Button A Detection
        press_A = (buttonA.value == False)
        release_A = self.button_a_pressed and not press_A
        self.button_a_pressed = press_A
        
        if release_A:
            if self.overlay_mode: # If overlay mode, switch Mood
                self.current_mood = (self.current_mood + 1) % 5
                self.confirm_mood_selection()
                self.overlay_start_time = current_time # Reset Timer
            else:
                # Enter Overlay Mode
                self.overlay_mode = True
                self.overlay_start_time = current_time
        
        # Check Overlay 
        if (current_time - self.overlay_start_time) > 2.0 and self.overlay_mode == True:
            self.overlay_mode = False
    

    # Mood Selection
    def confirm_mood_selection(self):
        current_row, current_col = self.get_current_time_block()
        self.grid[current_row][current_col] = self.current_mood  
    
    # Reset for new day
    def check_new_day(self):
        now = time.localtime()
        hr = now.tm_hour
        min = now.tm_min
        if hr == 0 and min < 20:
            self.grid = [[-1 for _ in range(12)] for _ in range(6)]
            current_row, current_col = self.get_current_time_block()
            self.grid[current_row][current_col] = 4
    
    def run(self):
        print("Mood Clock Started!")
        print("Button A: Click Button A to select the mood")
        
        while True:
            try:
                self.check_new_day()
                self.check_time_change()
                self.handle_button_press()
                if self.overlay_mode:
                    overlay_image = self.draw_overlay()
                    disp.image(overlay_image, rotation)
                else:
                    self.draw_canvas()
                    disp.image(image, rotation)
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\nMood Clock Off")
                break
            except Exception as e:
                time.sleep(1)

# ============================================================================
# main
# ============================================================================
if __name__ == "__main__":
    clock = MoodClock()
    clock.run()