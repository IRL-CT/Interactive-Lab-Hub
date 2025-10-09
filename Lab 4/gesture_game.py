# gesture_game_ascii.py
# Gesture-Controlled Game Demo with ASCII display
import time
import board
from adafruit_apds9960.apds9960 import APDS9960

# 初始化 APDS-9960
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_proximity = True
apds.enable_gesture = True

# 游戏角色初始位置
player_x = 5
player_y = 5

# 假设游戏屏幕大小 10x10
MAX_X = 10
MAX_Y = 10

def print_game_state(x, y):
    """ASCII 文本显示角色位置"""
    for j in range(MAX_Y):
        row = ""
        for i in range(MAX_X):
            if i == x and j == y:
                row += "@"  # 用 @ 表示角色
            else:
                row += "."  # 用 . 表示空地
        print(row)
    print("\n" + "-"*20 + "\n")

print("Gesture-Controlled Game Started! Move with gestures. Approach sensor to speed up.")

while True:
    gesture = apds.gesture()
    prox = apds.proximity

    # 手势控制移动
    if gesture == 0x01:       # up
        player_y = max(0, player_y - 1)
        print("Gesture: UP")
    elif gesture == 0x02:     # down
        player_y = min(MAX_Y-1, player_y + 1)
        print("Gesture: DOWN")
    elif gesture == 0x03:     # left
        player_x = max(0, player_x - 1)
        print("Gesture: LEFT")
    elif gesture == 0x04:     # right
        player_x = min(MAX_X-1, player_x + 1)
        print("Gesture: RIGHT")

    # 靠近触发加速
    if prox > 50:  # 阈值可调
        print("Proximity: NEAR! Boost activated!")
        player_x = min(MAX_X-1, player_x + 1)  # 向右加速

    # 打印 ASCII 游戏状态
    print_game_state(player_x, player_y)

    time.sleep(0.2)
