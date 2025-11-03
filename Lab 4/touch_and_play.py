import time
import board
import busio
import adafruit_mpr121
import pygame

# Initialize audio mixer
pygame.mixer.init()

# Load sound files for different notes
sounds = {
    1: pygame.mixer.Sound("notes/bell_A4.mp3"),
    2: pygame.mixer.Sound("notes/bell_B4.mp3"),
    3: pygame.mixer.Sound("notes/bell_C5.mp3"),
    4: pygame.mixer.Sound("notes/bell_D5.mp3"),

}

# Initialize I2C and MPR121
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)

# Keep track of touch state
was_touched = [False] * 12

print("Ready! Touch a pad to play a note")

while True:
    for i in range(12):
        touched = mpr121[i].value
        if touched and not was_touched[i]:
            if i in sounds:
                print(f"Pad {i} touched")
                sounds[i].play()  # Play once
        was_touched[i] = touched
    time.sleep(0.1)
