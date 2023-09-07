# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# -*- coding: utf-8 -*-

import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789


# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.CE0)
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
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Button configuration
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input()
buttonB.switch_to_input()

mac_scroll_position = 0
cpu_mem_disk_scroll_position = 0

while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Check button presses
    if not buttonA.value:  # Button A pressed (power off)
        draw.text((0, 0), "Shutdown " * 10, font=font, fill="#FF0000")
        disp.image(image, rotation)
        subprocess.run(['sudo', 'poweroff'])
    elif not buttonB.value:  # Button B pressed (restart)
        draw.text((0, 0), "Reboot " * 10, font=font, fill="#0000FF")
        disp.image(image, rotation)
        subprocess.run(['sudo', 'reboot'])

    y = top

    # IP Address
    cmd = "hostname -I | cut -d' ' -f1"
    IP = "IP: " + subprocess.check_output(cmd, shell=True).decode("utf-8")
    draw.text((x, y), IP, font=font, fill="#FFFFFF")
    y += font.getsize(IP)[1]

    # Network Name
    try:
        cmd = "iwgetid -r"
        Network = "Net: " + subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        Network = "Net: Error fetching network name"


    draw.text((x, y), Network, font=font, fill="#FFFFFF")
    y += font.getsize(Network)[1]


    # MAC Address
    MAC = "MAC: " + subprocess.check_output("cat /sys/class/net/eth0/address", shell=True).decode("utf-8").strip()
    draw.text((x - mac_scroll_position, y), MAC, font=font, fill="#FFFFFF")
    y += font.getsize(MAC)[1]
    mac_scroll_position = (mac_scroll_position + 5) % font.getsize(MAC)[0]

    # CPU Usage, Memory and Disk Usage
    CPU = subprocess.check_output("top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'", shell=True).decode("utf-8")
    MemUsage = subprocess.check_output("free -m | awk 'NR==2{printf \"Mem: %s/%s MB  %.2f%%\", $3,$2,$3*100/$2 }'", shell=True).decode("utf-8")
    Disk = subprocess.check_output('df -h | awk \'$NF=="/"{printf "Disk: %d/%d GB  %s", $3,$2,$5}\'', shell=True).decode("utf-8")
    CPUMemDisk = CPU + "  |  " + MemUsage + "  |  " + Disk
    draw.text((x - cpu_mem_disk_scroll_position, y), CPUMemDisk, font=font, fill="#00FF00")
    y += font.getsize(CPUMemDisk)[1]
    cpu_mem_disk_scroll_position = (cpu_mem_disk_scroll_position + 5) % font.getsize(CPUMemDisk)[0]

    # CPU Temperature
    Temp = subprocess.check_output("cat /sys/class/thermal/thermal_zone0/temp |  awk '{printf \"CPU Temp: %.1f C\", $(NF-0) / 1000}'", shell=True).decode("utf-8")
    draw.text((x, y), Temp, font=font, fill="#FF00FF")

    # Display image.
    disp.image(image, rotation)
    time.sleep(0.2)  # Adjust the speed of the scrolling text


