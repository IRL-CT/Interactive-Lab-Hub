import pandas as pd
import time
import subprocess
import digitalio
import board
import mqtt
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import busio
import adafruit_rgb_display.ili9341 as ili9341
import adafruit_rgb_display.st7789 as st7789  # pylint: disable=unused-import
import adafruit_rgb_display.hx8357 as hx8357  # pylint: disable=unused-import
import adafruit_rgb_display.st7735 as st7735  # pylint: disable=unused-import
import adafruit_rgb_display.ssd1351 as ssd1351  # pylint: disable=unused-import
import adafruit_rgb_display.ssd1331 as ssd1331  # pylint: disable=unused-import

import adafruit_mpr121

i2c = busio.I2C(board.SCL, board.SDA)

mpr121 = adafruit_mpr121.MPR121(i2c)

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
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

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)

IS_HOST = True
def wait_for_touch():
    print("Touch a pad to choose ROW...")
    row_chosen = False
    while not row_chosen:
        for i in range(3):
            if mpr121[i].value:
                if i == 0:
                    cell = "A"
                elif i == 1:
                    cell = "B"
                elif i == 2:
                    cell = "C"
                print(f"Row selected: {cell}")
                row_chosen = True
                while mpr121[i].value:
                    time.sleep(0.2)
                break
        time.sleep(0.05)

    print("Touch a pad to choose COLUMN...")
    col_chosen = False
    while not col_chosen:
        for i in range(4):
            if mpr121[i].value:
                cell += str(i + 1)
                print(f"Column selected: {i + 1}")
                col_chosen = True
                while mpr121[i].value:
                    time.sleep(0.2)
                break
        time.sleep(0.05)

    print(f"? Selected cell: {cell}")
    return cell


def draw_square(C, side):
    cx = point_dict[C][0]
    cy = point_dict[C][1]
    x0 = cx - side / 2
    y0 = cy - side / 2
    x1 = cx + side / 2
    y1 = cy + side / 2
    draw.rectangle((x0, y0, x1, y1), outline="white", width=3)
    disp.image(image, rotation=90)


def draw_cross(C, side):
    cx = point_dict[C][0]
    cy = point_dict[C][1]
    x0 = cx - side / 2
    y0 = cy - side / 2
    x1 = cx + side / 2
    y1 = cy + side / 2
    draw.line((x0, y0, x1, y1), fill="white", width=3)
    draw.line((x0, y1, x1, y0), fill="white", width=3)
    disp.image(image, rotation=90)


def draw_word(ship, C):
    cx = point_dict[C][0]
    cy = point_dict[C][1]
    if ship == "battleship":
        s = "B"
    if ship == "destroyer":
        s = "D"
    if ship == "submarine":
        s = "S"
    s_bbox = draw.textbbox((0, 0), s, font=font)
    s_width = s_bbox[2] - s_bbox[0]
    s_height = s_bbox[3] - s_bbox[0]
    draw.text((cx - s_width // 2, cy - s_height // 2), s, font=font, fill="white")
    disp.image(image, rotation=90)


def load_ships(csv_path="ships.csv"):
    df = pd.read_csv(csv_path)
    ships = {}
    for _, row in df.iterrows():
        ship_type = row["type"]
        cells = [c.strip().upper() for c in row["cells"].split(",")]
        ships[ship_type] = cells
    return ships


def check_hit(cell, ships):
    for ship, cells in ships.items():
        if cell in cells:
            cells.remove(cell)
            print(f"Hit {ship}!")
            if len(cells) == 0:
                print(f"Sink {ship}!")
            return True, ship
    print("Miss!")
    return False, None


def display(image_name):
    image = Image.open(image_name)
    image = image.rotate(270, expand=True)
    backlight = digitalio.DigitalInOut(board.D22)
    backlight.switch_to_output()
    backlight.value = True

    # Scale the image to the smaller screen dimension
    image_ratio = image.width / image.height
    screen_ratio = width / height
    if screen_ratio < image_ratio:
        scaled_width = image.width * height // image.height
        scaled_height = height
    else:
        scaled_width = width
        scaled_height = image.height * width // image.width
    image = image.resize((scaled_width, scaled_height), Image.BICUBIC)

    # Crop and center the image
    x = scaled_width // 2 - width // 2
    y = scaled_height // 2 - height // 2
    image = image.crop((x, y, x + width, y + height))

    # Display image.
    disp.image(image, rotation=90)


# main loop
ships = load_ships("ships.csv")  # !!! to build a map for now, comment it when server is implemented

'''
myships = load_ships("ships.csv")
send_map(myships)
ships = read_map()   # opponent map
'''

print("Ship map loaded")
for k, v in ships.items():
    print(f"  {k}: {v}")

turn = True
all_cells = sum(len(v) for v in ships.values())

point_dict = {'A1': [60, 25],
              'A2': [100, 25],
              'A3': [140, 25],
              'A4': [180, 25],
              'B1': [60, 65],
              'B2': [100, 65],
              'B3': [140, 65],
              'B4': [180, 65],
              'C1': [60, 105],
              'C2': [100, 105],
              'C3': [140, 105],
              'C4': [180, 105]}

draw_square('A1', 40)
draw_square('A2', 40)
draw_square('A3', 40)
draw_square('A4', 40)
draw_square('B1', 40)
draw_square('B2', 40)
draw_square('B3', 40)
draw_square('B4', 40)
draw_square('C1', 40)
draw_square('C2', 40)
draw_square('C3', 40)
draw_square('C4', 40)

mqtt.start_mqtt()
PLAYER_ID = "host" if IS_HOST else "client"
if IS_HOST:
    print("You are the host. Starting the game...")
    mqtt.send_message({"action": "start", "player": PLAYER_ID})
else:
    print("You are the client. Waiting for the host to start...")

gameplay = True
turn = IS_HOST  # host starts first

# memorize guess to avoid repeated guesses
guessed_cells = set()
while gameplay:
    if not turn:
        print("Waiting for opponent...")
        msg = mqtt.wait_for_message()
        if not msg:
            continue
        if "sender" in msg and msg["sender"] == PLAYER_ID:
            continue  # ignore own messages

        action = msg.get("action")

        if action == "start":
            print("Game started! Your turn.")
            turn = True

        elif action == "hit":
            print(f"Opponent hit {msg.get('cell')} ({msg.get('ship', '')})!")
            turn = True  # your turn now

        elif action == "miss":
            print(f"Opponent missed at {msg.get('cell')}.")
            turn = True  # your turn now

        elif action == "end":
            print("Game over — you lost!")
            display("defeat.png")
            break

        continue  # go back to loop

        # --- your turn ---
    print("Your turn!")
    guess = wait_for_touch()
    while guess in guessed_cells:
        print("You already guessed that cell. Choose another one.")
        guess = wait_for_touch()
    guessed_cells.add(guess)
    hit, ship = check_hit(guess, ships)

    if hit:
        draw_word(ship, guess)
        mqtt.send_message({"action": "hit", "cell": guess, "ship": ship, "sender": PLAYER_ID})
    else:
        draw_cross(guess, 40)
        mqtt.send_message({"action": "miss", "cell": guess, "sender": PLAYER_ID})

    # --- check for victory ---
    all_cells = sum(len(v) for v in ships.values())
    if all_cells == 0:
        print("You win!")
        display("victory.png")
        mqtt.send_message({"action": "end", "sender": PLAYER_ID})
        gameplay = False
        break

    # end of your turn, now opponent’s turn
    turn = False

mqtt.stop_mqtt()
