#!/usr/bin/env python3
import os, sys, time, glob, subprocess
import qwiic_gpio
import RPi.GPIO as GPIO

try:
    import pygame
    HAVE_PYGAME = True
except Exception:
    HAVE_PYGAME = False

# Rotary encoder pins (BCM)
CLK, DT, SW = 17, 27, 22

LED_PINS = [6, 7, 0, 5, 3, 4]
STEP = 5
MIN_VOL, MAX_VOL = 0, 100

def find_fixed_wav():
    cands = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "music", "*_fixed.wav")))
    return cands[0] if cands else None

def set_system_volume(pct):
    try:
        subprocess.run(["amixer", "sset", "Master", f"{pct}%"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def level_from_volume(pct, segments):
    return max(0, min(segments, int(round(pct * segments / 100.0))))

def update_led_bar(io, level):
    for i, pin in enumerate(LED_PINS):
        io.digitalWrite(pin, io.GPIO_LO if i < level else io.GPIO_HI)

class Player:
    def __init__(self, path):
        self.path = path
        self.playing = False
        self._init_backend()

    def _init_backend(self):
        self.backend = "none"
        if HAVE_PYGAME:
            try:
                os.environ.setdefault("SDL_AUDIODRIVER", "alsa")
                pygame.mixer.init()
                pygame.mixer.music.load(self.path)
                self.backend = "pygame"
                return
            except Exception:
                pass
        self.backend = "aplay"

    def play(self):
        if self.backend == "pygame":
            pygame.mixer.music.play(loops=-1)
        else:
            self.proc = subprocess.Popen(["aplay", "-q", self.path],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.playing = True

    def pause_toggle(self):
        if self.backend == "pygame":
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.playing = False
            else:
                pygame.mixer.music.unpause()
                self.playing = True
        else:
            # no pause with aplay: stop/start
            self.stop()
            self.play()
            self.playing = True

    def stop(self):
        if self.backend == "pygame":
            pygame.mixer.music.stop()
        else:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.playing = False

    def set_volume(self, pct):
        if self.backend == "pygame":
            pygame.mixer.music.set_volume(max(0.0, min(1.0, pct/100.0)))

def main():
    wav = find_fixed_wav()
    if not wav:
        print("No *_fixed.wav found in ./music", file=sys.stderr); sys.exit(1)

    io = qwiic_gpio.QwiicGPIO()
    if not io.isConnected():
        print("Qwiic GPIO not found.", file=sys.stderr); sys.exit(1)
    io.begin()
    for p in LED_PINS:
        io.pinMode(p, io.GPIO_OUT)
        io.digitalWrite(p, io.GPIO_HI)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DT,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SW,  GPIO.IN, pull_up_down=GPIO.PUD_UP)

    player = Player(wav)

    vol = 50
    set_system_volume(vol)
    player.set_volume(vol)
    update_led_bar(io, level_from_volume(vol, len(LED_PINS)))

    last_clk = GPIO.input(CLK)
    last_dt  = GPIO.input(DT)
    last_edge_t = 0
    press_t = None
    player.play()

    def on_rotate(channel):
        nonlocal vol, last_clk, last_dt, last_edge_t
        now = time.time()
        if now - last_edge_t < 0.002:
            return
        clk = GPIO.input(CLK)
        dt  = GPIO.input(DT)
        if clk == last_clk and dt == last_dt:
            return
        direction = 1 if dt != clk else -1
        last_clk, last_dt = clk, dt
        new_vol = max(MIN_VOL, min(MAX_VOL, vol + direction * STEP))
        if new_vol != vol:
            vol = new_vol
            set_system_volume(vol)
            player.set_volume(vol)
            update_led_bar(io, level_from_volume(vol, len(LED_PINS)))
        last_edge_t = now

    def on_press(channel):
        nonlocal press_t
        if GPIO.input(SW) == 0:
            press_t = time.time()
        else:
            if press_t is None:
                return
            dur = time.time() - press_t
            press_t = None
            if dur > 0.6:
                # long press: mute
                mute_to = 0 if vol > 0 else 50
                vol_set(mute_to)
            else:
                # short press: pause/unpause
                player.pause_toggle()

    def vol_set(pct):
        nonlocal vol
        vol = max(MIN_VOL, min(MAX_VOL, pct))
        set_system_volume(vol)
        player.set_volume(vol)
        update_led_bar(io, level_from_volume(vol, len(LED_PINS)))

    GPIO.add_event_detect(CLK, GPIO.BOTH, callback=on_rotate, bouncetime=1)
    GPIO.add_event_detect(DT,  GPIO.BOTH, callback=on_rotate, bouncetime=1)
    GPIO.add_event_detect(SW,  GPIO.BOTH, callback=on_press,  bouncetime=10)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        player.stop()
        for p in LED_PINS:
            io.digitalWrite(p, io.GPIO_HI)
        GPIO.cleanup()

if __name__ == "__main__":
    main()
