import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import random
import datetime
import math

# === Screen ===
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

# === Fonts ===
font_normal = ImageFont.truetype("/home/pi/Interactive-Lab-Hub/Lab 2/fonts/dogica/dogicapixel.ttf", 11)
font_big = ImageFont.truetype("/home/pi/Interactive-Lab-Hub/Lab 2/fonts/dogica/dogicapixelbold.ttf", 14)
font_history = ImageFont.truetype("/home/pi/Interactive-Lab-Hub/Lab 2/fonts/determination.ttf", 14)

# === Button ===
buttonA = digitalio.DigitalInOut(board.D23)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB = digitalio.DigitalInOut(board.D24)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# === Word lists ===
MORNING_WORDS = ["WAKE", "COFFEE", "SUNRISE", "FRESH", "ENERGY", "BRIGHT", "MORNING", "START", "NEW"]
DAY_WORDS = ["WORK", "LUNCH", "FOCUS", "TASK", "MEETING", "EMAIL", "PROJECT", "CODE", "STUDY", "PRODUCTIVE"]
EVENING_WORDS = ["DINNER", "RELAX", "REST", "MOVIE", "FAMILY", "WALK", "CHAT", "HOBBY", "CALM", "ENJOY", "RECHARGE"]
NIGHT_WORDS = ["DREAM", "SILENCE", "SLEEP", "QUIET", "STARS", "MOON", "NIGHT", "PEACE", "RESTFUL", "COZY"]
TIME_WORDS_MAP = {
    "MORNING": MORNING_WORDS,
    "DAY": DAY_WORDS,
    "EVENING": EVENING_WORDS,
    "NIGHT": NIGHT_WORDS
}

# === Color palette ===
TIME_COLORS_MAP = {
    "MORNING": ("#ffc971", "#ff9505", "#cc5803"),  # main, sub, background
    "DAY": ("#6FD587", "#38a3a5", "#22577a"),
    "EVENING": ("#ffcdb2", "#e5989b", "#b5838d"),
    "NIGHT": ("#b298dc", "#6f2dbd", "#360568")
}

# === MODE ===
MODE_NORMAL = "NORMAL"
MODE_HISTORY = "HISTORY"
MODE_DODGE = "DODGE"

mode = MODE_NORMAL
last_button_press_time = {"A": 0, "B": 0}
BUTTON_DEBOUNCE = 0.2


NORMAL_MODES = [MODE_NORMAL, MODE_HISTORY]
normal_mode_index = 0

# === Dodge game setting ===
player_y = height // 2
obstacles = []
score = 0
game_over = False
last_obstacle_time = 0
game_start_time = 0

# === History Fact ===
history_facts = [
    "The first mechanical clock was invented in 13th century Europe.",
    "The Gregorian calendar was introduced in 1582 by Pope Gregory XIII.",
    "The word 'clock' comes from the Celtic words 'clocca' and 'clagan' meaning bell.",
    "Big Ben's clock tower was completed in 1859.",
    "According to Einstein's theory of relativity, time passes slower when you move faster.",
    "The atomic clock is the most accurate timekeeping device, losing only one second every 300 million years.",
    "The concept of time zones was proposed by Sir Sandford Fleming in 1879.",
    "The Mayan calendar predicted the end of the world in 2012, which did not happen.",
    "The Moon's gravity makes days longer.",
    "While the Great Pyramids were being built, Mammoths still walked the Earth.",
    "Oxford University existed centuries before the Aztec Empire was founded.",
    "The Ottoman Empire was still around when Walt Disney released his first cartoons."
]
current_history_fact = random.choice(history_facts)


# === Time frame ===
def get_time_of_day():
    hour = datetime.datetime.now().hour
    if 6 <= hour < 12:
        return "MORNING"
    elif 12 <= hour < 17:
        return "DAY"
    elif 17 <= hour < 22:
        return "EVENING"
    else:
        return "NIGHT"

def get_routine_words():
    time_of_day = get_time_of_day()
    words_list = TIME_WORDS_MAP.get(time_of_day, [])
    
    if len(words_list) < 3:
        return words_list
    
    return random.sample(words_list, 3)

def init_word_cloud():
    routine_words = get_routine_words()
    random_words = ["".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=random.randint(3, 7)))
                    for _ in range(15)]
    words = routine_words + random_words
    positions = [[random.randint(0, width - 30), random.randint(0, height - 10)] for _ in words]
    velocities = [[random.uniform(-1, 1), random.uniform(-1, 1)] for _ in words]
    is_routine = [i < len(routine_words) for i in range(len(words))]
    return words, positions, velocities, is_routine

words, positions, velocities, is_routine = init_word_cloud()

# === NORMAL Mode ===
def draw_normal(main_color, normal_color, background_color):
    global words, positions, velocities, is_routine, current_history_fact
    draw.rectangle((0, 0, width, height), outline=0, fill=background_color)

    if mode == MODE_NORMAL:
        speed = 1
        for i, word in enumerate(words):
            x, y = positions[i]
            dx, dy = velocities[i]
            w = draw.textlength(word, font=font_normal)
            h = font_normal.size
    
            if x < 0: dx = abs(dx)
            if x > width - w: dx = -abs(dx)
            if y < 0: dy = abs(dy)
            if y > height - h: dy = -abs(dy)
    
            x += dx * speed
            y += dy * speed
            positions[i] = [x, y]
            velocities[i] = [dx, dy]
    
            if is_routine[i]:
                draw.text((x, y), word, font=font_big, fill=main_color)
            else:
                draw.text((x, y), word, font=font_normal, fill=normal_color)

 # === HISTORY Mode ===               
    elif mode == MODE_HISTORY:
        lines = []
        current_line = ""
        for word in current_history_fact.split():
            if not current_line:
                current_line = word
            elif draw.textlength(current_line + " " + word, font=font_history) < width - 10:
                current_line += " " + word
            else:
                lines.append(current_line.strip())
                current_line = word
        lines.append(current_line.strip())

        y_offset = height // 2 - (len(lines) * font_history.size) // 2
        
        for line in lines:
            text_w = draw.textlength(line, font=font_history)
            x_pos = (width - text_w) // 2
            draw.text((x_pos, y_offset), line, font=font_history, fill=main_color)
            y_offset += font_history.size + 4 

# === DODGE Mode ===
def draw_dodge(main_color, normal_color, background_color):
    global player_y, obstacles, score, game_over, last_obstacle_time

    draw.rectangle((0, 0, width, height), outline=0, fill=background_color)

    # Player character
    now = datetime.datetime.now()
    player_word = now.strftime("%I:%M") 
    draw.text((10, player_y), player_word, font=font_normal, fill=main_color)
    pw = draw.textlength(player_word, font=font_normal)
    ph = font_normal.size
    player_box = (10, player_y, 10 + pw, player_y + ph)

    # Generate new obstacless
    if time.time() - last_obstacle_time > 1:
        last_obstacle_time = time.time()
        word = random.choice(get_routine_words())
        oy = random.randint(0, height - 10)
        obstacles.append([width, oy, word])

    # Update the obstacles
    new_obstacles = []
    for ox, oy, word in obstacles:
        ox -= 5
        if ox > -30:
            new_obstacles.append([ox, oy, word])
            draw.text((ox, oy), word, font=font_big, fill=normal_color)
            # Collision
            ow = draw.textlength(word, font=font_big)
            oh = font_big.size
            obstacle_box = (ox, oy, ox + ow, oy + oh)
            if (player_box[0] < obstacle_box[2] and player_box[2] > obstacle_box[0] and
                player_box[1] < obstacle_box[3] and player_box[3] > obstacle_box[1]):
                game_over = True
    obstacles = new_obstacles

    # Scoring
    if not game_over:
        elapsed = int(time.time() - game_start_time)
        score = elapsed
        draw.rectangle((width - 78, 3, width, 18), fill=main_color)
        draw.text((width - 74, 6), 'SCORE:', font=font_normal, fill=normal_color)
        draw.text((width - 20, 6), str(score), font=font_normal, fill=normal_color)
    else:
        # Game Over
        draw.rectangle((width // 2 - 48, height // 2 - 4, width // 2 + 62, height // 2 + 16), fill=main_color)
        draw.text((width // 2 - 44, height // 2), "SCORE:", font=font_big, fill=normal_color)
        draw.text((width // 2 + 32, height // 2), str(score), font=font_big, fill=normal_color)
        disp.image(image, rotation)
        time.sleep(2)
        reset_game()

def reset_game():
    global mode, obstacles, score, game_over, player_y, game_start_time, normal_mode_index
    mode = MODE_NORMAL
    normal_mode_index = 0
    obstacles = []
    score = 0
    game_over = False
    player_y = height // 2
    game_start_time = 0
    # reset word cloud
    global words, positions, velocities, is_routine
    words, positions, velocities, is_routine = init_word_cloud()
    # reset history fact
    global current_history_fact
    current_history_fact = random.choice(history_facts)


# === Main Loop ===
while True:
    a_pressed = not buttonA.value
    b_pressed = not buttonB.value
    now = time.time()

    # Set color palette based on time of day
    time_of_day = get_time_of_day()
    main_color, normal_color, background_color = TIME_COLORS_MAP.get(time_of_day)


    # Reset to Normal mode
    if a_pressed and b_pressed and (now - last_button_press_time["A"]) > BUTTON_DEBOUNCE and (now - last_button_press_time["B"]) > BUTTON_DEBOUNCE:
        last_button_press_time["A"] = now
        last_button_press_time["B"] = now
        reset_game()

    elif a_pressed and (now - last_button_press_time["A"]) > BUTTON_DEBOUNCE:
        last_button_press_time["A"] = now
        if mode == MODE_DODGE:
            player_y = max(0, player_y - 10)
        else:
            normal_mode_index = (normal_mode_index + 1) % len(NORMAL_MODES)
            mode = NORMAL_MODES[normal_mode_index]
            words, positions, velocities, is_routine = init_word_cloud()
            if mode == MODE_HISTORY:
                current_history_fact = random.choice(history_facts)

    elif b_pressed and (now - last_button_press_time["B"]) > BUTTON_DEBOUNCE:
        last_button_press_time["B"] = now
        if mode in NORMAL_MODES:
            mode = MODE_DODGE
            game_start_time = time.time()
        elif mode == MODE_DODGE:
            player_y = min(height - 20, player_y + 10)

    if mode in NORMAL_MODES:
        draw_normal(main_color, normal_color, background_color)
    elif mode == MODE_DODGE:
        draw_dodge(main_color, normal_color, background_color)

    disp.image(image, rotation)
    time.sleep(0.05)
