"""Read APDS-9960 proximity on a Raspberry Pi. Does not drive a servo."""

import time

import board
from adafruit_apds9960.apds9960 import APDS9960


def main():
    i2c = board.I2C()
    try:
        sensor = APDS9960(i2c)
        sensor.enable_proximity = True
        print("APDS-9960 proximity: 0-255, NOT centimetres. Ctrl+C to stop.")
        print("Compare: no hand / hand approaching / tray in both positions.")
        while True:
            print(f"proximity = {sensor.proximity:3d}", flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        i2c.deinit()


if __name__ == "__main__":
    main()
