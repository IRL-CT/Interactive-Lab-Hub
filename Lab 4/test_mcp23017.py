import time
import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017

i2c = busio.I2C(board.SCL, board.SDA)
time.sleep(0.5)

while not i2c.try_lock():
    pass
addresses = [hex(x) for x in i2c.scan()]
i2c.unlock()
print("I2C devices found:", addresses)

# 尝试常见地址
for addr in [0x20, 0x21, 0x22, 0x23, 0x24, 0x27]:
    try:
        print(f"Trying MCP23017 at 0x{addr:02x}...")
        mcp = MCP23017(i2c, address=addr)
        print(f"✅ MCP23017 found at 0x{addr:02x}")
        pin0 = mcp.get_pin(0)
        pin0.switch_to_output(value=False)
        while True:
            pin0.value = not pin0.value
            print(f"LED ON" if pin0.value else "LED OFF")
            time.sleep(0.5)
    except Exception as e:
        print(f"❌ Address 0x{addr:02x} failed: {e}")
