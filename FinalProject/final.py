"""
Raspberry Pi 5 QR Scanner + ST7789 Display + Laptop Control
"""

import time
import digitalio
import board
import requests
import cv2
from pyzbar.pyzbar import decode
from PIL import Image, ImageOps
import io

import numpy as np
from sklearn.cluster import KMeans

# --- DISPLAY LIBRARIES ---
from adafruit_rgb_display.rgb import color565
import adafruit_rgb_display.st7789 as st7789

# ==========================================
# 1. HARDWARE SETUP (From your example)
# ==========================================

# Configuration for CS pin (GPIO5/Pin 29)
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None
BAUDRATE = 64000000

# Setup SPI
spi = board.SPI()

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
    # rotation=90 # You might need to uncomment this if the image is sideways
)

# Setup Backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

# ==========================================
# 2. CONFIGURATION
# ==========================================
LAPTOP_IP = "10.56.3.68"  # <--- UPDATE THIS TO YOUR LAPTOP IP
LAPTOP_PORT = "5002"
RESET_TIME = 6000

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def get_youtube_thumbnail(url):
    """
    Downloads YouTube thumbnail and converts it to a PIL Image 
    that fits the ST7789 screen.
    """
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

    # Download High Quality Thumb
    thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    print(f"Downloading art: {thumb_url}")
    
    try:
        resp = requests.get(thumb_url, timeout=2)
        if resp.status_code == 200:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(resp.content))
            
            # Resize and Crop to fit the screen dimensions
            # We use the display.width and display.height so it fits your config
            image = ImageOps.fit(image, (display.width, display.height), method=Image.LANCZOS)
            return image
    except Exception as e:
        print(f"Image download failed: {e}")
    
    return None

def extract_primary_colors(image, num_colors=3):
    """
    Given a PIL Image, returns `num_colors` dominant colors as RGB tuples.
    Uses k-means clustering on all pixels.
    """
    # Convert image to numpy array
    img = image.convert("RGB")
    img_np = np.array(img)

    # Flatten pixel array into (num_pixels, 3)
    pixels = img_np.reshape(-1, 3)

    # KMeans clustering
    kmeans = KMeans(n_clusters=num_colors, n_init="auto")
    kmeans.fit(pixels)

    # Cluster centers are the dominant colors
    colors = kmeans.cluster_centers_.astype(int)

    # Convert to list of (R, G, B)
    return [tuple(color) for color in colors]

# ============================
# LED STRIP SETUP
# ============================
import neopixel_spi as neopixel

NUM_PIXELS = 100
PIXEL_ORDER = neopixel.RGB
BRIGHTNESS = 0.3

spi_led = board.SPI()  # LED strip also uses SPI

pixels = neopixel.NeoPixel_SPI(
    spi_led,
    NUM_PIXELS,
    pixel_order=PIXEL_ORDER,
    brightness=BRIGHTNESS,
    auto_write=False
)


def dominant_color_cycle(colors, wait=0.05, repeat=2):
    """
    Animate the LED strip using a list of dominant (R, G, B) colors.
    - colors: list of RGB tuples [(r,g,b), (r,g,b), ...]
    - wait: delay between LED updates
    - repeat: how many times to sweep the strip per color
    """
    if not colors:
        print("No dominant colors provided.")
        return

    print("Animating dominant colors:", colors)

    for color in colors:
        r, g, b = color
        print(f"Color wipe: {str(color[0]), str(color[1]), str(color[2])}")

        for _ in range(repeat):
            for i in range(NUM_PIXELS):
                pixels[i] = (r, g, b)
                pixels.show()
                time.sleep(wait)

def show_status_color(r, g, b):
    """Fills screen with a solid color"""
    display.fill(color565(r, g, b))

# ==========================================
# 4. MAIN LOOP
# ==========================================

def main():
    print("Starting Webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Webcam not found.")
        return

    print("Scanner Running. Waiting for QR codes...")
    
    # Flash blue to show it's ready
    show_status_color(0, 0, 255)
    time.sleep(0.5)
    show_status_color(0, 0, 0) # Clear to black

    last_played_link = None
    last_seen_time = 0

    try:
        while True:
            # Read frame
            ret, frame = cap.read()
            if not ret:
                break

            qr_codes = decode(frame)

            # Reset logic: If no code seen for RESET_TIME, allow rescanning
            if not qr_codes:
                if last_played_link is not None and (time.time() - last_seen_time > RESET_TIME):
                    print("Resetting... Ready for new code.")
                    last_played_link = None
                    show_status_color(0, 0, 0) # Clear screen to black when reset

            for code in qr_codes:
                link = code.data.decode('utf-8')
                last_seen_time = time.time()

                if link != last_played_link:
                    print("-" * 30)
                    print(f"Found: {link}")
                    
                    # 1. Show YELLOW while processing
                    show_status_color(255, 255, 0)

                    # 2. Send to Laptop
                    try:
                        requests.get(f"http://{LAPTOP_IP}:{LAPTOP_PORT}/play", params={'url': link}, timeout=1)
                        print("Sent to laptop.")
                    except:
                        print("Could not connect to laptop.")

                    # 3. Get Album Art
                    art_image = get_youtube_thumbnail(link)

                    # 4. Display Art
                    if art_image:
                        display.image(art_image)

                        # ---- Extract Colors ----
                        dominant_colors = extract_primary_colors(art_image, num_colors=3)
                        print("Dominant Colors:", dominant_colors)

                        # ---- Run LED animation ----
                        dominant_color_cycle(dominant_colors)

                    else:
                        # If no art found, show RED, then Black
                        show_status_color(255, 0, 0)
                        time.sleep(1)
                        show_status_color(0, 0, 0)

                    last_played_link = link

            # Small sleep to save CPU
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
        backlight.value = False # Turn off screen
    finally:
        cap.release()

if __name__ == '__main__':
    main()
