import time
from smbus2 import SMBus

ADDR = 0x20  # 你的 i2c 地址
bus = SMBus(1)

def read_xyz():
    # 从寄存器0开始连读5字节：X_L, X_H, Y_L, Y_H, BTN
    blk = bus.read_i2c_block_data(ADDR, 0x00, 5)
    x = blk[0] | (blk[1] << 8)   # 小端
    y = blk[2] | (blk[3] << 8)   # 小端
    btn_raw = blk[4]
    # 先别假设 0/1 的含义，直接返回原值，下面打印看看
    return x, y, btn_raw

print("Move the stick and press/release to see values change. Ctrl+C to quit.")
try:
    while True:
        x, y, b = read_xyz()
        print(f"RAW -> X={x:4d}  Y={y:4d}  BTN={b}")
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

