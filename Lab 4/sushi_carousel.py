import time
import sys
import qwiic_button
import pi_servo_hat

SERVO_CHANNEL = 0
SERVO_SWING = 180
STEP = 90

button = qwiic_button.QwiicButton()

if not button.begin():
    print("Qwiic Button not found.")
    sys.exit(1)

servo_hat = pi_servo_hat.PiServoHat()
servo_hat.restart()

current_angle = 0

servo_hat.move_servo_position(
    SERVO_CHANNEL,
    current_angle,
    SERVO_SWING
)

print("Starting at 0 degrees")
print("Each button press moves 30 degrees.")

last_button_state = False

try:
    while True:
        pressed = button.is_button_pressed()

        if pressed and not last_button_state:
            current_angle += STEP

            # Don't go beyond the servo's 180° range
            if current_angle > 180:
                current_angle = 0

            print(f"Moving to {current_angle} degrees")

            servo_hat.move_servo_position(
                SERVO_CHANNEL,
                current_angle,
                SERVO_SWING
            )

            time.sleep(0.3)

        last_button_state = pressed
        time.sleep(0.02)

except KeyboardInterrupt:
    print("\nStopping carousel.")
