
"""
David's Hot Potato controller: LSM6DS3 IMU + Qwiic button + miniPiTFT
=====================================================================

  Tilt LEFT   -> aim LEFT
  Tilt RIGHT  -> aim RIGHT
  Tilt UP     -> aim FORWARD
  Tilt DOWN   -> cancel selection

  Qwiic button -> holding the potato: THROW where you aimed
                  potato flying at you: CATCH
                  lobby / game over: START

The IMU detects tilt directions to select a player, while the button
confirms the action. The miniPiTFT displays the game state, selected
target, countdown, and feedback.

Run on the Pi (from the Lab 6 folder, venv active):
    sudo systemctl stop piscreen.service
    python hot_potato/pi_imu.py
"""

import time
import board
import qwiic_button

from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
from pi_client import PotatoClient, Edge


# -----------------------------------
# Configuration
# -----------------------------------

NAME = "david"
SEAT = 4

TILT_THRESHOLD = 4.0
POLL_INTERVAL = 0.05


# -----------------------------------
# Detect tilt direction
# -----------------------------------

def detect_tilt(x, y):
    # Based on the measured IMU orientation

    if x > TILT_THRESHOLD:
        return "left"

    elif x < -TILT_THRESHOLD:
        return "right"

    elif y < -TILT_THRESHOLD:
        return "forward"

    elif y > TILT_THRESHOLD:
        return "down"

    return None


# -----------------------------------
# Main
# -----------------------------------

def main():

    # Initialize IMU
    imu = LSM6DS3(board.I2C())

    # Initialize Qwiic Button
    button = qwiic_button.QwiicButton()

    if not button.begin():
        raise RuntimeError(
            "Qwiic Button not detected. Check I2C wiring."
        )

    # -----------------------------------
    # Calibrate IMU
    # -----------------------------------

    print("Keep your Pi flat while calibrating...")

    samples = []

    for _ in range(20):
        samples.append(imu.acceleration)
        time.sleep(0.05)

    base_x = sum(v[0] for v in samples) / len(samples)
    base_y = sum(v[1] for v in samples) / len(samples)

    print(
        f"Calibration complete: "
        f"X={base_x:.2f}, Y={base_y:.2f}"
    )

    # -----------------------------------
    # Initialize game client
    # -----------------------------------

    game = PotatoClient(
        NAME,
        seat=SEAT,
        input_name="imu",
        aim_hint="Tilt LEFT / UP / RIGHT to aim"
    )

    game.start()

    button_edge = Edge()
    last_direction = None
    last_mode = None

    print("Hot Potato IMU Controller Ready!")
    print("Tilt LEFT / RIGHT / UP to select a player.")
    print("Tilt DOWN to cancel selection.")
    print("Press button to start, catch, or throw.")
    print("Ctrl+C to quit.")

    # -----------------------------------
    # Main loop
    # -----------------------------------

    try:
        while True:

            # Read IMU values
            ax, ay, az = imu.acceleration

            # Relative to calibrated neutral position
            x = ax - base_x
            y = ay - base_y

            direction = detect_tilt(x, y)
            mode = game.mode

            # Reset tracking when game mode changes
            if mode != last_mode:
                last_direction = None
                last_mode = mode

            # -----------------------------------
            # Handle tilt selection
            # -----------------------------------

            if mode == "holding":

                # Only register when direction changes
                if direction != last_direction:

                    if direction in ("left", "right", "forward"):

                        game.aim(direction)

                        print(
                            f"[IMU] Selected: {direction}"
                        )

                    elif direction == "down":

                        game.aim_dir = None
                        game.flash("selection cleared")

                        print(
                            "[IMU] Selection cancelled"
                        )

            # Remember the last detected direction
            last_direction = direction

            # -----------------------------------
            # Handle Qwiic Button
            # -----------------------------------

            if button_edge(button.is_button_pressed()):
                game.press()

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping Hot Potato controller...")

    finally:
        game.stop()


if __name__ == "__main__":
    main()
