 """
 Raspberry Pi 4 Edition
 QR Scanner + ST7789 Display + WS2811 LEDs (GPIO 18) + Laptop Control
 """
 import time
 import digitalio
 import board
 import requests
 import cv2
 import threading
 from pyzbar.pyzbar import decode
 from PIL import Image, ImageOps
 import io
 # --- STANDARD NEOPIXEL LIBRARY (For Pi 4) ---
 # We use the standard 'neopixel' library which uses PWM on GPIO 18
 import neopixel
 # --- DISPLAY LIBRARIES ---
 from adafruit_rgb_display.rgb import color565
 import adafruit_rgb_display.st7789 as st7789
 # ==========================================
 # 1. HARDWARE SETUP
 # ==========================================
 # --- LED STRIP CONFIGURATION ---
 # WIRING: Green Data Wire -> GPIO 18 (Pin 12)
 NUM_PIXELS = 100        
 # COLOR FIX: Changed from RGB to GRB.
 PIXEL_ORDER = neopixel.GRB
 BRIGHTNESS = 0.5        
 # --- DISPLAY CONFIGURATION ---
 # WIRING: Standard SPI (MOSI=19, SCLK=23, CS=24/29, DC=22/25)
 cs_pin = digitalio.DigitalInOut(board.D5)
 dc_pin = digitalio.DigitalInOut(board.D25)
 reset_pin = None
 BAUDRATE = 64000000
 # Setup SPI (For Display ONLY)
 spi = board.SPI()
 # Setup LEDs (Using GPIO 18 PWM)
 try:
     pixels = neopixel.NeoPixel(
         board.D18,
         NUM_PIXELS,
         brightness=BRIGHTNESS,
         auto_write=False,
         pixel_order=PIXEL_ORDER
     )
     print("LED Strip Initialized on GPIO 18.")
 except Exception as e:
     print(f"LED Error: {e}")
     print("Did you run with 'sudo'? PWM LEDs require root privileges.")
     pixels = None
 # Setup Display
 display = st7789.ST7789(
     spi,
     cs=cs_pin,
     dc=dc_pin,
     rst=reset_pin,
     baudrate=BAUDRATE,
     width=135,
     height=240,
     x_offset=53,
     y_offset=40,
     rotation=180 # <--- ADDED ROTATION HERE
 )
 # Setup Backlight
 backlight = digitalio.DigitalInOut(board.D22)
 backlight.switch_to_output(value=True)
 # ==========================================
 # 2. CONFIGURATION
 # ==========================================
 LAPTOP_IP = "10.247.142.213" 
 LAPTOP_PORT = "5001"
 # ==========================================
 # 3. LED ANIMATION THREAD
 # ==========================================
 # We use a global variable to tell the thread what colors to pulse between
 target_colors = [(0,0,0)] # Default to black
 stop_led_thread = False
 def led_animation_loop():
     """
     Background thread that creates a 'Moving Sections' (Marquee) effect.
     """
     global target_colors, stop_led_thread
     active_colors = [(0,0,0)]
     offset = 0
     segment_length = 10  # Length of each color block (5 LEDs)
     while not stop_led_thread:
         if not pixels:
             time.sleep(1)
             continue
         # 1. Update colors if target changed
         if active_colors != target_colors:
             active_colors = list(target_colors)
         # 2. Handle Single Color (Static fill)
         if len(active_colors) <= 1:
             c = active_colors[0] if active_colors else (0,0,0)
             pixels.fill(c)
             pixels.show()
             time.sleep(0.1)
             continue
         # 3. Handle Multi-Color "Moving Sections"
         num_colors = len(active_colors)
         for i in range(NUM_PIXELS):
             # We calculate which color index to use based on the pixel position + offset
             # Dividing by segment_length groups pixels into blocks
             color_idx = ((i + offset) // segment_length) % num_colors
             pixels[i] = active_colors[color_idx]
         pixels.show()
         # Shift the pattern down the strip
         offset += 1
         time.sleep(0.1) # Speed of movement (Lower = Faster)
 # ==========================================
 # 4. HELPER FUNCTIONS
 # ==========================================
 def get_youtube_thumbnail(url):
     video_id = ""
     if "v=" in url:
         try:
             video_id = url.split("v=")[1].split("&")[0]
         except: pass
     elif "youtu.be/" in url:
         try:
             video_id = url.split("youtu.be/")[1].split("?")[0]
         except: pass
     if not video_id:
         return None
     thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
     print(f"Downloading art: {thumb_url}")
     try:
         resp = requests.get(thumb_url, timeout=2)
         if resp.status_code == 200:
             image = Image.open(io.BytesIO(resp.content))
             image = ImageOps.fit(image, (display.width, display.height), method=Image.LANCZOS)
             return image
     except Exception as e:
         print(f"Image download failed: {e}")
     return None
 def set_led_colors(color_list):
     """Updates the global target for the animation thread"""
     global target_colors
     target_colors = color_list
 def show_status_color(r, g, b):
     # 1. Update Screen
     display.fill(color565(r, g, b))
     # 2. Update LEDs (Set as single static color)
     set_led_colors([(r, g, b)])
 def set_leds_from_image(image):
     try:
         # 1. Resize to a small thumbnail (faster processing)
         thumb = image.resize((50, 50))
         # 2. Reduce colors to a palette of 10 dominant shades
         quantized = thumb.quantize(colors=10, method=2)
         palette = quantized.getpalette()
         # 3. Find the TOP 3 most "colorful" (saturated) colors
         scored_colors = []
         # Check the first 8 dominant colors
         for i in range(8):
             if len(palette) < i*3+3: break
             r = palette[i*3]
             g = palette[i*3+1]
             b = palette[i*3+2]
             # Skip if too dark (black) or too bright (white)
             brightness = r + g + b
             if brightness < 40 or brightness > 700:
                 continue
             # Calculate saturation (difference between highest and lowest channel)
             sat = max(r,g,b) - min(r,g,b)
             scored_colors.append((sat, (r,g,b)))
         # Sort by saturation (most vibrant first)
         scored_colors.sort(key=lambda x: x[0], reverse=True)
         # Pick top 3
         top_colors = [c[1] for c in scored_colors[:3]]
         # Fallback if image is B&W or we couldn't find good colors
         if not top_colors:
             top_colors = [(palette[0], palette[1], palette[2])]
         print(f"Cycling between: {top_colors}")
         # Update the animation thread
         set_led_colors(top_colors)
     except Exception as e:
         print(f"Could not calculate colors: {e}")
 # ==========================================
 # 5. MAIN LOOP
 # ==========================================
 def main():
     global stop_led_thread
     # Start LED Animation Thread
     led_thread = threading.Thread(target=led_animation_loop)
     led_thread.daemon = True
     led_thread.start()
     print("Starting Webcam...")
     cap = cv2.VideoCapture(0)
     if not cap.isOpened():
         print("Error: Webcam not found.")
         return
     print("Scanner Running. Waiting for QR codes...")
     # Flash blue
     show_status_color(0, 0, 255)
     time.sleep(0.5)
     show_status_color(0, 0, 0)
     last_played_link = None
     try:
         while True:
             ret, frame = cap.read()
             if not ret:
                 break
             qr_codes = decode(frame)
             for code in qr_codes:
                 link = code.data.decode('utf-8')
                 if link != last_played_link:
                     print("-" * 30)
                     print(f"Found new code: {link}")
                     show_status_color(255, 255, 0) # Yellow loading
                     try:
                         requests.get(f"http://{LAPTOP_IP}:{LAPTOP_PORT}/play", params={'url': link}, timeout=1)
                         print("Sent to laptop.")
                     except:
                         print("Could not connect to laptop.")
                     art_image = get_youtube_thumbnail(link)
                     if art_image:
                         display.image(art_image)
                         set_leds_from_image(art_image) # Extract 3 colors & start cycle
                     else:
                         show_status_color(255, 0, 0)
                         time.sleep(1)
                         show_status_color(0, 0, 0)
                     last_played_link = link
             time.sleep(0.1)
     except KeyboardInterrupt:
         print("\nStopping...")
         stop_led_thread = True # Stop the thread
         led_thread.join()
         backlight.value = False
         if pixels:
             pixels.fill((0,0,0))
             pixels.show()
     finally:
         cap.release()
 if __name__ == '__main__':
     main()
