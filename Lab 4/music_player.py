import board
import os
import time
import subprocess
from adafruit_apds9960.apds9960 import APDS9960

# 初始化 I2C
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_proximity = True
apds.enable_gesture = True

# 音乐文件夹
MUSIC_FOLDER = "/home/pi/Music"  # 替换成你实际路径
songs = [f for f in os.listdir(MUSIC_FOLDER) if f.endswith(".mp3")]
songs.sort()
current_index = 0

# 播放器初始化
player_process = None

def play_song(index):
    global player_process
    if player_process:
        player_process.terminate()
    song_path = os.path.join(MUSIC_FOLDER, songs[index])
    print(f"Playing: {songs[index]}")
    # 使用 mpg123 播放 mp3 文件
    player_process = subprocess.Popen(["mpg123", "-q", song_path])

def pause_song():
    global player_process
    if player_process:
        print("Pausing playback")
        player_process.terminate()
        player_process = None

def resume_song():
    play_song(current_index)

# 开始播放第一首歌
play_song(current_index)

while True:
    gesture = apds.gesture()
    proximity = apds.proximity

    # 手势控制切歌
    if gesture == 0x03:  # 左
        current_index = (current_index - 1) % len(songs)
        play_song(current_index)
    elif gesture == 0x04:  # 右
        current_index = (current_index + 1) % len(songs)
        play_song(current_index)

    # 接近/远离控制播放
    if proximity > 200:  # 太靠近
        pause_song()
    elif proximity < 50:  # 远离
        resume_song()

    time.sleep(0.2)
