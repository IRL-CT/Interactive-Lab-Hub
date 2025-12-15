import adafruit_mpr121
import busio
import board
import time
import os
import subprocess
import neopixel

# ---------- NeoPixel Setup ----------
PIXEL_PIN = board.D12
NUM_PIXELS = 24
BRIGHTNESS = 0.3

pixels = neopixel.NeoPixel(
    PIXEL_PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False
)

# ---------- MPR121 Setup ----------
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)

# ---------- Sound State ----------
purr_process = None
meow_process = None

# ---------- Helper: Stop all sounds ----------
def stop_all():
    global purr_process, meow_process
    os.system("pkill aplay")
    purr_process = None
    meow_process = None
    pixels.fill((0, 0, 0))
    pixels.show()

# ---------- Helper: Play sound in loop ----------
def play_purr():
    global purr_process
    if purr_process is None:
        purr_process = subprocess.Popen(["aplay", "-q", "sound/purr.wav"])

def play_meow():
    global meow_process
    if meow_process is None:
        meow_process = subprocess.Popen(["aplay", "-q", "sound/meow.wav"])

# ---------- LED Animations ----------
def breathing(color, steps=20, speed=0.08):
    """Quick breathing animation for purring"""
    r, g, b = color
    for i in range(steps):
        level = i / steps
        pixels.fill((int(r*level), int(g*level), int(b*level)))
        pixels.show()
        time.sleep(speed)
    for i in range(steps, -1, -1):
        level = i / steps
        pixels.fill((int(r*level), int(g*level), int(b*level)))
        pixels.show()
        time.sleep(speed)

# def chase(color, speed=0.06):
#     """Fast chasing animation for meow"""
#     for i in range(NUM_PIXELS):
#         pixels.fill((0, 0, 0))
#         pixels[i] = color
#         pixels.show()
#         time.sleep(speed)

# ---------- Main Loop ----------
def main():
    last_release_time = None
    
    while True:
        touched_1 = mpr121[1].value
        touched_2 = mpr121[2].value
        
        if touched_1:
            # Reset timer, play purr
            last_release_time = None
            play_purr()
            breathing((80, 40, 150))
            
        elif touched_2:
            # Reset timer, play meow
            last_release_time = None
            play_meow()
            breathing((255, 80, 10))
            
        else:
            # No touch detected
            if last_release_time is None:
                # Just released, start timer
                last_release_time = time.time()
                print("Touch released, starting 3-second timer...")
            
            elapsed = time.time() - last_release_time
            
            if elapsed >= 3.0:
                # 3 seconds passed, stop everything
                print("3 seconds passed, stopping...")
                stop_all()
                last_release_time = None
            
            time.sleep(0.1)

if __name__ == "__main__":
    main()