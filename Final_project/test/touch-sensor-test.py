import adafruit_mpr121
import busio
import board
import digitalio
import time
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)

def run_touch_sensor_test():
    print("Touch Sensor Test")
    print("-----------------")
    print("Touch the electrodes to see the output.")
    try:
        while True:
            for i in range(12):
                if mpr121[i].value:
                    print(f"Electrode {i} touched! at {time.monotonic():.2f} seconds")
            # Small delay to avoid flooding the output
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
            
def main():
    run_touch_sensor_test()
    print("Touch Sensor Test Ended")
    
    
if __name__ == "__main__":
    main()
    