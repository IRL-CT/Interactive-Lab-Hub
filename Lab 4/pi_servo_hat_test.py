import pi_servo_hat
import time

# For most 9g micro servos (like SG90, MS18, SER0048), safe range is 0-120 degrees
SERVO_MIN = 0
SERVO_MAX = 120
SERVO_CH = 0  # Channel 0 by default

servo = pi_servo_hat.PiServoHat()
servo.restart()

print(f"Sweeping servo on channel {SERVO_CH} from {SERVO_MIN} to {SERVO_MAX} degrees...")

try:
    while True:
        # Sweep up
        for angle in range(SERVO_MIN, SERVO_MAX + 1, 1):
            servo.move_servo_position(SERVO_CH, angle)
            print(f"Angle: {angle}")
            time.sleep(0.01)
        # Sweep down
        for angle in range(SERVO_MAX, SERVO_MIN - 1, -1):
            servo.move_servo_position(SERVO_CH, angle)
            print(f"Angle: {angle}")
            time.sleep(0.01)
except KeyboardInterrupt:
    print("\nTest stopped.")
    servo.move_servo_position(SERVO_CH, 60)  # Move to center on exit
