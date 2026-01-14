# gesture_full_game.py
import time
import board
from adafruit_apds9960.apds9960 import APDS9960
import pygame

# 初始化 APDS-9960
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_gesture = True

# 游戏屏幕设置
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 400
GRID_SIZE = 10  # 10x10 网格

# 初始化 pygame
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Gesture Controlled Game")
clock = pygame.time.Clock()

# 角色初始位置（格子坐标）
player_x = 5
player_y = 5

# 画游戏状态
def draw_game():
    screen.fill((30, 30, 30))  # 背景色
    cell_w = WINDOW_WIDTH // GRID_SIZE
    cell_h = WINDOW_HEIGHT // GRID_SIZE

    # 画网格
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            rect = pygame.Rect(x*cell_w, y*cell_h, cell_w-2, cell_h-2)
            pygame.draw.rect(screen, (50, 50, 50), rect)

    # 画角色
    rect = pygame.Rect(player_x*cell_w, player_y*cell_h, cell_w-2, cell_h-2)
    pygame.draw.rect(screen, (0, 200, 0), rect)

    pygame.display.flip()

print("Use UP/DOWN to jump/squat and LEFT/RIGHT to move forward/backward!")

# 主循环
while True:
    # 处理 pygame 事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    gesture = apds.gesture()

    # 上下手势 → 上跳/下蹲
    if gesture == 0x01:       # up
        player_y = max(0, player_y - 1)
        print("Gesture: UP → Jump")
    elif gesture == 0x02:     # down
        player_y = min(GRID_SIZE-1, player_y + 1)
        print("Gesture: DOWN → Squat")

    # 左右手势 → 左/右移动
    elif gesture == 0x03:     # left
        player_x = max(0, player_x - 1)
        print("Gesture: LEFT → Move Backward")
    elif gesture == 0x04:     # right
        player_x = min(GRID_SIZE-1, player_x + 1)
        print("Gesture: RIGHT → Move Forward")

    draw_game()
    clock.tick(10)  # 每秒刷新 10 帧
    time.sleep(0.05)
