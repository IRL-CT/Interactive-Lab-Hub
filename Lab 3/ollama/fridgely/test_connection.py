import time
import board
import busio
import adafruit_mpr121

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize MPR121
mpr121 = adafruit_mpr121.MPR121(i2c)

print("Touch a pad...")

while True:
    for i in range(12):  # 12 inputs: 0–1
        if mpr121[i].value:
            print(f"Pad {i} touched!")
            time.sleep(0.5)

