#!/usr/bin/env python3
# Minimal I2C address scanner (Blinka)
import board, busio
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
while not i2c.try_lock(): pass
try:
    addrs = i2c.scan()
    print("I2C addresses:", [hex(a) for a in addrs])
finally:
    i2c.unlock()
