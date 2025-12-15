import time
import board
import neopixel
import random

# Initialize NeoPixel ring
NUM_PIXELS = 24  # Adjust based on your ring (12, 16, 24, etc.)
MAX_GLOBAL_BRIGHTNESS = 0.3  # Safe limit for Pi power
pixels = neopixel.NeoPixel(board.D18, NUM_PIXELS, brightness=MAX_GLOBAL_BRIGHTNESS, auto_write=False)

print("NeoPixel Ring Test Script")
print(f"Testing {NUM_PIXELS} pixels on pin D6")
print(f"Max brightness: {int(MAX_GLOBAL_BRIGHTNESS * 100)}%")
print("-" * 40)

def test_all_on(color, duration=2):
    """Light all pixels in one color"""
    print(f"All pixels: {color}")
    pixels.fill(color)
    pixels.show()
    time.sleep(duration)

def test_individual_pixels(color, delay=0.1):
    """Light each pixel individually"""
    print("Testing individual pixels...")
    pixels.fill((0, 0, 0))
    for i in range(NUM_PIXELS):
        pixels[i] = color
        pixels.show()
        time.sleep(delay)
    time.sleep(0.5)

def test_chase(color, delay=0.05, cycles=2):
    """Chase pattern around the ring"""
    print("Chase pattern...")
    for _ in range(cycles):
        for i in range(NUM_PIXELS):
            pixels.fill((0, 0, 0))
            pixels[i] = color
            pixels.show()
            time.sleep(delay)

def test_sparkle(
    duration=5,
    background=(0, 0, 0),
    sparkle_color=(255, 255, 255),
    max_sparkles=4,
    frame_delay=0.05
):
    """
    Sparkle effect:
      - background: base color of the ring
      - sparkle_color: color of the sparkles
      - duration: how long to run (seconds)
      - max_sparkles: how many pixels can sparkle per frame
      - frame_delay: speed of animation (seconds per frame)
    """
    print(f"Sparkle effect for {duration} seconds...")
    end_time = time.time() + duration

    while time.time() < end_time:
        # Start with the background color
        pixels.fill(background)

        # Random number of sparkles this frame
        num_sparkles = random.randint(1, max_sparkles)

        for _ in range(num_sparkles):
            i = random.randrange(NUM_PIXELS)

            # Random brightness for each sparkle (biased towards dim)
            scale = random.random() ** 2  # square it to favor small values
            r = int(sparkle_color[0] * scale)
            g = int(sparkle_color[1] * scale)
            b = int(sparkle_color[2] * scale)

            pixels[i] = (r, g, b)

        pixels.show()
        time.sleep(frame_delay)


def test_breathing(color, duration=5):
    """Breathing effect - fade in and out"""
    print(f"Breathing effect with {color}...")
    steps = 50
    
    # Fade in
    for i in range(steps + 1):
        brightness = i / steps
        r, g, b = color
        adjusted = (int(r * brightness), int(g * brightness), int(b * brightness))
        pixels.fill(adjusted)
        pixels.show()
        time.sleep(duration / (2 * steps))
    
    # Fade out
    for i in range(steps, -1, -1):
        brightness = i / steps
        r, g, b = color
        adjusted = (int(r * brightness), int(g * brightness), int(b * brightness))
        pixels.fill(adjusted)
        pixels.show()
        time.sleep(duration / (2 * steps))

def test_rainbow(delay=0.05):
    """Rainbow color wheel"""
    print("Rainbow color wheel...")
    for j in range(255):
        for i in range(NUM_PIXELS):
            pixel_index = (i * 256 // NUM_PIXELS) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(delay)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions"""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

# Run tests
try:
    print("\n1. Testing basic colors...")
    test_all_on((255, 0, 0), 1)    # Red
    test_all_on((0, 255, 0), 1)    # Green
    test_all_on((0, 0, 255), 1)    # Blue
    test_all_on((255, 255, 255), 1)  # White
    pixels.fill((0, 0, 0))
    pixels.show()
    time.sleep(0.5)
    
    print("\n2. Testing individual pixels...")
    test_individual_pixels((0, 150, 255))
    pixels.fill((0, 0, 0))
    pixels.show()
    time.sleep(0.5)
    
    print("\n3. Testing chase pattern...")
    test_chase((255, 100, 0))
    pixels.fill((0, 0, 0))
    pixels.show()
    time.sleep(0.5)
    
    print("\n4. Testing breathing effect (cool blue)...")
    test_breathing((50, 80, 150))
    time.sleep(0.5)
    
    print("\n5. Testing breathing effect (warm orange)...")
    test_breathing((150, 50, 20))
    time.sleep(0.5)
    
    print("\n6. Testing rainbow...")
    test_rainbow(0.02)
    
    print("\n7. Testing sparkle (cool white on black)...")
    test_sparkle(
        duration=5,                   # run for 5 seconds
        background=(0, 0, 0),         # black background
        sparkle_color=(255, 255, 255),# white sparkles
        max_sparkles=6,               # up to 6 sparkles at once
        frame_delay=0.05              # speed
    )
    time.sleep(0.5)

    print("\n8. Testing sparkle (gold on dark red)...")
    test_sparkle(
        duration=5,
        background=(40, 0, 0),
        sparkle_color=(255, 180, 50),
        max_sparkles=5,
        frame_delay=0.06
    )
    time.sleep(0.5)

    
    print("\n All tests complete!")
    pixels.fill((0, 255, 0))  # Green for success
    pixels.show()
    time.sleep(1)
    
except KeyboardInterrupt:
    print("\n\nTest interrupted by user")
    
finally:
    # Turn off all pixels
    pixels.fill((0, 0, 0))
    pixels.show()
    print("LEDs turned off. Test complete.")