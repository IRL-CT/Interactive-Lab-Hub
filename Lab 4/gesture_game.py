import time
import board
from adafruit_apds9960.apds9960 import APDS9960

# 初始化传感器
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_proximity = True

player_x = 5
player_y = 5
MAX_X = 10
MAX_Y = 10

def print_game_state(x, y):
    for j in range(MAX_Y):
        row = ""
        for i in range(MAX_X):
            if i == x and j == y:
                row += "@"
            else:
                row += "."
        print(row)
    print("\n" + "-"*20 + "\n")

# 1️⃣ 测初始空手距离
print("Measuring initial distance... please leave hand away.")
time.sleep(1)
samples = []
for _ in range(5):
    samples.append(apds.proximity)
    time.sleep(0.1)
initial_prox = sum(samples)/len(samples)
print(f"Initial reference distance: {initial_prox}")

# 设置动作阈值（相对变化）
DELTA = 15  # 变化量超过 15 才触发

print("Proximity Jump Game Started! Approach to squat, move away to jump.")

while True:
    prox = apds.proximity
    diff = prox - initial_prox  # 相对变化量

    if diff > DELTA:
        player_y = min(MAX_Y - 1, player_y + 1)  # 下蹲
        print(f"Proximity {prox}: Squat (Down)")
    elif diff < -DELTA:
        player_y = max(0, player_y - 1)  # 上跳
        print(f"Proximity {prox}: Jump (Up)")
    else:
        print(f"Proximity {prox}: Neutral")

    print_game_state(player_x, player_y)
    time.sleep(0.2)
