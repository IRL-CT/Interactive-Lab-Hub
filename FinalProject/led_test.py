from rpi_ws281x import PixelStrip, Color
import time

# LED strip configuration:
LED_COUNT = 30       # Number of LEDs
LED_PIN = 18         # GPIO pin (must support PWM!)
LED_FREQ_HZ = 800000 # LED signal frequency (800kHz WS2812)
LED_DMA = 10         # DMA channel
LED_BRIGHTNESS = 50  # 0-255
LED_INVERT = False
LED_CHANNEL = 0      # Use channel 0 for GPIO18
LED_STRIP_TYPE = None  # Auto-detect

# Create the strip object
strip = PixelStrip(
    LED_COUNT,
    LED_PIN,
    LED_FREQ_HZ,
    LED_DMA,
    LED_INVERT,
    LED_BRIGHTNESS,
    LED_CHANNEL,
    LED_STRIP_TYPE
)

strip.begin()

def color_wipe(color, wait_ms=50):
    """Wipe color across display."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)

def rainbow_cycle(wait_ms=10):
    for j in range(256):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i * 256 // strip.numPixels() + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)

def wheel(pos):
    """Generate colors across a spectrum."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def main():
    print("Testing LED strip...")
    try:
        while True:
            color_wipe(Color(255, 0, 0))  # Red
            color_wipe(Color(0, 255, 0))  # Green
            color_wipe(Color(0, 0, 255))  # Blue
            rainbow_cycle()
    except KeyboardInterrupt:
        strip.begin()
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        print("LEDs off.")

if __name__ == "__main__":
    main()
