#!/usr/bin/env python3
import os, time, subprocess, statistics
from pathlib import Path
import qwiic_joystick
from outfits import THEMES, ORDER

READ_HZ = 20
CAL_SEC = 0.8
SAY_COOLDOWN = 0.45
BTN_COOLDOWN = 1.2
PRESS_STABLE_N = 2
MID_HOLD_FALLBACK = True
MID_HOLD_SEC = 1.2

LAB3_DIR = Path("/home/pi/Interactive-Lab-Hub-hz764/Lab 3")
TMP_WAV = LAB3_DIR / "tmp.wav"

def say(text: str):
    try:
        r = subprocess.run(
            ["piper", "--model", "en_US-lessac-medium", "--output_file", str(TMP_WAV)],
            input=text.encode("utf-8"), cwd=str(LAB3_DIR), check=False,
        )
        if r.returncode == 0 and TMP_WAV.exists():
            subprocess.run(["aplay", str(TMP_WAV)], cwd=str(LAB3_DIR), check=False)
            return
    except Exception:
        pass
    subprocess.run(["espeak", text], check=False)

def clamp_hys(off, enter_thr, exit_thr, prev):
    if prev == "MID":
        if off >= enter_thr: return "POS"
        if off <= -enter_thr: return "NEG"
        return "MID"
    else:
        if -exit_thr <= off <= exit_thr: return "MID"
        return prev

def safe_button_read(js):
    try:
        return js.button  # typical: 0 pressed, 1 released
    except Exception:
        return None

def main():
    js = qwiic_joystick.QwiicJoystick()
    if not js.connected:
        print("Joystick not connected. Check SDA/SCL.")
        return
    js.begin()

    xs, ys = [], []
    t0 = time.time()
    while time.time() - t0 < CAL_SEC:
        try:
            xs.append(js.horizontal)
            ys.append(js.vertical)
        except Exception:
            pass
        time.sleep(0.01)
    cx = int(statistics.median(xs)) if xs else 512
    cy = int(statistics.median(ys)) if ys else 512

    xr = max(300, (max(xs) - min(xs)) if xs else 1023)
    yr = max(300, (max(ys) - min(ys)) if ys else 1023)

    enter_h = max(80, int(xr * 0.25))
    exit_h  = max(40, int(xr * 0.14))
    enter_v = max(80, int(yr * 0.25))
    exit_v  = max(40, int(yr * 0.14))

    # probe button once
    last_btn = safe_button_read(js)
    button_supported = (last_btn is not None)
    if not button_supported:
        print("[WARN] Button register not responding. Voice trigger will use mid-hold fallback." if MID_HOLD_FALLBACK else "[WARN] Button not available.")

    theme_idx = 0
    item_idx = 0
    last_say = 0.0

    def speak_current():
        nonlocal last_say
        now = time.time()
        if now - last_say < SAY_COOLDOWN: return
        last_say = now
        theme = ORDER[theme_idx]
        items = THEMES[theme]
        text = f"recommend type: {theme}. Option {item_idx+1}. {items[item_idx]}"
        print("[SAY]", text)
        say(text)

    print("Ready. Up/Down=theme, Left/Right=item, Press=Q&A")
    speak_current()

    last_h = "MID"
    last_v = "MID"
    btn_cnt = 0
    last_btn_time = 0.0
    mid_since = time.time()
    interval = 1.0 / READ_HZ

    try:
        while True:
            try:
                x = js.horizontal
                y = js.vertical
            except Exception:
                time.sleep(interval)
                continue

            dh = x - cx
            dv = y - cy

            dir_h = clamp_hys(dh, enter_h, exit_h, last_h)
            dir_v = clamp_hys(dv, enter_v, exit_v, last_v)

            if dir_v != "MID" and last_v == "MID":
                if dir_v == "NEG":
                    theme_idx = (theme_idx - 1) % len(ORDER)
                elif dir_v == "POS":
                    theme_idx = (theme_idx + 1) % len(ORDER)
                item_idx = 0
                speak_current()

            if dir_h != "MID" and last_h == "MID":
                items = THEMES[ORDER[theme_idx]]
                if dir_h == "NEG":
                    item_idx = (item_idx - 1) % len(items)
                elif dir_h == "POS":
                    item_idx = (item_idx + 1) % len(items)
                speak_current()

            triggered = False

            if button_supported:
                b = safe_button_read(js)
                if b is not None:
                    pressed = (b == 0)
                    was_pressed = (last_btn == 0) if (last_btn is not None) else False
                    if pressed: btn_cnt += 1
                    else: btn_cnt = 0
                    if btn_cnt >= PRESS_STABLE_N and not was_pressed:
                        triggered = True
                    last_btn = b
                else:
                    # button read failed this frame, skip without crashing
                    pass
            else:
                if MID_HOLD_FALLBACK:
                    if -exit_v <= dv <= exit_v and dir_h == "MID":
                        if time.time() - mid_since >= MID_HOLD_SEC:
                            triggered = True
                            mid_since = time.time() + 999.0
                    else:
                        mid_since = time.time()

            if triggered and (time.time() - last_btn_time >= BTN_COOLDOWN):
                print("[BTN] Voice Q&A")
                last_btn_time = time.time()
                try:
                    env = dict(os.environ)
                    env["PYTHONPATH"] = str(LAB3_DIR)
                    subprocess.run(
                        ["python3", str(LAB3_DIR / "my-scripts/voice_interaction_router.py")],
                        cwd=str(LAB3_DIR), env=env, check=False,
                    )
                except Exception as e:
                    print("[WARN] voice error:", e)

            last_h, last_v = dir_h, dir_v
            time.sleep(interval)

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
