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
is_playing = False
instance = vlc.Instance('--aout=alsa')

def play_song(song):
    m = instance.media_new(song)
    media_player.set_media(m)
    media_player.audio_set_volume(70)
    media_player.play()
    is_playing = True

def stop_song(p):
    if is_playing:
        p.pause()
def volume_up(p):
    current_volume = p.audio_get_volume()
    vlc.libvlc_audio_set_volume(p, current_volume+10)
def volume_down(p):
    current_volume = p.audio_get_volume()
    vlc.libvlc_audio_set_volume(p, current_volume-10)

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
lk_background_lottery = Image.open("image/lionking-blue.jpg").resize((width, height))
lk_background_win_lottery = Image.open("image/lion-king-winner.webp").resize((width, height))
wk_background_waiting = Image.open("image/wicked-waiting.jpg").resize((width, height))
wk_background_lottery = Image.open("image/wicked-lottery.jpg").resize((width, height))
wk_background_win_lottery = Image.open("image/wicked-winner.jpg").resize((width, height))
lk_audio_waiting = "audios/LKCircle.mp3"
lk_audio_lottery = "audios/LKWait.mp3"
lk_audio_win_lottery = "audios/LKHakuna.mp3"
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

while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=400)
    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)
    now = datetime.now()

    if a_pressed and b_pressed:
        win_lottery = True
        image.paste(background_waiting[selected_musical], (0,0))
        target = datetime.now() + timedelta(seconds=10)
        # target = datetime.now() + timedelta(hours=10)

    if win_lottery is True: 
        remaining = target - now
        image.paste(background_win_lottery[selected_musical], (0,0))
        play_song(lk_audio_win_lottery[selected_musical])
        if remaining.total_seconds() <= 0:
            # hours, minutes, seconds = 0, 0, 0
            win_lottery = False
        else:
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            countdown = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            draw.text((10, top+5), "Countdown (1hr):", font=font, fill=(255, 255, 255))
            draw.text((10, top + 30), countdown, font=font, fill=(255, 255, 255))

    if win_lottery is False:
        if a_pressed and not b_pressed:
            selected_musical = (selected_musical + 1) % len(musicals)
        if b_pressed and not a_pressed:
            selected_musical = (selected_musical - 1) % len(musicals)

        image.paste(background_waiting[selected_musical], (0,0))
        # Target time (9:00 AM today) for the lottery to be opened next
        target = now.replace(hour=lottery_opens[selected_musical], minute=0, second=0, microsecond=0)
        # if it's past 9 AM but before 3pm, set target to 3 PM today
        if now.hour < lottery_closes[selected_musical]: 
            target = now.replace(hour=lottery_closes[selected_musical], minute=0, second=0, microsecond=0)
            image.paste(background_lottery[selected_musical], (0,0))
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
            draw.text((10, top+5), "Lottery Opens Until:", font=font, fill=(255, 255, 255))
            draw.text((20,  top + 30), waiting_time, font=font, fill=(255, 255, 255))
       
        draw.text((10, height //2 +10), "Next Performance:", font=font, fill=(255, 255, 255))
        draw.text((20, height //2 + 30), performance_time.strftime("%Y-%m-%d %H:%M"), font=font, fill=(255, 255, 255))

    # Display image.
    disp.image(image, rotation)
    time.sleep(1)
