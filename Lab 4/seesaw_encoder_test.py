#!/usr/bin/env python3
import time
import board, busio
from adafruit_seesaw.seesaw import Seesaw

ADDR_CANDS = [0x36, 0x27]
i2c = busio.I2C(board.SCL, board.SDA)

ss = None
for addr in ADDR_CANDS:
    try:
        ss_try = Seesaw(i2c, addr=addr)
        # quick sanity read
        _ = ss_try.get_status() if hasattr(ss_try, "get_status") else None
        ss = ss_try
        print(f"found seesaw at 0x{addr:02x}")
        break
    except Exception:
        pass

if ss is None:
    print("No seesaw device found at common addresses. Run i2cdetect -y 1 and adjust address.")
    raise SystemExit(1)

# reset position if supported
if hasattr(ss, "set_encoder_position"):
    ss.set_encoder_position(0)
else:
    print("Warning: set_encoder_position not available on this Seesaw object.")
print("available methods:", [m for m in dir(ss) if callable(getattr(ss, m)) and not m.startswith("_")])

last = ss.get_encoder_position() if hasattr(ss, "get_encoder_position") else None
print("start, initial position:", last)
try:
    while True:
        if hasattr(ss, "get_encoder_position"):
            v = ss.get_encoder_position()
            if v != last:
                print("position:", v)
                last = v
        else:
            # fallback: read raw rotary register if library differs
            try:
                v = ss.get rotary_position  # placeholder, won't run if not present
            except Exception:
                pass
        time.sleep(0.01)
except KeyboardInterrupt:
    pass