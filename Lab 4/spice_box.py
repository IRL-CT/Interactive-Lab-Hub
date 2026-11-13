import time
import board
import qwiic_proximity
import pi_servo_hat
from adafruit_apds9960.apds9960 import APDS9960

SERVO_CH = 0
CLOSED_ANGLE = 0
OPEN_ANGLE = 140
HAND_THRESHOLD = 30      # APDS-9960 (0-255), higher = hand closer
BOTTLE_THRESHOLD = 300   # distance sensor, higher = bottle closer
CLOSE_DELAY = 2.0        # seconds after bottle is back
NO_TAKE_TIMEOUT = 5.0    # close if bottle was never taken

apds = APDS9960(board.I2C())
apds.enable_proximity = True

bottle_sensor = qwiic_proximity.QwiicProximity()
if not bottle_sensor.connected:
    raise RuntimeError("Distance sensor not found. Check the Qwiic cable.")
bottle_sensor.begin()

servo = pi_servo_hat.PiServoHat()
servo.restart()
servo.move_servo_position(SERVO_CH, CLOSED_ANGLE)

def move_to(start, end):
    step = 2 if end > start else -2
    for a in range(start, end, step):
        servo.move_servo_position(SERVO_CH, a)
        time.sleep(0.01)
    servo.move_servo_position(SERVO_CH, end)

is_open = False
bottle_taken = False
opened_at = 0
returned_at = None

def close_lid():
    global is_open, bottle_taken, returned_at
    print("\nClosing lid")
    move_to(OPEN_ANGLE, CLOSED_ANGLE)
    is_open = False
    bottle_taken = False
    returned_at = None

print("Spice box ready.")
try:
    while True:
        hand = apds.proximity
        bottle = bottle_sensor.get_proximity()
        hand_near = hand > HAND_THRESHOLD
        bottle_in = bottle > BOTTLE_THRESHOLD
        now = time.time()
        print(f"hand: {hand:3d}   bottle: {bottle:5d}   ", end="\r")

        if not is_open:
            if hand_near:
                print("\nHand detected -> opening")
                move_to(CLOSED_ANGLE, OPEN_ANGLE)
                is_open = True
                opened_at = now
        else:
            if not bottle_in:
                if not bottle_taken:
                    print("\nBottle taken -> lid stays open")
                bottle_taken = True
                returned_at = None
            elif bottle_taken:
                if returned_at is None:
                    print("\nBottle back")
                    returned_at = now
                if now - returned_at > CLOSE_DELAY and not hand_near:
                    close_lid()
            else:
                if hand_near:
                    opened_at = now
                elif now - opened_at > NO_TAKE_TIMEOUT:
                    close_lid()
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\nStopping.")
    servo.move_servo_position(SERVO_CH, CLOSED_ANGLE)
