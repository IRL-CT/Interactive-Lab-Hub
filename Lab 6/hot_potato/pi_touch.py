"""
Viktor's Hot Potato controller: capacitive touch + green Qwiic button + miniPiTFT
==================================================================================

  Touch pad 6  -> aim LEFT      (screen shows who that is)
  Touch pad 8  -> aim FORWARD   (your last touch stays as your aim)
  Touch pad 11 -> aim RIGHT
  Green button -> holding the potato: THROW where you aimed
                  potato flying at you: CATCH
                  lobby / game over: START

Optional: --led lights the button (blinks = catch now, solid = aimed). Off by default because
LED commands made the Qwiic button miss presses on the Pi.

Run on the Pi (from the Lab 6 folder, venv active):
    sudo systemctl stop piscreen.service
    pip install sparkfun-qwiic-button          # first time only
    python hot_potato/pi_touch.py              # or: --name viktor --seat 1
"""

import argparse
import sys
import time

import board
import adafruit_mpr121

from pi_client import PotatoClient, Edge

PADS = {6: "left", 8: "forward", 11: "right"}

ap = argparse.ArgumentParser()
ap.add_argument("--name", default="viktor")
ap.add_argument("--seat", type=int, default=1, choices=[1, 2, 3, 4])
ap.add_argument("--test", action="store_true", help="just print touches and button presses (no game)")
ap.add_argument("--led", action="store_true", help="also light the button's LED (off by default)")
args = ap.parse_args()

# ---------- sensors ----------
i2c = board.I2C()
touch = adafruit_mpr121.MPR121(i2c)


class GreenButton:
    """SparkFun Qwiic Button, read exactly like David's working IMU script:
    plain is_button_pressed() + Edge, polled ~30x a second, and NO extra writes to the button
    (LED commands and clearing its status bits upset it on the Pi's I2C bus).
    The LED is opt-in:  python hot_potato/pi_touch.py --led
    If the Qwiic button isn't found, the two small PiTFT buttons are used instead."""

    def __init__(self, use_led=False):
        self.qwiic = None
        self.use_led = use_led
        self.led_pattern = None
        self.errors = 0
        self.pins = []
        try:
            self.qwiic = self._find_qwiic_button()
        except Exception as e:
            print(f"[button] Qwiic button library problem: {e}  (pip install sparkfun-qwiic-button)")
        if self.qwiic:
            print(f"[button] green Qwiic button found at address {hex(self.qwiic.address)}")
        else:
            print("[button] !! green Qwiic button NOT found - using the two small PiTFT buttons instead")
            print("[button]    check its cable, then run: sudo i2cdetect -y 1")
            import digitalio
            for pin in (board.D23, board.D24):
                p = digitalio.DigitalInOut(pin)
                p.switch_to_input(pull=digitalio.Pull.UP)
                self.pins.append(p)

    @staticmethod
    def _find_qwiic_button():
        """Default address 0x6F first (like David's), then any other device that answers like a Qwiic Button."""
        import qwiic_button
        b = qwiic_button.QwiicButton()
        if b.begin():
            return b
        try:
            import qwiic_i2c
            found = qwiic_i2c.getI2CDriver().scan()
        except Exception:
            found = []
        print(f"[button] nothing at 0x6f; I2C devices found: {[hex(a) for a in found]}")
        for addr in found:
            if addr in (0x5A, 0x5B, 0x5C, 0x5D, 0x6F):   # MPR121 touch board addresses / already tried
                continue
            try:
                b = qwiic_button.QwiicButton(addr)
                if b.address == addr and b.begin():
                    return b
            except Exception:
                continue
        return None

    def is_down(self):
        if self.qwiic:
            try:
                return self.qwiic.is_button_pressed()
            except OSError:
                self.errors += 1
                return False
        return any(not p.value for p in self.pins)     # PiTFT buttons are active-low

    def led(self, pattern):
        """'off' | 'dim' | 'start' | 'solid' | 'blink' - only with --led, and only on a change."""
        if not (self.use_led and self.qwiic) or pattern == self.led_pattern:
            return
        self.led_pattern = pattern
        levels = {"solid": 255, "dim": 25, "start": 40}
        try:
            if pattern == "blink":
                self.qwiic.LED_config(255, 250, 60)
            elif pattern in levels:
                self.qwiic.LED_on(levels[pattern])
            else:
                self.qwiic.LED_off()
        except OSError:
            self.errors += 1


button = GreenButton(use_led=args.led)
button_edge = Edge()
POLL = 0.03     # seconds between reads (David's working script uses 0.05)

# ---------- hardware test mode:  python hot_potato/pi_touch.py --test ----------
if args.test:
    print("TEST MODE: touch pads and press the green button. Ctrl+C to stop.")
    print(f"  pads used for the game: {', '.join(f'{p}={d}' for p, d in PADS.items())}")
    last = None
    try:
        while True:
            touched = touch.touched_pins
            now_on = [i for i, t in enumerate(touched) if t]
            if now_on != last:
                label = ", ".join(f"{i} ({PADS.get(i, 'not used')})" for i in now_on) or "none"
                print(f"  pads touched: {label}")
                last = now_on
            if button_edge(button.is_down()):
                print("  BUTTON pressed")
            if button.errors:
                print(f"  ({button.errors} I2C read errors from the button)")
                button.errors = 0
            time.sleep(POLL)
    except KeyboardInterrupt:
        button.led("off")
        sys.exit(0)

# ---------- game ----------
game = PotatoClient(args.name, seat=args.seat, input_name="touch", aim_hint="touch 6 / 8 / 11 to aim")
game.start()

other_edges = {pad: Edge() for pad in range(12)}
current_aim = None          # the last pad you touched stays your aim (like the encoder's knob position)
last_error_report = time.time()
print("Ready: pads 6 / 8 / 11 aim left / forward / right, green button = throw / catch / start. Ctrl+C to quit.")

try:
    while True:
        touched = touch.touched_pins            # one I2C read for all 12 pads
        for pad, direction in PADS.items():
            if touched[pad]:
                current_aim = direction
        if current_aim:
            game.aim(current_aim)               # re-applied every loop, so it's always set
        for pad in range(12):                   # helps spot wiring/numbering mix-ups
            if pad not in PADS and other_edges[pad](touched[pad]):
                print(f"[pads] pad {pad} touched - not used (aim pads are {sorted(PADS)})")

        if button_edge(button.is_down()):
            print(f"[button] press  (screen says: {game.mode}, aim: {game.aim_dir}, "
                  f"pads touched now: {[p for p in range(12) if touched[p]] or 'none'})")
            game.press()

        # LED cue
        mode, st = game.mode, game.state
        if mode == "incoming" and not st.get("caught"):
            button.led("blink")                                      # CATCH!
        elif mode == "holding":
            button.led("solid" if game.aim_dir else "dim")           # solid when aimed
        elif mode in ("lobby", "gameover"):
            button.led("start")                                      # press to start
        else:
            button.led("off")

        if button.errors and time.time() - last_error_report > 5:
            print(f"[button] {button.errors} I2C read errors in the last few seconds (loose Qwiic cable?)")
            button.errors = 0
            last_error_report = time.time()

        time.sleep(POLL)
except KeyboardInterrupt:
    print("\nbye!")
finally:
    button.led("off")
    game.stop()
    sys.exit(0)
