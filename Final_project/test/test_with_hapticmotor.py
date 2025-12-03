import time
import board
import busio
import adafruit_drv2605

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)
drv = adafruit_drv2605.DRV2605(i2c)

print("Strong Constant Vibration Test")

# Pick one strong pattern:
STRONG_EFFECT = 118   # You can try 47, 70, 86, 118

# Put the strong effect in the first slot
drv.sequence[0] = adafruit_drv2605.Effect(STRONG_EFFECT)

# Enable loop mode
drv.loop = True      # This makes the effect repeat indefinitely

# Start vibration
drv.play()
print("Vibration ON (constant strong)")

try:
    while True:
        time.sleep(0.5)  # Keep running
except KeyboardInterrupt:
    print("Stopping...")
    drv.stop()

