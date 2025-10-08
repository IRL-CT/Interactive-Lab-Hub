# SPDX-License-Identifier: MIT
# Control 4 LEDs on SparkFun Qwiic GPIO (MCP23017 DEV-17047)
# using Adafruit I2C QT Rotary Encoder (0x36)

import time
import board
import busio
from adafruit_seesaw import seesaw, rotaryio, digitalio

# 尝试导入官方 MCP23017，如果不兼容则使用通用基类
try:
    from adafruit_mcp230xx.mcp23017 import MCP23017
    MCP_CLASS = "adafruit"
except Exception:
    from adafruit_mcp230xx.mcp230xx import MCP230XX
    MCP_CLASS = "generic"

# 初始化 I2C
i2c = busio.I2C(board.SCL, board.SDA)
time.sleep(0.5)  # 等待稳定

# 扫描 I2C 设备
while not i2c.try_lock():
    pass
addresses = [hex(x) for x in i2c.scan()]
i2c.unlock()
print("I2C devices found:", addresses)

# --- 初始化旋转编码器 (Seesaw) ---
encoder_i2c_addr = 0x36
ss = seesaw.Seesaw(i2c, addr=encoder_i2c_addr)
product = (ss.get_version() >> 16) & 0xFFFF
print(f"Found encoder product {product}")
encoder = rotaryio.IncrementalEncoder(ss)
button = digitalio.DigitalIO(ss, 24)
last_position = None
button_held = False

# --- 初始化 Qwiic GPIO / MCP23017 ---
try:
    gpio = MCP23017(i2c, address=0x27)
    print("Using Adafruit MCP23017 driver")
except Exception as e:
    print("Standard MCP23017 init failed, switching to base class:", e)
    from adafruit_mcp230xx.mcp230xx import MCP230XX
    gpio = MCP230XX(i2c, address=0x27, num_gpios=16)
    print("Using generic MCP230XX driver")

# 定义 4 个输出口控制灯泡
led_pins = [gpio.get_pin(i) for i in range(4)]
for led in led_pins:
    led.switch_to_output(value=False)

print("Rotate the knob to light LEDs (positions 0–3). Press to reset.")

# --- 主循环 ---
while True:
    pos = -encoder.position  # 旋转方向相反，取负
    if pos != last_position:
        last_position = pos
        print(f"Position: {pos}")

        # 只保留 0~3 范围
        idx = pos % 4
        for i, led in enumerate(led_pins):
            led.value = (i == idx)

    # 按钮重置功能
    if not button.value and not button_held:
        button_held = True
        print("Button pressed — turning off all LEDs.")
        for led in led_pins:
            led.value = False
        encoder.position = 0

    if button.value and button_held:
        button_held = False

    time.sleep(0.05)
