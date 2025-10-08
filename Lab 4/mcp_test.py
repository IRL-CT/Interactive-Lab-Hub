import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017
import time

i2c = busio.I2C(board.SCL, board.SDA)
while not i2c.try_lock():
    pass
print("I2C addresses found:", [hex(x) for x in i2c.scan()])
i2c.unlock()

# 初始化 GPIO expander
i2c = busio.I2C(board.SCL, board.SDA)
gpio = MCP23017(i2c, address=0x27)

pin0 = gpio.get_pin(0)
pin0.switch_to_output(value=False)

print("Blinking on pin 0 ...")
while True:
    pin0.value = True
    time.sleep(0.5)
    pin0.value = False
    time.sleep(0.5)
