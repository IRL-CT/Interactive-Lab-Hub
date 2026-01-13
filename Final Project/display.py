import board
import digitalio
from PIL import Image, ImageDraw, ImageFont, ImageOps 
import adafruit_rgb_display.st7789 as st7789


class Display:
    def __init__(self):
        # ---------------------------
        # SPI Pins
        # ---------------------------
        cs_pin = digitalio.DigitalInOut(board.D5)     # GPIO 5
        dc_pin = digitalio.DigitalInOut(board.D25)    # GPIO 25
        reset_pin = None
        BAUDRATE = 64_000_000

        spi = board.SPI()

        # ---------------------------
        # Landscape resolution
        # PiTFT 240x135 but rotated -> 240 wide, 135 tall
        # ---------------------------
        self.width = 240
        self.height = 135

        self.display = st7789.ST7789(
            spi,
            cs=cs_pin,
            dc=dc_pin,
            rst=reset_pin,
            baudrate=BAUDRATE,
            width=135,
            height=240,
            x_offset=53,
            y_offset=40,
            rotation=90,
        )

        # Backlight
        self.backlight = digitalio.DigitalInOut(board.D22)
        self.backlight.switch_to_output(value=True)

        # Create image buffer
        self.image = Image.new("RGB", (self.width, self.height), "black")
        self.draw = ImageDraw.Draw(self.image)

        # Fonts
        try:
            self.font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/FreeSerifBold.ttf", 18)
            self.font_body = ImageFont.truetype("/usr/share/fonts/truetype/freefont/DejaVuSans-Bold.ttf", 14)
            # NEW: Bigger fonts for microphone display
            self.font_big = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf", 28)
            self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            self.font_title = ImageFont.load_default()
            self.font_body = ImageFont.load_default()
            self.font_big = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()

    # ---------------------------
    # Idle Mode
    # ---------------------------
    def show_idle(self):
        # 1. Clear screen to black
        self.clear((0, 0, 0)) 
        
        # 2. Your text
        text = "Pick up any object to hear its Sound! Then press the top button to see photo"
        
        # 3. Use the existing wrap_text function to split it into lines
        # We allow 220 pixels width (leaving 10px padding on each side)
        lines = self.wrap_text(text, self.font_title, 220)
        
        # 4. Calculate total height of the text block to center it vertically
        total_text_height = 0
        line_spacing = 5
        line_heights = []
        
        for line in lines:
            bbox = self.draw.textbbox((0, 0), line, font=self.font_title)
            h = bbox[3] - bbox[1]
            line_heights.append(h)
            total_text_height += h + line_spacing
        
        # Remove the last extra spacing
        if total_text_height > 0:
            total_text_height -= line_spacing

        # 5. Calculate starting Y position (Vertical Center)
        current_y = (self.height - total_text_height) // 2
        
        # 6. Draw each line centered horizontally
        for i, line in enumerate(lines):
            # Calculate width of this specific line
            bbox = self.draw.textbbox((0, 0), line, font=self.font_title)
            line_w = bbox[2] - bbox[0]
            
            # Center X
            current_x = (self.width - line_w) // 2
            
            # Draw text in dimmed gray
            self.draw.text((current_x, current_y), line, font=self.font_title, fill=(100, 100, 100))
            
            # Move Y down for the next line
            current_y += line_heights[i] + line_spacing
        
        # 7. Push to display
        self.display.image(self.image)

    # ---------------------------
    # Clear screen
    # ---------------------------
    def clear(self, color=(0,0,0)):
        self.draw.rectangle((0, 0, self.width, self.height), fill=color)


    # ---------------------------
    # Auto-wrap text
    # ---------------------------
    def wrap_text(self, text, font, max_width):
        lines = []
        words = text.split()

        current = ""
        for w in words:
            test = current + " " + w if current else w
            bbox = self.draw.textbbox((0,0), test, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = w
        lines.append(current)
        return lines


    # ---------------------------
    # Show Title + Paragraph
    # ---------------------------
    def show_info(self, title, body):
        self.clear()

        # Margins
        x_margin = 10
        y = 5

        # ----- Draw Title -----
        title_bbox = self.draw.textbbox((0,0), title, font=self.font_title)
        title_w = title_bbox[2] - title_bbox[0]

        # Centered title
        title_x = (self.width - title_w) // 2
        self.draw.text((title_x, y), title, font=self.font_title, fill=(255,255,255))
        
        y += title_bbox[3] - title_bbox[1] + 5

        # ----- Draw Body (auto-wrapped) -----
        wrapped = self.wrap_text(body, self.font_body, max_width=self.width - 20)

        for line in wrapped:
            self.draw.text((x_margin, y), line, font=self.font_body, fill=(200,200,200))
            bbox = self.draw.textbbox((0,0), line, font=self.font_body)
            y += bbox[3] - bbox[1] + 3

        self.display.image(self.image)


    # ---------------------------
    # NEW: Microphone Display (Centered + Big)
    # ---------------------------
    def show_mic_message(self, line1, line2=None, color1=(255, 255, 255), color2=(200, 200, 200)):
        """
        Display centered, big text for microphone interactions.
        
        Args:
            line1: Main text (big font, white)
            line2: Secondary text (medium font, gray) - optional
            color1: Color for line1
            color2: Color for line2
        """
        self.clear((0, 0, 0))
        
        line_spacing = 10
        
        # Calculate heights
        bbox1 = self.draw.textbbox((0, 0), line1, font=self.font_big)
        h1 = bbox1[3] - bbox1[1]
        w1 = bbox1[2] - bbox1[0]
        
        if line2:
            # Wrap line2 if needed
            wrapped_line2 = self.wrap_text(line2, self.font_medium, self.width - 20)
            
            # Calculate total height for line2
            h2_total = 0
            line2_heights = []
            line2_widths = []
            for line in wrapped_line2:
                bbox2 = self.draw.textbbox((0, 0), line, font=self.font_medium)
                h = bbox2[3] - bbox2[1]
                w = bbox2[2] - bbox2[0]
                line2_heights.append(h)
                line2_widths.append(w)
                h2_total += h + 5
            h2_total -= 5  # Remove last spacing
            
            total_height = h1 + line_spacing + h2_total
        else:
            total_height = h1
        
        # Calculate starting Y (vertically centered)
        start_y = (self.height - total_height) // 2
        
        # Draw line1 (centered)
        x1 = (self.width - w1) // 2
        self.draw.text((x1, start_y), line1, font=self.font_big, fill=color1)
        
        # Draw line2 if provided
        if line2:
            y2 = start_y + h1 + line_spacing
            for i, line in enumerate(wrapped_line2):
                x2 = (self.width - line2_widths[i]) // 2
                self.draw.text((x2, y2), line, font=self.font_medium, fill=color2)
                y2 += line2_heights[i] + 5
        
        self.display.image(self.image)

    # ---------------------------
    # NEW: Microphone Recording Display (with countdown)
    # ---------------------------
    def show_mic_recording(self, seconds_left):
        """
        Display recording status with big countdown.
        
        Args:
            seconds_left: Number of seconds remaining
        """
        self.clear((0, 0, 0))
        
        # "RECORDING" title
        title = "RECORDING"
        bbox_title = self.draw.textbbox((0, 0), title, font=self.font_medium)
        w_title = bbox_title[2] - bbox_title[0]
        h_title = bbox_title[3] - bbox_title[1]
        
        # Big countdown number
        countdown = str(seconds_left)
        bbox_num = self.draw.textbbox((0, 0), countdown, font=self.font_big)
        w_num = bbox_num[2] - bbox_num[0]
        h_num = bbox_num[3] - bbox_num[1]
        
        # "seconds left" subtitle
        subtitle = "seconds left"
        bbox_sub = self.draw.textbbox((0, 0), subtitle, font=self.font_body)
        w_sub = bbox_sub[2] - bbox_sub[0]
        h_sub = bbox_sub[3] - bbox_sub[1]
        
        # Calculate total height
        spacing = 8
        total_height = h_title + spacing + h_num + spacing + h_sub
        
        # Start Y
        y = (self.height - total_height) // 2
        
        # Draw "RECORDING" in red
        x_title = (self.width - w_title) // 2
        self.draw.text((x_title, y), title, font=self.font_medium, fill=(255, 50, 50))
        y += h_title + spacing
        
        # Draw countdown number in white (big)
        x_num = (self.width - w_num) // 2
        self.draw.text((x_num, y), countdown, font=self.font_big, fill=(255, 255, 255))
        y += h_num + spacing
        
        # Draw "seconds left" in gray
        x_sub = (self.width - w_sub) // 2
        self.draw.text((x_sub, y), subtitle, font=self.font_body, fill=(150, 150, 150))
        
        self.display.image(self.image)

    # ---------------------------
    # NEW: Microphone Countdown Display (3, 2, 1)
    # ---------------------------
    def show_mic_countdown(self, number):
        """
        Display big countdown number (3, 2, 1, GO!).
        
        Args:
            number: The countdown number or "GO!"
        """
        self.clear((0, 0, 0))
        
        text = str(number)
        
        # Use extra big font for countdown
        try:
            font_huge = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf", 60)
        except:
            font_huge = self.font_big
        
        bbox = self.draw.textbbox((0, 0), text, font=font_huge)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        
        # Center on screen
        x = (self.width - w) // 2
        y = (self.height - h) // 2
        
        # Color: yellow for numbers, green for GO!
        if text == "GO!":
            color = (50, 255, 50)  # Green
        else:
            color = (255, 255, 50)  # Yellow
        
        self.draw.text((x, y), text, font=font_huge, fill=color)
        self.display.image(self.image)

    
    # ---------------------------
    # Backlight controls
    # ---------------------------
    def backlight_on(self):
        self.backlight.value = True

    def backlight_off(self):
        self.backlight.value = False
    
    # ---------------------------
    # Show Photo with Title Overlay
    # ---------------------------
    def show_photo(self, image_path, title):
        # 1. Load the image
        try:
            input_image = Image.open(image_path)
        except Exception as e:
            print(f"Error loading image: {e}")
            # If image fails, just show text on black background
            self.show_info(title, "Image file not found.")
            return

        # 2. Smart Resize (Center Crop)
        # This makes the image fill the 240x135 screen without stretching
        bg_image = ImageOps.fit(input_image, (self.width, self.height), method=Image.Resampling.LANCZOS)

        # 3. Paste image onto our canvas
        self.image.paste(bg_image)

        # 4. Add a "Dimming" rectangle at the bottom for text readability
        # (Optional: makes text pop out against the photo)
        overlay = Image.new('RGBA', self.image.size, (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)
        # Draw a semi-transparent black bar at the bottom
        draw_overlay.rectangle((0, 105, 240, 135), fill=(0, 0, 0, 180)) 
        
        # Composite the overlay onto the image
        self.image = Image.alpha_composite(self.image.convert('RGBA'), overlay).convert('RGB')
        
        # Re-initialize draw object because we converted images
        self.draw = ImageDraw.Draw(self.image)

        # 5. Draw the Title Text at the bottom
        # Calculate center position
        bbox = self.draw.textbbox((0, 0), title, font=self.font_title)
        text_w = bbox[2] - bbox[0]
        x = (self.width - text_w) // 2
        
        # Draw text in white
        self.draw.text((x, 110), title, font=self.font_title, fill=(255, 255, 255))

        # 6. Send to screen
        self.display.image(self.image)