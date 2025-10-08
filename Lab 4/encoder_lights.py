import time
import board
from adafruit_seesaw import seesaw, rotaryio, digitalio
from adafruit_mcp230xx.mcp23017 import MCP23017

i2c = board.I2C()

encoder_ss = seesaw.Seesaw(i2c, addr=0x36)
encoder_product = (encoder_ss.get_version() >> 16) & 0xFFFF
print(f"Found encoder product {encoder_product}")
if encoder_product != 4991:
    print("Warning: wrong firmware? Expected 4991")

encoder_ss.pin_mode(24, encoder_ss.INPUT_PULLUP)
button = digitalio.DigitalIO(encoder_ss, 24)
encoder = rotaryio.IncrementalEncoder(encoder_ss)

gpio = MCP23017(i2c, address=0x27)

led_pins = [gpio.get_pin(i) for i in range(4)]
for led in led_pins:
    led.switch_to_output(value=False)

last_position = None
button_held = False

print("Ready! Rotate encoder to change LEDs.\n")

while True:
    position = -encoder.position
    position_mod = position % 4

    if position != last_position:
        last_position = position
        print(f"Encoder position: {position} → LED {position_mod}")

        for led in led_pins:
            led.value = False
        led_pins[position_mod].value = True

    if not button.value and not button_held:
        button_held = True
        print("Button pressed")

    if button.value and button_held:
        button_held = False
        print("Button released")

    time.sleep(0.05)
