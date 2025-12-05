import adafruit_mpr121
import busio
import board
import time
import neopixel
import RPi.GPIO as GPIO

# --- NeoPixel Setup ---
PIXEL_PIN = board.D18
NUM_PIXELS = 24
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=0.3, auto_write=False)

# --- MPR121 Touch Sensor ---
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)

# --- FSR Pressure Sensor ---
FSR_PIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(FSR_PIN, GPIO.IN)

# --- Vibration Motor ---
MOTOR_PIN = 12
GPIO.setup(MOTOR_PIN, GPIO.OUT)

print("Simple Plush Ready!")
print("Touch pad 0 = LED on")
print("Press FSR = Vibration on")
print("Ctrl+C to exit")

try:
    while True:
        # Check touch pad 0
        if mpr121[0].value:
            pixels.fill((255, 100, 50))  # Warm orange
            pixels.show()
        else:
            pixels.fill((0, 0, 0))  # Off
            pixels.show()
        
        # Check pressure sensor
        if GPIO.input(FSR_PIN):
            GPIO.output(MOTOR_PIN, GPIO.HIGH)  # Vibration on
        else:
            GPIO.output(MOTOR_PIN, GPIO.LOW)   # Vibration off
        
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    pixels.fill((0, 0, 0))
    pixels.show()
    GPIO.cleanup()
    print("Done!")