import RPi.GPIO as GPIO
import time

# Use GPIO12 for motor control
MOTOR_PIN = 12

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR_PIN, GPIO.OUT)

# Create PWM at 200 Hz (smooth for motors)
pwm = GPIO.PWM(MOTOR_PIN, 200)
pwm.start(0)   # start at 0% power

try:
    while True:
        # Breath in (soft → strong)
        for duty in range(0, 50, 1):   # 0% to 100%
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.02)

        # Breath out (strong → soft)
        for duty in range(50, -1, -1): # 100% to 0%
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.02)

except KeyboardInterrupt:
    pass

finally:
    pwm.stop()
    GPIO.cleanup()
    print("Motor breathing stopped.")
