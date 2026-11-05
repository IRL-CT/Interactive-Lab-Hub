#!/usr/bin/env python3
"""Measure Dinner Dial's three paper-menu positions without guessing servo angles.

Before running: center the bare horn at 1500 us with dinner_dial.py --center,
stop PWM, shut down and disconnect power, then align the pointer with NOODLES.
Never force an energized servo shaft. Reconnect power before calibration.
The first command is 1500 us; its motion from an unknown physical position
cannot be speed-limited. All subsequent moves are ramped at <=300 us/second.
"""

import argparse
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time

import dinner_dial as dial


def ramp_to(servo, current, target, sleep):
    """Move from the last commanded pulse; use the main program's rate limiter."""
    dial.pulse_ticks(current)
    dial.pulse_ticks(target)
    while current != target:
        sleep(dial.POLL_SECONDS)
        current = dial.step_pulse(current, target, dial.POLL_SECONDS)
        servo.write(current)
    return current


def save_config(path, config):
    """Replace only with complete validated JSON; preserve old file on failure."""
    config = dial.validate_calibration(config)
    path = Path(path).expanduser().resolve()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix="." + path.name + ".", suffix=".tmp",
                                         delete=False) as output:
            temporary = Path(output.name)
            json.dump(config, output, indent=2, allow_nan=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run(args, servo_factory=None, read=input, sleep=time.sleep, log=print):
    servo_factory = servo_factory or dial.ServoOutput
    path = Path(args.output).expanduser().resolve()
    log("Dinner Dial paper menu: RICE left / NOODLES center / DUMPLINGS right.")
    log("Mount the pointer at the printed pivot; its tip should reach the target dots.")
    log("First pulse: 1500 us. Keep the pointer clear; never force the powered horn.")
    log("Use + / - for 25 us, > / < for 5 us, then Enter. These are pulse changes,")
    log("not degrees or guaranteed left/right directions. Observe each small move.")
    log("Type ok only when the tip matches the target dot. q or Ctrl+C aborts unsaved.")
    log(f"After all three targets, save writes: {path}")
    if path.exists():
        log("An existing calibration will be replaced only after final save.")
    while True:
        command = read("Pointer clear and centered mechanically? Type start or q: ").strip().lower()
        if command == "q":
            log("Cancelled. Calibration file unchanged.")
            return None
        if command == "start":
            break
        log("Type start to command 1500 us, or q to cancel.")

    config = {"schema_version": 1, "channel": 0, "axis": "y", "neutral": 498}
    deltas = {"+": 25, "-": -25, ">": 5, "<": -5}
    current = 1500
    servo = servo_factory(0)
    save_requested = False
    try:
        servo.start()
        servo.write(current)
        for key, target_name in (("center_us", "NOODLES center dot"),
                                 ("left_us", "RICE left dot"),
                                 ("right_us", "DUMPLINGS right dot")):
            if key != "center_us":
                log("Returning gradually to the confirmed NOODLES position...")
                current = ramp_to(servo, current, config["center_us"], sleep)
            log(f"Align with {target_name}. The printed targets are -40 / 0 / +40 degrees;")
            log("pulse values are measured here, not calculated from those angles.")
            while True:
                command = read(f"{target_name}, {current:g} us [+ - > < ok q]: ").strip().lower()
                if command == "q":
                    log("Cancelled. Calibration file unchanged.")
                    return None
                if command in deltas:
                    target = current + deltas[command]
                    if not 1000 <= target <= 2000:
                        log("Limit reached (1000..2000 us). Do not force a wider range;")
                        log("quit and check the pointer mounting if the dot is unreachable.")
                        continue
                    current = ramp_to(servo, current, target, sleep)
                elif command == "ok":
                    if key == "left_us" and current == config["center_us"]:
                        log("RICE must be a different position from NOODLES. Adjust first.")
                        continue
                    if key == "right_us" and ((current - config["center_us"]) *
                                               (config["left_us"] - config["center_us"]) >= 0):
                        log("DUMPLINGS must be on the opposite side of NOODLES from RICE.")
                        continue
                    config[key] = current
                    log(f"Confirmed {target_name}: {current:g} us.")
                    break
                else:
                    log("Use + / - / > / <, ok when aligned, or q. No automatic sweep.")

        config = dial.validate_calibration(config)
        log("All three positions are confirmed. Review using rice, noodles or dumplings.")
        log("Type save to finish, or q to discard. Keep the mechanism clear during review.")
        review = {"rice": "left_us", "noodles": "center_us", "dumplings": "right_us"}
        while True:
            command = read("Review [rice noodles dumplings save q]: ").strip().lower()
            if command == "q":
                log("Cancelled. Calibration file unchanged.")
                return None
            if command == "save":
                save_requested = True
                break
            if command in review:
                current = ramp_to(servo, current, config[review[command]], sleep)
                log(f"{command.capitalize()}: {current:g} us.")
            else:
                log("Type rice, noodles, dumplings, save or q.")
    finally:
        try:
            servo.close()
        except Exception as error:
            raise RuntimeError("Could not disable servo PWM. Calibration was not saved; "
                               "disconnect servo power if necessary.") from error

    if save_requested:
        save_config(path, config)
        log(f"Saved measured menu positions to {path}. PWM is off.")
        log("Run: python dinner_dial.py --run --audio --config menu_calibration.json")
        return config
    return None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Interactive calibration for the 20 x 13 cm Dinner Dial menu (channel 0).",
        epilog="No guessed side angles: confirm each printed target before saving. Joystick not required.",
    )
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parent / "menu_calibration.json",
                        help="JSON output (default: menu_calibration.json beside this script)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    def stop_on_signal(signum, frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, stop_on_signal)
    try:
        run(args)
    except (KeyboardInterrupt, EOFError):
        print("Stopped. No new calibration saved.")
        return 0
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        signal.signal(signal.SIGTERM, previous)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
