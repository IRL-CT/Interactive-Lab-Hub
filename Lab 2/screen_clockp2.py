import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from time import strftime, localtime, sleep
from datetime import datetime, timedelta
import vlc
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

song_state = {
    "instance": vlc.Instance('--aout=alsa'),
    "media_player": None
}

def play_song(song, state=song_state):
    print(state["media_player"])
    if not state["media_player"]:
        media_player = state["instance"].media_player_new()
        media = state["instance"].media_new(song)
        media_player.set_media(media)
        media_player.audio_set_volume(70)
        media_player.play()
        state["media_player"] = media_player
        state["is_playing"] = True
    
def stop_song(state=song_state):
    if state["media_player"]:
        state["media_player"].pause()
        state["is_playing"] = False
        state["media_player"] = None
        

def volume_up(state=song_state):
    print("Volume")
    if state["media_player"]:
        print("Volume up")
        current_volume = state["media_player"].audio_get_volume()
        print(current_volume)
        new_volume = min(current_volume + 10, 100)  # Clamp max 100
        state["media_player"].audio_set_volume(new_volume)        
        print(state["media_player"].audio_get_volume())
def volume_down(state=song_state):
    print("Volume")
    if state["media_player"]:
        print("Volume down")
        current_volume = state["media_player"].audio_get_volume()
        print(current_volume)
        new_volume = max(current_volume - 10, 0)  # Clamp min 0
        state["media_player"].audio_set_volume(new_volume)  # Use method, not libvlc call
        print("New volume:", state["media_player"].audio_get_volume())

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
# Use internal pull-ups; buttons then read LOW when pressed.
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

lk_background_waiting = Image.open("image/lionkingOpening.jpg").resize((width, height))
lk_background_lottery = Image.open("image/lionkingOpening.jpg").resize((width, height))
lk_background_win_lottery = Image.open("image/lion-king-winner.webp").resize((width, height))
wk_background_waiting = Image.open("image/wicked-waiting.jpg").resize((width, height))
wk_background_lottery = Image.open("image/wicked-lottery.jpg").resize((width, height))
wk_background_win_lottery = Image.open("image/wicked-winner.jpg").resize((width, height))
lk_audio_waiting = "audios/LKHakuna.mp3"
lk_audio_lottery = "audios/LKWait.mp3"
lk_audio_win_lottery = "audios/lionkingOpening.mp3"
wk_audio_waiting = "audios/WickedGood.mp3"
wk_audio_lottery= "audios/WickedDancing.mp3"
wk_audio_win_lottery = "audios/WickedDefy.mp3"

background_waiting = [lk_background_waiting, wk_background_waiting]
background_lottery = [lk_background_lottery, wk_background_lottery]
background_win_lottery = [lk_background_win_lottery, wk_background_win_lottery]
audio_waiting=[lk_audio_waiting, lk_audio_lottery]
audio_lottery=[lk_audio_lottery, wk_audio_lottery]
audio_win=[lk_audio_win_lottery, wk_audio_win_lottery]

lottery_is_open = False
lottery_opens = [9, 20]
lottery_closes = [15, 11]
performance_date_delta = [1,0]
performance_time_list = [19, 19]
win_lottery = False

selected_musical = 0
musicals = ["Lion King", "Wicked"]
buttonA_state = {'pressed': False, 'click_times': []}
buttonB_state = {'pressed':  False, 'click_times': []}
DOUBLE_CLICK_THRESHOLD = 0.5


def check_button(button, button_state, button_name):
    now = datetime.now()

    # Button is pressed (active low)
    if not button.value and not button_state['pressed']:
        button_state['pressed'] = True
        button_state['click_times'].append(now)
        print(f"{button_name} pressed at {now.strftime('%H:%M:%S.%f')}")

    # Button released
    if button.value and button_state['pressed']:
        button_state['pressed'] = False

    # Detect double click
    if len(button_state['click_times']) == 2:
        if (button_state['click_times'][1] - button_state['click_times'][0]).total_seconds() <= DOUBLE_CLICK_THRESHOLD:
            button_state['click_times'] = []  # Reset after double click
            print(f"{button_name} DOUBLE click detected")
            return "double"
        else:
            button_state['click_times'].pop(0)

    # Detect single click only if enough time has passed without second click
    if len(button_state['click_times']) == 1:
        elapsed = (now - button_state['click_times'][0]).total_seconds()
        if elapsed > DOUBLE_CLICK_THRESHOLD:
            button_state['click_times'] = []  # Reset after single click
            print(f"{button_name} SINGLE click detected")
            return "single"

    return None

last_audio_played = None
while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=400)
    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)
    now = datetime.now()
    clickA = check_button(buttonA, buttonA_state, "Button A")
    clickB = check_button(buttonB, buttonB_state, "Button B")
    both_pressed = a_pressed and b_pressed


    if clickA == "single":
        print("Single click detected on Button A")
        selected_musical = (selected_musical + 1) % len(musicals)
    elif clickA == "double":
        print("Double click detected on Button A")
        volume_up(song_state)
    
    if clickB == "single":
        print("Single click detected on Button B")
        selected_musical = (selected_musical - 1) % len(musicals)
    elif clickB == "double":
        print("Double click detected on Button B")
        volume_down(song_state)
        
    if last_audio_played != audio_waiting[selected_musical]:
        stop_song(song_state)
        play_song(audio_waiting[selected_musical])
        last_audio_played = audio_waiting[selected_musical]
        
    if win_lottery:
        background_to_show = background_win_lottery[selected_musical]
    elif now.hour < lottery_closes[selected_musical]:
        background_to_show = background_lottery[selected_musical]
    else:
        print("Waiting background")
        background_to_show = background_waiting[selected_musical]
    
    image.paste(background_to_show, (0, 0))

        
# Now actually paste the chosen background once
# image.paste(background_to_show, (0, 0))
    if both_pressed:
        win_lottery = True
        target = datetime.now() + timedelta(hours=1) 
    else:
        if win_lottery is True:
            remaining = target - now
            if remaining.total_seconds() <= 0:
            # hours, minutes, seconds = 0, 0, 0
                win_lottery = False
            else:
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                countdown = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                draw.text((10, top+5), "Countdown (1hr):", font=font, fill=(255, 255, 255))
                draw.text((10, top + 30), countdown, font=font, fill=(255, 255, 255))

        
        
        # image.paste(background_waiting[selected_musical], (0, 0))
        
        # 
            
    if win_lottery is False:
        # if a_pressed and not b_pressed:
        #     selected_musical = (selected_musical + 1) % len(musicals)
        # if b_pressed and not a_pressed:
        #     selected_musical = (selected_musical - 1) % len(musicals)
       
        # image.paste(background_waiting[selected_musical], (0,0))
        target = now.replace(hour=lottery_opens[selected_musical], minute=0, second=0, microsecond=0)
        
        if now.hour < lottery_closes[selected_musical]: 
            target = now.replace(hour=lottery_closes[selected_musical], minute=0, second=0, microsecond=0)
            # image.paste(background_lottery[selected_musical], (0,0))
            lottery_is_open = True
        # if it's past 3pm, set target to 9 AM tomorrow
        if now.hour >= lottery_closes[selected_musical]: 
            lottery_is_open = False
            target += timedelta(days=1)
        # Performance = next day at 7:00 PM
        performance_time = (now + timedelta(days=performance_date_delta[selected_musical])).replace(hour=performance_time_list[selected_musical], minute=0, second=0, microsecond=0)
        
        # Calculate remaining time
        remaining = target - now

        # Break it into hours/minutes/seconds
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Format nicely
        waiting_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Draw it on your canvas
        # draw.text((15, top), day_name, font=font, fill=(255, 255, 255))
        if lottery_is_open is False:
            draw.text((10, top+5), "Countdown to Lottery:", font=font, fill=(255, 255, 255))
            draw.text((20, top + 30), waiting_time, font=font, fill=(255, 255, 255))
        else: 
            flash = not flash
            draw.text((10, top+5), "Lottery Opens Until:", font=font, fill=(255, 255, 255))

            if flash:
                draw.text((20,  top + 30), waiting_time, font=font, fill=(255, 255, 255))
       
        draw.text((10, height //2 +10), "Next Performance:", font=font, fill=(255, 255, 255))
        draw.text((20, height //2 + 30), performance_time.strftime("%Y-%m-%d %H:%M"), font=font, fill=(255, 255, 255))
    
    # Display image.
    disp.image(image, rotation)
    print("Image sent to display at", datetime.now())

    time.sleep(.1)