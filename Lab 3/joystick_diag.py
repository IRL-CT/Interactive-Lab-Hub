#!/usr/bin/env python3
import time
from smbus2 import SMBus

I2C_ADDR = 0x20
BUS_NUM = 1
CAL_SEC = 1.0
READ_HZ = 20

def read_xyz(bus):
    blk = bus.read_i2c_block_data(I2C_ADDR, 0x00, 5)
    x = blk[0] | (blk[1] << 8)
    y = blk[2] | (blk[3] << 8)
    b = blk[4]
    return x, y, b

def main():
    bus = SMBus(BUS_NUM)
    xs, ys, bs = [], [], []
    t0 = time.time()
    while time.time() - t0 < CAL_SEC:
        x, y, b = read_xyz(bus)
        xs.append(x); ys.append(y); bs.append(b)
        time.sleep(0.01)
    cx = sum(xs)//len(xs)
    cy = sum(ys)//len(ys)
    b_idle = max(set(bs), key=bs.count)

    xr = max(xs) - min(xs)
    yr = max(ys) - min(ys)
    horiz_is_x = (xr >= yr)

    enter_h = max(400, int((xr if horiz_is_x else yr) * 0.40))
    enter_v = max(400, int((yr if horiz_is_x else xr) * 0.40))

    print("Centers:", cx, cy, "| Idle button:", b_idle, "| Ranges:", xr, yr, "| HORIZ is", "X" if horiz_is_x else "Y")
    print("Enter thresholds:", enter_h, enter_v)
    print("Moving... Ctrl+C to stop.")

    try:
        last = 0
        while True:
            x, y, b = read_xyz(bus)
            h_raw = x if horiz_is_x else y
            v_raw = y if horiz_is_x else x
            dh = h_raw - (cx if horiz_is_x else cy)
            dv = v_raw - (cy if horiz_is_x else cx)

            dir_h = "MID"
            if dh >= enter_h: dir_h = "RIGHT"
            elif dh <= -enter_h: dir_h = "LEFT"

            dir_v = "MID"
            if dv >= enter_v: dir_v = "DOWN"
            elif dv <= -enter_v: dir_v = "UP"

            pressed = (b != b_idle) or (b in (0,6,64,128))
            now = time.time()
            if now - last > 0.15:
                print(f"x={x:5d} y={y:5d} b={b:3d} | H:{dir_h:5s} V:{dir_v:5s} | PRESS={pressed}")
                last = now
            time.sleep(1.0/READ_HZ)
    except KeyboardInterrupt:
        pass
    finally:
        bus.close()

if __name__ == "__main__":
    main()
