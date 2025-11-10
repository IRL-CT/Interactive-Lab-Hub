import board
import neopixel_spi as neopixel
import time

# Try specifying frequency explicitly
spi = board.SPI()
pixels = neopixel.NeoPixel_SPI(
    spi, 
    12, 
    brightness=0.3, 
    auto_write=False, 
    pixel_order=neopixel.GRB,
    frequency=8000000  # Try 8MHz
)

# Test each LED individually
print("Testing each LED...")
for i in range(24):
    pixels.fill((0, 0, 0))
    pixels[i] = (255, 0, 0)  # Red
    pixels.show()
    print(f"LED {i} should be on")
    time.sleep(0.5)

pixels.fill((0, 0, 0))
pixels.show()
print("Done")