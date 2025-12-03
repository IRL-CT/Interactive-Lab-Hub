import time
import board
import busio
import adafruit_drv2605
import neopixel

# Initialize I2C for haptic driver
i2c = busio.I2C(board.SCL, board.SDA)
drv = adafruit_drv2605.DRV2605(i2c)

# Initialize NeoPixel ring (adjust pin and number of pixels as needed)
# Common pins: board.D6, board.D10, board.D12
NUM_PIXELS = 12  # Adjust based on your ring (12, 16, 24, etc.)
# Set max brightness to 0.3 (30%) to limit current draw from Pi
# Each NeoPixel can draw ~60mA at full white; 12 pixels = 720mA max
# At 30% brightness, max draw is ~216mA, safely within Pi GPIO limits
MAX_GLOBAL_BRIGHTNESS = 0.3
pixels = neopixel.NeoPixel(board.D6, NUM_PIXELS, brightness=MAX_GLOBAL_BRIGHTNESS, auto_write=False)

# Use real-time playback mode for smooth intensity control
drv.use_ERM()  # Use ERM motor mode
drv.mode = adafruit_drv2605.MODE_REALTIME

print("Smooth Breathing Haptic + NeoPixel Pattern")

# Breathing timing (in seconds)
INHALE_DURATION = 5.0
EXHALE_DURATION = 4.0
PAUSE_DURATION = 1.0

# Haptic intensity range (0-127 for realtime mode)
MIN_HAPTIC = 0
MAX_INHALE_HAPTIC = 30  # Strong inhale
MAX_EXHALE_HAPTIC = 20  # Gentler exhale

# LED color and brightness
# You can change these colors to match your breathing theme
# Using moderate RGB values to further reduce current draw
INHALE_COLOR = (50, 80, 150)    # Cool blue for inhale (reduced intensity)
EXHALE_COLOR = (150, 50, 20)    # Warm orange for exhale (reduced intensity)
MIN_BRIGHTNESS = 0.0
MAX_BRIGHTNESS = 1.0  # This is relative to MAX_GLOBAL_BRIGHTNESS (30%)

def set_ring_color(color, brightness):
    """Set all pixels to a color with given brightness"""
    r, g, b = color
    adjusted_color = (int(r * brightness), int(g * brightness), int(b * brightness))
    pixels.fill(adjusted_color)
    pixels.show()

def smooth_ramp(start_haptic, end_haptic, start_color, end_color, start_brightness, end_brightness, duration, steps=50):
    """Smoothly ramp both haptic and LED intensity from start to end over duration"""
    for i in range(steps + 1):
        # Calculate current intensity
        progress = i / steps
        haptic_intensity = int(start_haptic + (end_haptic - start_haptic) * progress)
        brightness = start_brightness + (end_brightness - start_brightness) * progress
        
        # Interpolate color
        r = int(start_color[0] + (end_color[0] - start_color[0]) * progress)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * progress)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * progress)
        current_color = (r, g, b)
        
        # Set the haptic realtime value
        drv.realtime_value = haptic_intensity
        
        # Set the NeoPixel ring
        set_ring_color(current_color, brightness)
        
        time.sleep(duration / steps)

def breathing_cycle():
    """Execute one complete breathing cycle"""
    
    # INHALE - ramp up to strong intensity with cool blue
    print("Inhale...")
    smooth_ramp(
        MIN_HAPTIC, MAX_INHALE_HAPTIC,
        (0, 0, 0), INHALE_COLOR,
        MIN_BRIGHTNESS, MAX_BRIGHTNESS,
        INHALE_DURATION, steps=60
    )
    
    # EXHALE - ramp down more gently with warm color transition
    print("Exhale...")
    smooth_ramp(
        MAX_INHALE_HAPTIC, MAX_EXHALE_HAPTIC,
        INHALE_COLOR, EXHALE_COLOR,
        MAX_BRIGHTNESS, MAX_BRIGHTNESS * 0.6,
        EXHALE_DURATION * 0.7, steps=60
    )
    smooth_ramp(
        MAX_EXHALE_HAPTIC, MIN_HAPTIC,
        EXHALE_COLOR, (0, 0, 0),
        MAX_BRIGHTNESS * 0.6, MIN_BRIGHTNESS,
        EXHALE_DURATION * 0.3, steps=30
    )
    
    # PAUSE - minimal vibration and no light
    print("Pause...")
    drv.realtime_value = 0
    set_ring_color((0, 0, 0), 0)
    time.sleep(PAUSE_DURATION)

try:
    while True:
        breathing_cycle()
except KeyboardInterrupt:
    print("\nStopping...")
    drv.realtime_value = 0
    drv.mode = adafruit_drv2605.MODE_INTTRIG  # Return to normal mode
    drv.stop()
    pixels.fill((0, 0, 0))
    pixels.show()
    print("Breathing pattern stopped.")