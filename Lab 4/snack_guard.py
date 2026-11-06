import sys
import time

import pi_servo_hat
import qwiic_oled
import qwiic_proximity

# --- Proximity range that counts as "your snack" ---
# Raw readings from the VCNL4040: bigger number = closer/more stuff in front.
# 1-10  -> one hand: servo opens, "Hi Enjoy Your Snack!"
# >10   -> more than one hand: "THIS IS NOT YOUR SNACK!"
SNACK_MIN = 1
SNACK_MAX = 10

# Readings below this mean nothing is in front of the sensor, so the screen
# is cleared instead of showing the warning.
IDLE_THRESHOLD = 1

# --- Servo ---
SERVO_CH = 0
REST_ANGLE = 0    # starting position
OPEN_ANGLE = 90   # 90 degrees from rest; swap the two values if it turns the wrong way
HOLD_SECONDS = 5
# Speed of the turn: the servo steps 1 degree, then waits this long.
# 0.02 -> 90 degrees in ~1.8 s. Bigger = slower.
STEP_DELAY = 0.02
# Separate speed for coming back down to rest. Bigger = slower.
RETURN_STEP_DELAY = 0.05

def show(oled, lines):
    # print() can't handle "\n" in this library, so place each line manually
    oled.clear(oled.PAGE)
    for i, line in enumerate(lines):
        oled.set_cursor(0, i * 10)
        oled.print(line)
    oled.display()


def main():
    prox = qwiic_proximity.QwiicProximity()
    if not prox.connected:
        print("Proximity sensor not connected. Check the Qwiic cable.", file=sys.stderr)
        return
    prox.begin()

    oled = qwiic_oled.QwiicOledDisplay()
    if not oled.connected:
        print("OLED not connected. Check the Qwiic cable.", file=sys.stderr)
        return
    oled.begin()
    oled.clear(oled.ALL)
    oled.set_font_type(0)  # small font: 21 chars x 3 lines on 128x32

    servo = pi_servo_hat.PiServoHat()
    servo.restart()
    servo.move_servo_position(SERVO_CH, REST_ANGLE)

    angle = REST_ANGLE
    target = REST_ANGLE
    close_at = None  # when the 5 s hold ends, once fully open
    last_screen = None
    last_value = None

    # Each pass: read the sensor, then move the servo at most 1 degree.
    # The sensor is never ignored, so a second hand can close it mid-move.
    while True:
        value = prox.get_proximity()
        if value != last_value:
            print(f"Proximity: {value}")
            last_value = value

        if value > SNACK_MAX:
            # More than one hand: close right away, even while opening/holding
            target = REST_ANGLE
            close_at = None
            screen = "wrong"
        elif value >= SNACK_MIN and target == REST_ANGLE and angle == REST_ANGLE:
            # One hand while closed: start opening
            target = OPEN_ANGLE
            close_at = None
            screen = "snack"
        elif target == OPEN_ANGLE:
            # Still opening or holding; hand leaving doesn't close it early
            screen = "snack"
        elif value < IDLE_THRESHOLD and angle == REST_ANGLE:
            screen = "idle"
        else:
            screen = last_screen

        # Start the 5 s hold once fully open, then close when it runs out
        if target == OPEN_ANGLE and angle == OPEN_ANGLE:
            if close_at is None:
                close_at = time.monotonic() + HOLD_SECONDS
            elif time.monotonic() >= close_at:
                target = REST_ANGLE
                close_at = None

        if screen != last_screen:
            if screen == "snack":
                show(oled, ["Hi Enjoy Your Snack!"])
            elif screen == "wrong":
                show(oled, ["THIS IS NOT", "YOUR SNACK!"])
            else:
                show(oled, [])
            last_screen = screen

        if angle != target:
            angle += 1 if target > angle else -1
            servo.move_servo_position(SERVO_CH, angle)
            time.sleep(STEP_DELAY if target == OPEN_ANGLE else RETURN_STEP_DELAY)
        else:
            time.sleep(STEP_DELAY)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)
