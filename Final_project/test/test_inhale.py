import time
import board
import busio
import adafruit_drv2605

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)
drv = adafruit_drv2605.DRV2605(i2c)

# Use real-time playback mode for smooth intensity control
drv.use_ERM()  # Use ERM motor mode
drv.mode = adafruit_drv2605.MODE_REALTIME

print("Smooth Breathing Haptic Pattern")

# Breathing timing (in seconds)
INHALE_DURATION = 5.0
EXHALE_DURATION = 4.0
PAUSE_DURATION = 1.0

# Intensity range (0-127 for realtime mode)
MIN_INTENSITY = 0
MAX_INHALE_INTENSITY = 70  # Strong inhale
MAX_EXHALE_INTENSITY = 30   # Gentler exhale

def smooth_ramp(start, end, duration, steps=50):
    """Smoothly ramp intensity from start to end over duration"""
    for i in range(steps + 1):
        # Calculate current intensity
        progress = i / steps
        intensity = int(start + (end - start) * progress)
        
        # Set the realtime value
        drv.realtime_value = intensity
        time.sleep(duration / steps)

def breathing_cycle():
    """Execute one complete breathing cycle"""
    
    # INHALE - ramp up to strong intensity
    print("Inhale...")
    smooth_ramp(MIN_INTENSITY, MAX_INHALE_INTENSITY, INHALE_DURATION, steps=60)
    
    # EXHALE - ramp down more gently to lower intensity
    print("Exhale...")
    smooth_ramp(MAX_INHALE_INTENSITY, MAX_EXHALE_INTENSITY, EXHALE_DURATION * 0.7, steps=60)
    smooth_ramp(MAX_EXHALE_INTENSITY, MIN_INTENSITY, EXHALE_DURATION * 0.3, steps=30)
    
    # PAUSE - minimal vibration
    print("Pause...")
    drv.realtime_value = 0
    time.sleep(PAUSE_DURATION)

try:
    while True:
        breathing_cycle()
except KeyboardInterrupt:
    print("\nStopping...")
    drv.realtime_value = 0
    drv.mode = adafruit_drv2605.MODE_INTTRIG  # Return to normal mode
    drv.stop()
    print("Breathing pattern stopped.")