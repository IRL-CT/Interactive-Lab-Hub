import smbus2
import time
import random
import pygame
import board
import busio
import adafruit_mpr121
import qwiic
import os

# -------------------- TCA9534 LED setup --------------------
I2C_ADDR = 0x27
bus = smbus2.SMBus(1)

OUTPUT_REG = 0x01
CONFIG_REG = 0x03  # 1=input, 0=output
bus.write_byte_data(I2C_ADDR, CONFIG_REG, 0x00)  # all pins as outputs

# -------------------- Music & Sensors setup --------------------
base_path = os.path.dirname(os.path.abspath(__file__))
music_folder = os.path.join(base_path, "music")
playlist = [os.path.join(music_folder, f) for f in sorted(os.listdir(music_folder)) if f.endswith(".mp3")]
if not playlist:
    print("No music files found in 'music' folder!")
    exit()

# I2C for MPR121
i2c = busio.I2C(board.SCL, board.SDA)
try:
    mpr121 = adafruit_mpr121.MPR121(i2c)
except ValueError:
    print("MPR121 not detected. Check wiring.")
    exit()

# Distance sensor
vcnl4040 = qwiic.QwiicVL53L1X()

# Pygame music
pygame.mixer.init()
current_song = 0
volume = 0.5
pygame.mixer.music.set_volume(volume)

def play_song(index):
    pygame.mixer.music.load(playlist[index])
    pygame.mixer.music.play(-1)

def shuffle_songs():
    global current_song
    random.shuffle(playlist)
    current_song = 0
    play_song(current_song)
    print("Playlist shuffled")

def change_volume(delta):
    global volume
    volume = min(1.0, max(0.0, volume + delta))
    pygame.mixer.music.set_volume(volume)
    print(f"Volume set to {volume:.2f}")

play_song(current_song)
print("Freeze Dance Machine + Disco LEDs ready!")

# -------------------- Main loop --------------------
MOTION_THRESHOLD = 2000
last_motion = False

try:
    while True:
        # --- TCA9534 LED "disco" ---
        led_pattern = random.randint(0, 255)
        bus.write_byte_data(I2C_ADDR, OUTPUT_REG, led_pattern)
        # print(f"LED pattern: {led_pattern:08b}")  # optional debug

        # --- Distance / motion ---
        try:
            vcnl4040.start_ranging()
            time.sleep(0.02)
            distance = vcnl4040.get_distance()
            vcnl4040.stop_ranging()
            motion = distance > MOTION_THRESHOLD
        except OSError as e:
            print("Distance sensor error:", e)
            motion = False

        if motion and not last_motion:
            pygame.mixer.music.unpause()
        elif not motion and last_motion:
            pygame.mixer.music.pause()

        last_motion = motion

        # --- Capacitive touch inputs ---
        for i in range(12):
            if mpr121[i].value:
                if 0 <= i <= 5:
                    shuffle_songs()
                elif 6 <= i <= 8:
                    change_volume(-0.1)
                elif 9 <= i <= 11:
                    change_volume(+0.1)
                time.sleep(0.3)  # debounce

        # Randomized LED delay for disco feel
        time.sleep(random.uniform(0.05, 0.1))

except KeyboardInterrupt:
    bus.write_byte_data(I2C_ADDR, OUTPUT_REG, 0x00)  # turn off LEDs
    pygame.mixer.music.stop()
    print("\nParty over. Lights off, music stopped.")
