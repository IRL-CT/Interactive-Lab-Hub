# gesture_daemon.py
import os, time
import board, busio
from adafruit_apds9960.apds9960 import APDS9960

VIEW_MODE_FILE = "/tmp/reminder_view_mode"

# --- Threshold and debounce parameters ---
THRESH_NEAR = 60     # Considered "hand near"
THRESH_FAR  = 40     # Considered "hand far"
COOLDOWN_S  = 1.0    # Minimum time between toggles

def read_mode():
    try:
        with open(VIEW_MODE_FILE, "r") as f:
            v = f.read().strip()
            return v if v in ("detail", "minimal") else "detail"
    except FileNotFoundError:
        return "detail"

def write_mode(mode):
    with open(VIEW_MODE_FILE, "w") as f:
        f.write(mode)

def toggle_mode():
    cur = read_mode()
    new = "minimal" if cur == "detail" else "detail"
    write_mode(new)
    print(f"[gesture] toggle -> {new}")

def main():
    # Ensure mode file exists
    if not os.path.exists(VIEW_MODE_FILE):
        write_mode("detail")

    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = APDS9960(i2c)
    sensor.enable_proximity = True

    last_toggle = 0.0
    near_state = False
    alpha = 0.4
    filt = None

    print("[gesture] running... (wave hand to toggle)")
    while True:
        prox = sensor.proximity
        if filt is None:
            filt = prox
        else:
            filt = alpha * prox + (1 - alpha) * filt

        now = time.monotonic()

        # Rising edge: far -> near
        if not near_state and filt >= THRESH_NEAR:
            if now - last_toggle >= COOLDOWN_S:
                toggle_mode()
                last_toggle = now
            near_state = True

        # Falling edge: near -> far
        if near_state and filt <= THRESH_FAR:
            near_state = False

        time.sleep(0.05)

if __name__ == "__main__":
    main()
