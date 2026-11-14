"""APDS-9960 + SparkFun Servo pHAT DEV-15316 (PCA9685 at 0x40).

One positional servo on channel 0. Confirm power wiring before use.
Pulse widths are commands, not measured angles. Start with no arm attached.
"""

import argparse
import math
import time

# The replacement lid rotates the servo body 90 degrees. On the assembled box,
# 1500 us points the arm forward and 1200 us moves it to the escape side.
# Both endpoints are inside the pulse range already tested on this hardware.
DEFAULT_REST_US = 1500
DEFAULT_ESCAPE_US = 1200


class HandState:
    """Hysteresis plus continuous near/far dwell times."""

    def __init__(self, near, far):
        self.near, self.far = near, far
        self.escaped = False
        self.since = None

    def update(self, value, now):
        condition = value <= self.far if self.escaped else value >= self.near
        dwell = 1.0 if self.escaped else 0.1
        if not condition:
            self.since = None
        elif self.since is None:
            self.since = now
        elif now - self.since >= dwell:
            self.escaped = not self.escaped
            self.since = None
        return self.escaped


def arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['center', 'align', 'sweep', 'run'])
    p.add_argument('--rest-us', type=int, default=DEFAULT_REST_US,
                   help=f'Rest pulse width in us (default: {DEFAULT_REST_US})')
    p.add_argument('--escape-us', type=int, default=DEFAULT_ESCAPE_US,
                   help=f'Escape pulse width in us (default: {DEFAULT_ESCAPE_US})')
    p.add_argument('--near', type=int, help='Measured hand-present threshold, 1-255')
    p.add_argument('--far', type=int, help='Measured release threshold, 0-254')
    args = p.parse_args()
    if not all(1000 <= v <= 2000 for v in [args.rest_us, args.escape_us]):
        p.error('Keep pulse widths within 1000-2000 us; use 1400/1600 for a small test.')
    if args.mode == 'run' and not (
        args.near is not None and args.far is not None
        and 0 <= args.far < args.near <= 255
    ):
        p.error('run requires calibrated --near and --far: 0 <= far < near <= 255')
    return args


def main():
    args = arguments()
    # Import after parsing so --help also works on a computer without hardware.
    import board
    from adafruit_pca9685 import PCA9685

    i2c = board.I2C()
    pca = None
    try:
        pca = PCA9685(i2c, address=0x40)
        pca.frequency = 50
        output = pca.channels[0]

        def write_us(pulse):
            output.duty_cycle = round(pulse * pca.frequency * 65535 / 1_000_000)

        def move(start, end, duration):
            steps = max(1, math.ceil(duration / 0.02))
            for step in range(1, steps + 1):
                fraction = step / steps
                eased = fraction * fraction * (3 - 2 * fraction)
                write_us(start + (end - start) * eased)
                time.sleep(duration / steps)

        # Read the sensor before enabling servo pulses in integrated mode.
        sensor = None
        if args.mode == 'run':
            from adafruit_apds9960.apds9960 import APDS9960
            sensor = APDS9960(i2c)
            sensor.enable_proximity = True
            _ = sensor.proximity

        print('Channel 0 will move. Keep the sweep clear. Ctrl+C disables PWM.')
        print(f'Configured range: REST={args.rest_us}us, ESCAPE={args.escape_us}us.')
        write_us(1500)
        time.sleep(1)
        if args.mode == 'center':
            print('Holding nominal centre. Disconnect servo power before mounting the horn.')
            while True:
                time.sleep(0.1)

        move(1500, args.rest_us, 0.8)
        if args.mode == 'align':
            print(f'Holding REST at {args.rest_us}us for horn alignment.')
            print('Press Ctrl+C, disconnect power, then refit the horn pointing forward.')
            while True:
                time.sleep(0.1)

        if args.mode == 'sweep':
            for _ in range(3):
                move(args.rest_us, args.escape_us, 0.8)
                time.sleep(1)
                move(args.escape_us, args.rest_us, 1.2)
                time.sleep(1)
            return

        state = HandState(args.near, args.far)
        position = float(args.rest_us)
        last = time.monotonic()
        report_at = last
        while True:
            value = sensor.proximity
            now = time.monotonic()
            escaped = state.update(value, now)
            target = args.escape_us if escaped else args.rest_us
            duration = 0.8 if escaped else 1.2
            speed = abs(args.escape_us - args.rest_us) / duration
            # Cap the step after scheduling delays; do not jump across the sweep.
            step = speed * min(now - last, 0.05)
            delta = max(-step, min(step, target - position))
            if delta:
                position += delta
                write_us(position)
            last = now
            if now >= report_at:
                print(f'proximity={value:3d}  state={"ESCAPE" if escaped else "REST"}  pulse={position:.0f}us')
                report_at = now + 0.25
            time.sleep(0.02)
    except KeyboardInterrupt:
        print('\nStopped; PWM disabled, arm may move freely.')
    finally:
        try:
            if pca is not None:
                try:
                    pca.channels[0].duty_cycle = 0
                finally:
                    pca.deinit()
        finally:
            i2c.deinit()


if __name__ == '__main__':
    main()
