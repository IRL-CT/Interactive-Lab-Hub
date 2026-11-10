#!/usr/bin/env python3
"""Dinner Dial: one-step joystick selection, servo pointer, and optional speech."""

import argparse
import json
import math
from pathlib import Path
import shutil
import signal
import statistics
import subprocess
import sys
import time
import wave


FOODS = {-1: "Rice", 0: "Noodles", 1: "Dumplings"}
POLL_SECONDS = 0.02


def validate_calibration(config):
    """Reject incomplete, ambiguous or unsafe calibration before opening hardware."""
    fields = {"schema_version", "channel", "axis", "neutral", "left_us", "center_us", "right_us"}
    if not isinstance(config, dict) or set(config) != fields:
        raise ValueError("Calibration must contain exactly: " + ", ".join(sorted(fields)))
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("Unsupported calibration schema_version; expected 1.")
    if type(config["channel"]) is not int or not 0 <= config["channel"] <= 15:
        raise ValueError("Calibration channel must be an integer from 0 to 15.")
    if config["axis"] not in ("x", "y"):
        raise ValueError("Calibration axis must be x or y.")
    for field in ("neutral", "left_us", "center_us", "right_us"):
        if type(config[field]) not in (int, float) or not math.isfinite(config[field]):
            raise ValueError(f"Calibration {field} must be a finite number.")
    if not 200 <= config["neutral"] <= 823:
        raise ValueError("Calibration neutral must be between 200 and 823.")
    for field in ("left_us", "center_us", "right_us"):
        pulse_ticks(config[field])
    if not min(config["left_us"], config["right_us"]) < config["center_us"] < max(config["left_us"], config["right_us"]):
        raise ValueError("Calibration center pulse must lie strictly between left and right pulses.")
    return dict(config)


def load_calibration(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate calibration key: {key}")
            result[key] = value
        return result

    with Path(path).expanduser().open(encoding="utf-8") as source:
        config = json.load(source, object_pairs_hook=unique_keys)
    return validate_calibration(config)


class Selector:
    """One menu step per tilt; a stable neutral reading rearms the next step."""

    def __init__(self, neutral, invert=False, debounce=0.12):
        self.neutral = neutral
        self.invert = invert
        self.debounce = debounce
        self.state = 0
        self.pending = None
        self.since = 0.0
        self.armed = False

    def update(self, value, now):
        if not math.isfinite(value) or not 0 <= value <= 1023:
            raise ValueError("Joystick reading must be between 0 and 1023.")
        delta = (value - self.neutral) * (-1 if self.invert else 1)
        if delta <= -160:
            candidate = -1
        elif delta >= 160:
            candidate = 1
        elif abs(delta) <= 100:
            candidate = 0
        else:
            candidate = None
        if candidate != self.pending:
            self.pending, self.since = candidate, now
        if candidate is not None and now - self.since >= self.debounce:
            if candidate == 0:
                self.armed = True
            elif self.armed:
                self.state = max(-1, min(1, self.state + candidate))
                self.armed = False
        return self.state


class AudioPlayer:
    """Play the latest selected food without blocking the hardware polling loop."""

    def __init__(self, audio_dir, device, popen=None, which=None, clock=None):
        self.files = {state: Path(audio_dir).expanduser().resolve() / (food.lower() + '.wav')
                      for state, food in FOODS.items()}
        self.device = device
        self.popen = popen or subprocess.Popen
        self.which = which or shutil.which
        self.clock = clock or time.monotonic
        self.executable = None
        self.process = None
        self.pending = None
        self.stopping_since = None
        self.killed = False
        self.ready = False

    def start(self):
        self.executable = self.which('aplay')
        if not self.executable:
            raise RuntimeError('aplay was not found. Install alsa-utils before enabling audio.')
        for path in self.files.values():
            try:
                with wave.open(str(path), 'rb') as source:
                    frames = source.getnframes()
                    expected = frames * source.getnchannels() * source.getsampwidth()
                    if frames <= 0 or len(source.readframes(frames)) != expected:
                        raise ValueError('WAV is empty or truncated')
            except (OSError, EOFError, wave.Error, ValueError) as error:
                raise RuntimeError(f'Cannot read audio file {path}: {error}') from error
        self.ready = True

    def request(self, state):
        if not self.ready:
            raise RuntimeError('Audio has not been initialized.')
        if state not in self.files:
            raise ValueError('Unknown food selection.')
        self.pending = state
        self.poll()

    def poll(self):
        if self.process is not None:
            result = self.process.poll()
            if result is None:
                if self.pending is not None and self.stopping_since is None:
                    self.process.terminate()
                    self.stopping_since = self.clock()
                elif self.stopping_since is not None:
                    elapsed = self.clock() - self.stopping_since
                    if elapsed >= 2:
                        raise RuntimeError('Previous audio process did not stop.')
                    if elapsed >= 1 and not self.killed:
                        self.process.kill()
                        self.killed = True
                return
            interrupted = self.stopping_since is not None
            self.process = None
            self.stopping_since = None
            self.killed = False
            if result != 0 and not interrupted:
                raise RuntimeError(f'aplay exited with code {result}. Check the USB speaker.')
        if self.ready and self.pending is not None:
            state, self.pending = self.pending, None
            self.process = self.popen(
                [self.executable, '-q', '-D', self.device, str(self.files[state])],
                stdin=subprocess.DEVNULL, start_new_session=True,
            )

    def close(self):
        self.ready = False
        self.pending = None
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=1)
            self.process = None
        self.stopping_since = None
        self.killed = False


def pulse_ticks(value):
    if not math.isfinite(value) or not 900 <= value <= 2000:
        raise ValueError("Pulse width must be finite and within 900..2000 us.")
    return round(value * 50 * 4096 / 1_000_000)


def step_pulse(current, target, dt):
    limit = 300 * min(max(dt, 0), 0.1)
    return current + max(-limit, min(limit, target - current))


def neutral_from_samples(samples):
    if not samples or any(not math.isfinite(v) or not 0 <= v <= 1023 for v in samples):
        raise ValueError("Invalid joystick calibration samples.")
    neutral = statistics.median(samples)
    if max(samples) - min(samples) > 60 or not 200 <= neutral <= 823:
        raise ValueError("Release the joystick and keep it still, then start again.")
    return neutral


class ServoOutput:
    """One PCA9685 channel at nominal 50 Hz; pulse widths are microseconds."""

    def __init__(self, channel, bus=None, hat_factory=None):
        if not 0 <= channel <= 15:
            raise ValueError("Servo channel must be between 0 and 15.")
        self.channel = channel
        self.bus = bus
        self.hat_factory = hat_factory
        self.hat = None
        self.active = False
        self.last_ticks = None

    def start(self):
        if self.bus is None:
            import qwiic_i2c
            self.bus = qwiic_i2c.getI2CDriver()
        if self.bus is None or not self.bus.isDeviceConnected(0x40):
            raise RuntimeError("Pi Servo pHAT not found at 0x40. Use --preview to test the joystick.")

        # Mark active before initialization so even a partial failure is cleaned up.
        self.active = True
        self.bus.writeByte(0x40, 0x09 + 4 * self.channel, 0x10)
        if self.hat_factory is None:
            import pi_servo_hat
            self.hat_factory = pi_servo_hat.PiServoHat
        # SparkFun's constructor sets 50 Hz. Do not call restart(): it broadcasts reset.
        self.hat = self.hat_factory()
        self.hat.PCA9685.set_invrt_bit(0)
        self.hat.PCA9685.set_outdrv_bit(1)
        self.hat.PCA9685.set_och_bit(0)
        self.hat.wake()

    def write(self, pulse):
        if not self.active or self.hat is None:
            raise RuntimeError("Servo output has not been started.")
        ticks = pulse_ticks(pulse)
        if ticks == self.last_ticks:
            return
        # on_off=1 selects ON; on_off=0 selects OFF in SparkFun's API.
        if not self.hat.PCA9685.set_channel_word(self.channel, 1, 0):
            raise RuntimeError("Could not write the servo ON count.")
        if not self.hat.PCA9685.set_channel_word(self.channel, 0, ticks):
            raise RuntimeError("Could not write the servo OFF count.")
        self.last_ticks = ticks

    def close(self):
        if self.active:
            # LEDn_OFF_H bit 4 is FULL_OFF. The library's word API rejects 4096.
            self.bus.writeByte(0x40, 0x09 + 4 * self.channel, 0x10)
            self.active = False
            self.last_ticks = None


def connect_joystick():
    import qwiic_joystick
    joystick = qwiic_joystick.QwiicJoystick()
    if not joystick.begin():
        raise RuntimeError("Qwiic Joystick not found at its default address 0x20.")
    return joystick


def read_axes(joystick):
    values = (joystick.horizontal, joystick.vertical)
    if any(not math.isfinite(value) or not 0 <= value <= 1023 for value in values):
        raise ValueError("Invalid joystick reading; stopping rather than moving the pointer.")
    return values


def run(args, joystick_factory=None, servo_factory=None, sleep=None, clock=None, log=print):
    joystick_factory = joystick_factory or connect_joystick
    servo_factory = servo_factory or ServoOutput
    sleep = sleep or time.sleep
    clock = clock or time.monotonic
    servo = None
    audio = None
    try:
        if args.mode == "center":
            servo = servo_factory(args.channel)
            servo.start()
            servo.write(args.center_us)
            log(f"CENTER: channel {args.channel}, {args.center_us:g} us. Ctrl+C to stop PWM.")
            while True:
                sleep(POLL_SECONDS)

        if args.audio:
            audio = AudioPlayer(args.audio_dir, args.audio_device)
            audio.start()
        joystick = joystick_factory()
        axis_index = 0 if args.axis == "x" else 1
        neutral = args.neutral
        if neutral is None:
            log("Release the joystick and keep it still for 1 second...")
            samples = []
            for _ in range(50):
                samples.append(read_axes(joystick)[axis_index])
                sleep(POLL_SECONDS)
            neutral = neutral_from_samples(samples)
        selector = Selector(neutral, invert=args.invert)
        pulses = {-1: args.left_us, 0: args.center_us, 1: args.right_us}
        current = args.center_us
        if args.mode == "run":
            servo = servo_factory(args.channel)
            servo.start()
            servo.write(current)

        log(f"{args.mode.upper()}: axis={args.axis}, neutral={neutral:g}, invert={args.invert}.")
        log("Rice <-> Noodles <-> Dumplings. Tilt once to step; release to rearm.")
        log("Release keeps the selection. Start with the stick released. Ctrl+C to exit.")
        if audio is not None:
            log("Audio: announce each changed choice; a newer choice interrupts the previous phrase.")
        if servo is None:
            log("Joystick preview only; no servo commands are sent.")
        else:
            log(f"Channel {args.channel}: left={args.left_us:g}, center={args.center_us:g}, "
                f"right={args.right_us:g} us. Physical positions need calibration.")
        last_time = clock()
        last_print = float("-inf")
        last_state = None
        announced_state = 0
        while True:
            x, y = read_axes(joystick)
            now = clock()
            state = selector.update((x, y)[axis_index], now)
            if servo is not None:
                current = step_pulse(current, pulses[state], now - last_time)
                servo.write(current)
            if audio is not None:
                if state != announced_state:
                    audio.request(state)
                    announced_state = state
                audio.poll()
            if state != last_state or now - last_print >= 0.5:
                detail = f" | command={current:.0f} us" if servo is not None else ""
                log(f"X={x:4.0f} Y={y:4.0f} | {FOODS[state]}{detail}")
                last_state, last_print = state, now
            last_time = now
            sleep(POLL_SECONDS)
    finally:
        original = sys.exc_info()[1]
        cleanup_errors = []
        if servo is not None:
            try:
                servo.close()
            except Exception as error:
                cleanup_errors.append((
                    "Could not disable servo PWM over I2C. Stop using the mechanism and "
                    "disconnect its power if necessary.", error))
        if audio is not None:
            try:
                audio.close()
            except Exception as error:
                cleanup_errors.append(('Could not stop audio playback.', error))
        if cleanup_errors:
            context = f" Original error: {original!r}." if original is not None else ""
            raise RuntimeError(' '.join(message for message, _ in cleanup_errors) + context
                               ) from cleanup_errors[0][1]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Dinner Dial: tilt once to step, release to keep the food; optional servo and speech.",
        epilog="Default pulses give a small test movement, not calibrated menu positions.",
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--preview", dest="mode", action="store_const", const="preview",
                       help="read joystick only (default)")
    modes.add_argument("--run", dest="mode", action="store_const", const="run",
                       help="read joystick and move servo")
    modes.add_argument("--center", dest="mode", action="store_const", const="center",
                       help="hold servo at center pulse; joystick not required")
    parser.set_defaults(mode="preview")
    parser.add_argument("--config", type=Path,
                        help="load measured menu calibration JSON; explicit CLI values override it")
    parser.add_argument("--axis", choices=("x", "y"), help="joystick axis (default without config: x)")
    parser.add_argument("--invert", action="store_true", help="reverse joystick left/right mapping")
    parser.add_argument("--neutral", type=float, help="fixed joystick center; otherwise measure on startup")
    parser.add_argument("--channel", type=int, choices=range(16), help="servo channel (default without config: 0)")
    parser.add_argument("--left-us", type=float, help="Rice pulse, in us (default without config: 1450)")
    parser.add_argument("--center-us", type=float, help="Noodles pulse, in us (default without config: 1500)")
    parser.add_argument("--right-us", type=float, help="Dumplings pulse, in us (default without config: 1550)")
    parser.add_argument("--audio", action="store_true", help="announce each changed food using saved WAVs")
    parser.add_argument("--audio-dir", type=Path, default=Path(__file__).resolve().parent / 'audio',
                        help="directory containing rice.wav, noodles.wav, dumplings.wav (default: beside script)")
    parser.add_argument("--audio-device", default="plughw:CARD=UACDemoV10,DEV=0",
                        help="ALSA playback device (default: USB UACDemoV10)")
    args = parser.parse_args(argv)
    defaults = {"axis": "x", "neutral": None, "channel": 0,
                "left_us": 1450, "center_us": 1500, "right_us": 1550}
    if args.config is not None:
        try:
            defaults.update(load_calibration(args.config))
        except (OSError, ValueError, TypeError) as error:
            parser.error(f"Cannot load calibration {args.config}: {error}")
    for key in ("axis", "neutral", "channel", "left_us", "center_us", "right_us"):
        if getattr(args, key) is None:
            setattr(args, key, defaults[key])
    if args.mode == 'center' and args.audio:
        parser.error('--audio is for --preview or --run, not --center.')
    if args.neutral is not None and (not math.isfinite(args.neutral) or not 200 <= args.neutral <= 823):
        parser.error("--neutral must be finite and between 200 and 823.")
    try:
        pulse_ticks(args.center_us)
        if args.mode != "center":
            pulse_ticks(args.left_us)
            pulse_ticks(args.right_us)
            if not min(args.left_us, args.right_us) < args.center_us < max(args.left_us, args.right_us):
                parser.error("Center pulse must lie strictly between left and right pulses.")
    except ValueError as error:
        parser.error(str(error))
    return args


def main(argv=None):
    args = parse_args(argv)

    def stop_on_signal(signum, frame):
        raise KeyboardInterrupt

    previous_handler = signal.signal(signal.SIGTERM, stop_on_signal)
    try:
        run(args)
    except KeyboardInterrupt:
        print("Stopped.")
        return 0
    except ModuleNotFoundError as error:
        print(f"Missing Python module: {error.name}. Activate the Lab 4 .venv and check its libraries.",
              file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
