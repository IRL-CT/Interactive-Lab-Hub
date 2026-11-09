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
    """SparkFun Qwiic Button (with LED). Falls back to the PiTFT's own buttons if it isn't found."""

    def __init__(self):
        self.qwiic = None
        self.led_level = None
        try:
            import qwiic_button
            b = qwiic_button.QwiicButton()
            if b.begin():
                self.qwiic = b
                b.LED_off()
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

    def is_down(self):
        if self.qwiic:
            try:
                return self.qwiic.is_button_pressed()
            except OSError:
                return False
        return any(not p.value for p in self.pins)   # PiTFT buttons are active-low

    def led(self, level):
        """0 = off, 255 = full. Only talks to the button when the level changes."""
        if not self.qwiic or level == self.led_level:
            return
        self.led_level = level
        try:
            if level:
                self.qwiic.LED_on(level)
            else:
                self.qwiic.LED_off()
        except OSError:
            pass


button = GreenButton()

# ---------- game ----------
game = PotatoClient(args.name, seat=args.seat, input_name="touch", aim_hint="touch 6 / 8 / 11 to aim")
game.start()

pad_edges = {pad: Edge() for pad in PADS}
button_edge = Edge()
print("Ready: pads 6 / 8 / 11 aim left / forward / right, green button = throw / catch / start. Ctrl+C to quit.")

try:
    while True:
        touched = touch.touched_pins            # one I2C read for all 12 pads
        for pad, direction in PADS.items():
            if pad_edges[pad](touched[pad]):
                game.aim(direction)

        if button_edge(button.is_down()):
            game.press()

        # LED cue
        mode, st = game.mode, game.state
        if mode == "incoming" and not st.get("caught"):
            button.led(255 if int(time.time() * 10) % 2 else 0)      # fast blink: CATCH!
        elif mode == "holding":
            button.led(255 if game.aim_dir else 25)                  # solid when aimed
        elif mode in ("lobby", "gameover"):
            button.led(40)                                           # dim: press to start
        else:
            button.led(0)

        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nbye!")
finally:
    button.led(0)
    game.stop()
    sys.exit(0)
