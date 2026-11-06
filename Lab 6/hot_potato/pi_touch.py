"""
Viktor's Hot Potato controller: capacitive touch + green Qwiic button + miniPiTFT
==================================================================================

  Touch pad 6  -> aim LEFT      (screen shows who that is)
  Touch pad 8  -> aim FORWARD
  Touch pad 11 -> aim RIGHT
  Green button -> holding the potato: THROW where you aimed
                  potato flying at you: CATCH
                  lobby / game over: START

The button's LED helps too: blinks = catch now, solid = aimed and ready to throw.

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
args = ap.parse_args()

# ---------- sensors ----------
i2c = board.I2C()
touch = adafruit_mpr121.MPR121(i2c)


class GreenButton:
    """SparkFun Qwiic Button (with LED). Falls back to the PiTFT's own buttons if it isn't found.

    The Qwiic button is a little microcontroller on I2C, and the Pi's I2C can drop reads from it,
    so: reads retry, the button's own "has been clicked" latch catches taps we missed, and the LED
    only gets a command when its pattern changes (it blinks by itself in pulse mode).
    """

    STATUS_REG = 0x03          # BUTTON_STATUS: bit2 = is pressed, bit1 = has been clicked

    def __init__(self):
        self.qwiic = None
        self.led_pattern = None
        self.last_down = False
        self.fired_this_press = False
        self.last_fire = 0.0
        self.errors = 0
        try:
            import qwiic_button
            b = qwiic_button.QwiicButton()
            if b.begin():
                self.qwiic = b
                b.LED_off()
                b.clear_event_bits()
                print("[button] green Qwiic button found")
        except Exception as e:
            print(f"[button] Qwiic button library problem: {e}")
        if not self.qwiic:
            import digitalio
            print("[button] Qwiic button NOT found - using the PiTFT buttons instead")
            self.pins = []
            for pin in (board.D23, board.D24):
                p = digitalio.DigitalInOut(pin)
                p.switch_to_input(pull=digitalio.Pull.UP)
                self.pins.append(p)

    def _status(self):
        for _ in range(3):                      # retry flaky I2C reads
            try:
                return self.qwiic._i2c.readByte(self.qwiic.address, self.STATUS_REG)
            except OSError:
                self.errors += 1
                time.sleep(0.002)
        return None

    def poll(self):
        """True exactly once per physical press."""
        now = time.time()
        if self.qwiic:
            status = self._status()
            if status is None:
                return False
            down, clicked = bool(status & 0x04), bool(status & 0x02)
        else:
            down, clicked = any(not p.value for p in self.pins), False

        fire = False
        if down and not self.last_down:          # normal case: we saw it go down
            fire = True
            self.fired_this_press = True
        if clicked:                              # press+release finished on the button itself
            try:
                self.qwiic.clear_event_bits()
            except OSError:
                self.errors += 1
            if not self.fired_this_press:        # it was too quick for us to see it held: count it now
                fire = True
            self.fired_this_press = down
        self.last_down = down
        if fire and now - self.last_fire < 0.12:  # ignore contact bounce
            fire = False
        if fire:
            self.last_fire = now
        return fire

    def led(self, pattern):
        """'off' | 'dim' | 'start' | 'solid' | 'blink'. Only talks to the button on a change."""
        if not self.qwiic or pattern == self.led_pattern:
            return
        self.led_pattern = pattern
        try:
            if pattern == "blink":
                self.qwiic.LED_config(255, 250, 60)   # the button pulses by itself
            elif pattern == "solid":
                self.qwiic.LED_on(255)
            elif pattern == "dim":
                self.qwiic.LED_on(25)
            elif pattern == "start":
                self.qwiic.LED_on(40)
            else:
                self.qwiic.LED_off()
        except OSError:
            self.errors += 1
            self.led_pattern = None                    # try again next loop


button = GreenButton()

# ---------- game ----------
game = PotatoClient(args.name, seat=args.seat, input_name="touch", aim_hint="touch 6 / 8 / 11 to aim")
game.start()

pad_edges = {pad: Edge() for pad in PADS}
last_error_report = time.time()
print("Ready: pads 6 / 8 / 11 aim left / forward / right, green button = throw / catch / start. Ctrl+C to quit.")

try:
    while True:
        touched = touch.touched_pins            # one I2C read for all 12 pads
        for pad, direction in PADS.items():
            if pad_edges[pad](touched[pad]):
                game.aim(direction)

        if button.poll():
            print(f"[button] press  (screen says: {game.mode})")
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

        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nbye!")
finally:
    button.led("off")
    game.stop()
    sys.exit(0)
