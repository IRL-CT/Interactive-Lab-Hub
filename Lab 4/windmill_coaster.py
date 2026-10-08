import time
import qwiic_proximity
import pi_servo_hat

# Windmill Coaster
# A cup placed on the coaster is detected by a Qwiic proximity sensor.
# When the cup is present, a servo animates the windmill by sweeping
# back and forth. Remove the cup and the servo returns to its home position.

SERVO_CH = 0
SERVO_MIN = 20
SERVO_MAX = 100
SERVO_HOME = 60

SERVO_STEP = 3
STEP_DELAY = 0.02

# Calibrate this value for your own cup and sensor placement.
# Run qwiic_distance.py first to compare the proximity reading
# with and without a cup on the coaster.
# Higher proximity values mean the object is closer.
CUP_THRESHOLD = 100


# --- Set up proximity sensor ---
proximity_sensor = qwiic_proximity.QwiicProximity()

if not proximity_sensor.connected:
    raise RuntimeError(
        "Qwiic proximity sensor not found. Check the Qwiic connection."
    )

proximity_sensor.begin()


# --- Set up servo ---
servo = pi_servo_hat.PiServoHat()
servo.restart()
servo.move_servo_position(SERVO_CH, SERVO_HOME)

print("Windmill Coaster ready!")
print("Place a cup on the coaster.")
print(f"Current proximity threshold: {CUP_THRESHOLD}")


angle = SERVO_HOME
direction = 1
cup_present = False

try:
    while True:
        proximity = proximity_sensor.get_proximity()
        print(f"Proximity: {proximity}", end="\r")

        if proximity > CUP_THRESHOLD:
            if not cup_present:
                print(f"\nCup detected! Proximity = {proximity}")
                print("Windmill starts.")

            cup_present = True

            angle += SERVO_STEP * direction

            if angle >= SERVO_MAX:
                angle = SERVO_MAX
                direction = -1
            elif angle <= SERVO_MIN:
                angle = SERVO_MIN
                direction = 1

            servo.move_servo_position(SERVO_CH, angle)
            time.sleep(STEP_DELAY)

        else:
            if cup_present:
                print(f"\nCup removed. Proximity = {proximity}")
                print("Windmill stops.")
                servo.move_servo_position(SERVO_CH, SERVO_HOME)
                angle = SERVO_HOME
                direction = 1

            cup_present = False
            time.sleep(0.05)

except KeyboardInterrupt:
    print("\nStopping Windmill Coaster.")
    servo.move_servo_position(SERVO_CH, SERVO_HOME)
