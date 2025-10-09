import time
import board
from adafruit_apds9960.apds9960 import APDS9960
import pygame
import os

# --------------------
# 初始化传感器
# --------------------
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_gesture = True
apds.enable_proximity = True

# --------------------
# 初始化 pygame 播放器
# --------------------
pygame.mixer.init()

# 音乐文件夹
MUSIC_DIR = "music"  # 在当前目录下创建 music 文件夹
songs = [os.path.join(MUSIC_DIR, f) for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]

if not songs:
    print("请在 music 文件夹里放入 mp3 或 wav 文件！")
    exit()

current_song = 0
pygame.mixer.music.load(songs[current_song])
pygame.mixer.music.play()
playing = True

def show_status():
    status = "播放中" if playing else "暂停中"
    print(f"[{status}] 当前歌曲: {os.path.basename(songs[current_song])}")

print("Gesture Music Player Started!")
show_status()
print("左右手势切歌，靠近暂停，远离播放")

# --------------------
# 距离阈值（可调）
# --------------------
NEAR_THRESHOLD = 60  # 手靠近触发暂停
FAR_THRESHOLD = 20   # 手远离触发播放

# --------------------
# 主循环
# --------------------
while True:
    gesture = apds.gesture()
    prox = apds.proximity

    # --------------------
    # 手势切歌
    # --------------------
    if gesture == 0x03:  # 左手
        current_song = (current_song - 1) % len(songs)
        pygame.mixer.music.load(songs[current_song])
        pygame.mixer.music.play()
        playing = True
        print("手势: 左 → 上一首")
        show_status()
        time.sleep(0.5)  # 防止连续触发

    elif gesture == 0x04:  # 右手
        current_song = (current_song + 1) % len(songs)
        pygame.mixer.music.load(songs[current_song])
        pygame.mixer.music.play()
        playing = True
        print("手势: 右 → 下一首")
        show_status()
        time.sleep(0.5)

    # --------------------
    # 靠近/远离控制播放/暂停
    # --------------------
    if prox > NEAR_THRESHOLD and playing:
        pygame.mixer.music.pause()
        playing = False
        print("靠近 → 暂停")
        show_status()
        time.sleep(0.3)
    elif prox < FAR_THRESHOLD and not playing:
        pygame.mixer.music.unpause()
        playing = True
        print("远离 → 播放")
        show_status()
        time.sleep(0.3)

    time.sleep(0.1)
