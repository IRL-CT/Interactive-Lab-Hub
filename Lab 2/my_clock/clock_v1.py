import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import random
import datetime

# === Display setup ===
cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None
BAUDRATE = 64000000
spi = board.SPI()

disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

height = disp.width
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90
draw = ImageDraw.Draw(image)

font_normal = ImageFont.truetype(
    "/home/pi/Interactive-Lab-Hub/Lab 2/fonts/dogica/dogicapixel.ttf", 14
)
font_big = ImageFont.truetype(
    "/home/pi/Interactive-Lab-Hub/Lab 2/fonts/dogica/dogicapixel.ttf", 18
)

# === Buttons ===
buttonA = digitalio.DigitalInOut(board.D23)  # GPIO23
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB = digitalio.DigitalInOut(board.D24)  # GPIO24
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# === number to english ===
numbers_map = {
    0: "ZERO", 1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR",
    5: "FIVE", 6: "SIX", 7: "SEVEN", 8: "EIGHT", 9: "NINE",
    10: "TEN", 11: "ELEVEN", 12: "TWELVE", 13: "THIRTEEN",
    14: "FOURTEEN", 15: "FIFTEEN", 16: "SIXTEEN", 17: "SEVENTEEN",
    18: "EIGHTEEN", 19: "NINETEEN", 20: "TWENTY", 30: "THIRTY",
    40: "FORTY", 50: "FIFTY"
}

def number_to_words(n):
    if n in numbers_map:
        return numbers_map[n]
    elif n < 30:
        return "TWENTY " + numbers_map[n % 10]
    elif n < 40:
        return "THIRTY " + numbers_map[n % 10]
    elif n < 50:
        return "FORTY " + numbers_map[n % 10]
    elif n < 60:
        return "FIFTY " + numbers_map[n % 10]
    return str(n)

def get_time_words():
    now = datetime.datetime.now()
    hour = now.hour % 12
    hour = 12 if hour == 0 else hour
    minute = now.minute
    return f"{number_to_words(hour)} {number_to_words(minute)}"

def init_time_letters():
    """建立時間字母 + 初始隨機位置 + 目標位置"""
    now = datetime.datetime.now()
    hour = now.hour % 12
    hour = 12 if hour == 0 else hour
    minute = now.minute

    
    hour_str = number_to_words(hour)        # e.g. "TEN"
    minute_str = number_to_words(minute)    # e.g. "FORTY NINE"


    hour_words = hour_str.split(" ")        # ["TEN"]
    minute_words = minute_str.split(" ")    # ["FORTY","NINE"]

    hour_letters = list(" ".join(hour_words))  
    hour_total_w = len(hour_letters) * 18
    hour_start_x = (width - hour_total_w) // 2
    hour_y = height // 2 - 14

    minute_letters = list(" ".join(minute_words))
    minute_total_w = len(minute_letters) * 18
    minute_start_x = (width - minute_total_w) // 2
    minute_y = height // 2 + 10

    # merge
    time_letters = hour_letters + minute_letters
    time_targets = []

    for i, _ in enumerate(hour_letters):
        time_targets.append([hour_start_x + i * 18, hour_y])

    for i, _ in enumerate(minute_letters):
        time_targets.append([minute_start_x + i * 18, minute_y])

    # random initial position
    time_pos = [[random.randint(0, width), random.randint(0, height)] for _ in time_letters]

    return time_letters, time_pos, time_targets


# random letters
random_letters = [chr(random.randint(65, 90)) for _ in range(40)]
random_pos = [[random.randint(0, width), random.randint(0, height)] for _ in random_letters]
random_vel = [[random.choice([-1,1]), random.choice([-1,1])] for _ in random_letters]


time_letters, time_pos, time_targets = init_time_letters()

# === Main Loop ===
while True:
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

    speed = 3 if not buttonA.value else 1  # Button A accelerate
    if not buttonB.value:  # Button B restart
        time_letters, time_pos, time_targets = init_time_letters()

    for i, letter in enumerate(random_letters):
        x, y = random_pos[i]
        dx, dy = random_vel[i]

        x += dx
        y += dy

        if x < 0 or x > width - 10:
            dx *= -1
        if y < 0 or y > height - 10:
            dy *= -1

        random_pos[i] = [x, y]
        random_vel[i] = [dx, dy]

        draw.text((x, y), letter, font=font_normal, fill="#5c5b54b3")
    
    
    


    # Update time letters → move towards target
    for i, letter in enumerate(time_letters):
        x, y = time_pos[i]
        tx, ty = time_targets[i]

        if x < tx: x += speed
        if x > tx: x -= speed
        if y < ty: y += speed
        if y > ty: y -= speed

        time_pos[i] = [x, y]
        draw.text((x, y), letter, font=font_big, fill="#FFFF00")


    disp.image(image, rotation)
    time.sleep(0.05)
