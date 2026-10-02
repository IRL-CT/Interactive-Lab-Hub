import time
import board
import busio
import adafruit_mpr121

# Connect to the Raspberry Pi's I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Connect to the MPR121
mpr121 = adafruit_mpr121.MPR121(i2c)

print()
print("================================")
print("      MPR121 TOUCH TEST")
print("================================")
print("Sensor connected successfully!")
print()
print("Touch any of the 12 electrodes.")
print("Press Ctrl+C to stop.")
print()

# Keep track of the previous state so we only print
# when something changes.
previous = [False] * 12

try:
    while True:
        for i in range(12):
            touched = mpr121[i].value

            # Only print when the touch state changes
            if touched != previous[i]:
                if touched:
                    print(f"Electrode E{i}: TOUCHED")
                else:
                    print(f"Electrode E{i}: released")

                previous[i] = touched

        time.sleep(0.05)

except KeyboardInterrupt:
    print()
    print("Test stopped.")
