#!/usr/bin/env python3
import time
import qwiic_gpio

io = qwiic_gpio.QwiicGPIO()
if not io.isConnected():
    print("QWIIC NOT CONNECTED")
    raise SystemExit(1)
io.begin()
PINS = list(range(8))
for p in PINS:
    io.pinMode(p, io.GPIO_IN)
print("Reading pins, Ctrl+C to stop")
try:
    while True:
        values = [str(io.digitalRead(p)) for p in PINS]
        print(" ".join(f"{p}:{v}" for p, v in zip(PINS, values)))
        time.sleep(0.05)
except KeyboardInterrupt:
    print("Exit")