import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont

# Button A config
button_A = digitalio.DigitalInOut(board.D23)
button_A.switch_to_input(pull=digitalio.Pull.UP)

# Button B config
button_B = digitalio.DigitalInOut(board.D24)
button_B.switch_to_input(pull=digitalio.Pull.UP)

time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
date_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

weather_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)

def button_a_pressed():
    if button_A.value == False: # False = not pressed, True = pressed
        return True

def button_b_pressed():
    if button_B.value == False:
        return True

def create_time_screen(width, height):
    frame = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(frame)

    current_date = time.strftime("%b %d, %Y")
    current_time = time.strftime("%I:%M %p")

    date_bbox = draw.textbbox((0, 0), current_date, font=date_font)
    date_width = date_bbox[2] - date_bbox[0]

    time_bbox = draw.textbbox((0, 0), current_time, font=time_font)
    time_width = time_bbox[2] - time_bbox[0]

    date_x = (width - date_width) // 2
    time_x = (width - time_width) // 2

    draw.text(
        (date_x, 25),
        current_date,
        font=date_font,
        fill=(0, 0, 0)
    )

    draw.text(
        (time_x, 55),
        current_time,
        font=time_font,
        fill=(0, 0, 0)
    )

    return frame

def get_weather_icon_path(code):
    # Sunny / clear
    if code == 1000:
        return "images/weather/sunny.jpeg"

    # Cloudy / partly cloudy / overcast / fog-like
    elif code in [
        1003, 1006, 1009,
        1030, 1135, 1147
    ]:
        return "images/weather/cloudy.jpeg"

    # Storm / thunder
    elif code in [
        1087, 1273, 1276, 1279, 1282
    ]:
        return "images/weather/stormy.jpeg"

    # Snow / sleet / ice
    elif code in [
        1066, 1069, 1072,
        1114, 1117,
        1204, 1207,
        1210, 1213, 1216, 1219,
        1222, 1225,
        1237,
        1249, 1252,
        1255, 1258,
        1261, 1264
    ]:
        return "images/weather/snowy.jpeg"

    # Everything rainy
    else:
        return "images/weather/rainy.jpeg"

def create_weather_screen(width, height, temperature, condition_code):
    frame = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(frame)

    temperature_text = f"{temperature}°F"

    temp_bbox = draw.textbbox((0, 0), temperature_text, font=weather_font)
    temp_width = temp_bbox[2] - temp_bbox[0]

    icon_path = get_weather_icon_path(condition_code)

    icon = Image.open(icon_path).convert("RGBA")
    icon = icon.resize((45, 45))

    icon_width = 45
    gap = 8

    # Total width of temperature + gap + icon
    total_width = temp_width + gap + icon_width

    # Starting x so the whole group is centered
    start_x = (width - total_width) // 2

    temp_x = start_x
    temp_y = 45

    icon_x = temp_x + temp_width + gap
    icon_y = 45

    draw.text(
        (temp_x, temp_y),
        temperature_text,
        font=weather_font,
        fill=(0, 0, 0)
    )

    frame.paste(icon, (icon_x, icon_y), icon)

    return frame