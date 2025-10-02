# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import pi_servo_hat
import time
import board
from adafruit_apds9960.apds9960 import APDS9960

# Set up servo: For most 9g micro servos (like SG90, MS18, SER0048), safe range is 0-120 degrees
SERVO_MIN = 0
SERVO_MAX = 90
SERVO_CH = 0  # Channel 0 by default

servo = pi_servo_hat.PiServoHat()
servo.restart()

# Set up proximity sensor
i2c = board.I2C()
apds = APDS9960(i2c)

apds.enable_proximity = True

print(f"Sweeping servo on channel {SERVO_CH} from {SERVO_MIN} to {SERVO_MAX} degrees...")

shake_keys = True

try:
    while True:
        if (shake_keys):
            # Sweep up
            for angle in range(SERVO_MIN, SERVO_MAX + 1, 1):
                servo.move_servo_position(SERVO_CH, angle)
                time.sleep(0.001)
            # Sweep down
            for angle in range(SERVO_MAX, SERVO_MIN - 1, -1):
                servo.move_servo_position(SERVO_CH, angle)
                time.sleep(0.001)

        if (apds.proximity > 5):
            shake_keys = False
            servo.move_servo_position(SERVO_CH, 0)
        else:
            shake_keys = True
        
        print(apds.proximity)

except KeyboardInterrupt:
    print("\nTest stopped.")
    servo.move_servo_position(SERVO_CH, 60)  # Move to center on exit

