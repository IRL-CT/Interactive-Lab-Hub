import time
from smbus2 import SMBus

ADDR = 0x20   # 你 i2cdetect 扫到的地址

bus = SMBus(1)

def read_xyz():
    # 从寄存器0开始连续读取3字节：X, Y, Button
    data = bus.read_i2c_block_data(ADDR, 0x00, 3)
    x, y, btn = data[0], data[1], data[2]
    pressed = (btn == 0)  # 按下=0，未按=1
    return x, y, pressed

try:
    while True:
        x, y, pressed = read_xyz()
        print(f"X={x:3d}  Y={y:3d}  BTN={'PRESSED' if pressed else '---'}")
        time.sleep(0.2)

except KeyboardInterrupt:
    print("Bye!")
