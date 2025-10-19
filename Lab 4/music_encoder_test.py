#!/usr/bin/env python3
import time, sys
import qwiic_gpio

ENCODER_A = 1
ENCODER_B = 2

def main():
    io = qwiic_gpio.QwiicGPIO()
    if not io.isConnected():
        print("Qwiic GPIO not connected")
        return
    io.begin()
    io.pinMode(ENCODER_A, io.GPIO_IN)
    io.pinMode(ENCODER_B, io.GPIO_IN)

    last_a = io.digitalRead(ENCODER_A)
    last_b = io.digitalRead(ENCODER_B)
    count = 0
    print("Start test. Rotate encoder slowly. Ctrl+C to exit.")

    try:
        while True:
            a = io.digitalRead(ENCODER_A)
            b = io.digitalRead(ENCODER_B)
            if a != last_a or b != last_b:
                ts = time.time()
                print(f"{ts:.3f} A={a} B={b} count={count}")
                # simple direction detection on A rising edge
                if last_a == 0 and a == 1:
                    if b == 0:
                        count += 1
                    else:
                        count -= 1
                    print(f"  -> direction count now {count}")
                last_a, last_b = a, b
            time.sleep(0.002)
    except KeyboardInterrupt:
        print("Exit")
        sys.exit(0)

if __name__ == "__main__":
    main()