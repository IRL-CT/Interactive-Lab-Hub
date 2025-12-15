import time
import board
import busio
import adafruit_mpr121

# -------------------------
# I2C + MPR121 初始化
# -------------------------
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)

PAD = 0   # 你的銅箔接在哪個 pad? 0~11

print("MPR121 connected. Reading raw values...")
print("Place your object on the copper pad, then pick it up.")
print("----")

# 建議：連續讀60秒來觀察模式
while True:
    raw = mpr121[PAD].raw_value
    touched = mpr121[PAD].value  # boolean (有時會因baseline不同變動)

    print(f"PAD {PAD} | raw={raw:4} | touched={touched}")
    time.sleep(0.1)
