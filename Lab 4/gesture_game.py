# proximity_jump_game.py
import time
import board
from adafruit_apds9960.apds9960 import APDS9960

# 初始化传感器
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_proximity = True  # 只启用距离感应
apds.enable_gesture = True    # 如果还想保留左右手势可以打开

# 游戏角色初始位置
player_x = 5
player_y = 5

MAX_X = 10
MAX_Y = 10

# 阈值设置（需要根据实际传感器距离调试）
NEAR_THRESHOLD = 60  # 靠近触发下蹲
FAR_THRESHOLD = 20   # 远离触发上跳

def print_game_state(x, y):
    """ASCII 文本显示角色位置"""
    for j in range(MAX_Y):
        row = ""
        for i in range(MAX_X):
            if i == x and j == y:
                row += "@"
            else:
                row += "."
        print(row)
    print("\n" + "-"*20 + "\n")

print("Proximity Jump Game Started! Approach to squat, move away to jump.")

while True:
    prox = apds.proximity
    gesture = apds.gesture()  # 如果想左右移动，可以使用这个

    # 靠近/远离控制上下
    if prox > NEAR_THRESHOLD:
        player_y = min(MAX_Y - 1, player_y + 1)  # 下蹲
        print(f"Proximity {prox}: Squat (Down)")
    elif prox < FAR_THRESHOLD:
        player_y = max(0, player_y - 1)  # 上跳
        print(f"Proximity {prox}: Jump (Up)")
    else:
        print(f"Proximity {prox}: Neutral")

    # 手势左右移动（可选）
    if gesture == 0x03:  # left
        player_x = max(0, player_x - 1)
        print("Gesture: LEFT")
    elif gesture == 0x04:  # right
        player_x = min(MAX_X - 1, player_x + 1)
        print("Gesture: RIGHT")

    # 显示游戏状态
    print_game_state(player_x, player_y)

    time.sleep(0.2)

