import time
import board
from adafruit_seesaw import seesaw, rotaryio
import busio
import adafruit_ssd1306
import qwiic_proximity
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import os
import subprocess
import smbus2

# --- I2C ---
i2c = board.I2C()

# --- Rotary encoder ---
seesaw_device = seesaw.Seesaw(i2c, addr=0x36)
encoder = rotaryio.IncrementalEncoder(seesaw_device)
last_encoder_position = encoder.position

# --- OLED ---
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
# I2C addresses for your OLEDs
OLED_ADDR = 0x3C  # default for Qwiic OLED

# I2C buses (hardware + dtoverlay software)
bus_hw = smbus2.SMBus(1)   # /dev/i2c-1
bus_sw13 = smbus2.SMBus(15) # /dev/i2c-13
bus_sw14 = smbus2.SMBus(16) # /dev/i2c-14

# List of buses for iteration
buses = [bus_hw, bus_sw13, bus_sw14]

# SSD1306 display size
WIDTH = 128
HEIGHT = 32
PAGES = HEIGHT // 8

# ---------------------------
# SSD1306 COMMANDS
# ---------------------------

def ssd1306_init(bus):
    cmds = [
        0xAE,       # Display OFF
        0xD5, 0x80, # Set display clock divide ratio
        0xA8, HEIGHT - 1, # Set multiplex
        0xD3, 0x00, # Set display offset
        0x40,       # Set start line
        0x8D, 0x14, # Charge pump
        0x20, 0x00, # Memory addressing mode: horizontal
        0xA1,       # Segment remap
        0xC8,       # COM scan direction
        0xDA, 0x02, # COM pins
        0x81, 0x7F, # Contrast
        0xD9, 0xF1, # Precharge
        0xDB, 0x40, # VCOM detect
        0xA4,       # Display all on resume
        0xA6,       # Normal display
        0xAF        # Display ON
    ]
    for cmd in cmds:
        bus.write_byte_data(OLED_ADDR, 0x00, cmd)

# Initialize all OLEDs
for bus in buses:
    ssd1306_init(bus)


font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)

# draw text function
def draw_text(bus, number):
    # Create monochrome image
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    
    # Draw at top-left
    draw.text((0, 0), str(number), font=font, fill=255)
    
    # Convert image to bytes for SSD1306
    for page in range(PAGES):
        page_bytes = []
        for x in range(WIDTH):
            byte = 0
            for bit in range(8):
                y = page * 8 + bit
                if y >= HEIGHT:
                    continue
                pixel = image.getpixel((x, y))
                if pixel:
                    byte |= (1 << bit)
            page_bytes.append(byte)

        # Send in 32-byte chunks
        for i in range(0, len(page_bytes), 32):
            chunk = page_bytes[i:i+32]
            bus.write_i2c_block_data(OLED_ADDR, 0x40, chunk)


# --- Distance sensor ---
sensor = qwiic_proximity.QwiicProximity()
if not sensor.connected:
    print("VCNL4040 not connected")
    exit(1)
sensor.begin()

# # VCNL4040 command registers (didn't work well)
# PROX_RATE = 0x03
# PROX_DATA_MSB = 0x08
# PROX_DATA_LSB = 0x09
# COMMAND_REG = 0x03

# def read_proximity(bus, addr):
#     # Trigger a single proximity measurement
#     bus.write_byte_data(addr, COMMAND_REG, 0x08)
#     time.sleep(0.01)  # wait 10 ms for measurement

#     # Read 16-bit proximity value
#     msb = bus.read_byte_data(addr, PROX_DATA_MSB)
#     lsb = bus.read_byte_data(addr, PROX_DATA_LSB)
#     return ((msb << 8) | lsb) / 10.0


# --- Time States ---
last_taken = datetime.now() - timedelta(hours=4)
next_time = datetime.now()+ timedelta(seconds=20)
object_present = False
display_mode = 0  # 0 = last_taken, 1 = next_time, 2 = medication name
reminder_spoken = False  # prevents repeated speech

def speak_message(message):
    """Speak a message using espeak."""
    try:
        subprocess.run(["espeak", message], check=True)
    except Exception as e:
        print("Speech error:", e)

while True:
    try:
        now = datetime.now()

        # --- Rotary encoder ---
        current_position = -encoder.position
        if current_position != last_encoder_position:
            display_mode = (display_mode + 1) % 3  # 3 screens
            last_encoder_position = current_position

        # --- Distance sensor ---
        distance_cm = sensor.get_proximity() / 10.0
        print(f"Distance: {distance_cm:.1f} cm")
        currently_present = distance_cm > 10

        # (still didn't work well)
        # distance2 = read_proximity(bus_sw14, 0x60)
        # currently_present2 = distance2 < 10
        # draw_text(bus_sw14, f"S2: {distance2:.1f}cm")

        # update time only when medication taken
        if not currently_present and object_present:
            last_taken = now
            next_time = last_taken + timedelta(minutes=1)
            reminder_spoken = False  # reset for next reminder
            object_present = currently_present
        elif currently_present and not object_present:
            object_present = currently_present

        # --- Speak reminder if time reached ---
        if next_time and not reminder_spoken and now >= next_time:
            speak_message("Please take your Tylenol right now. Please take your Tylenol right now. Please take your Tylenol right now.")
            reminder_spoken = True

        # --- Display ---

        if display_mode == 0:
            draw_text(bus_hw, "Last taken:\n" + last_taken.strftime("%H:%M:%S"))
            draw_text(bus_sw14, "Last taken:\n 10:24:21")
            draw_text(bus_sw13, "Last taken:\n 9:12:10")

        elif display_mode == 1:
            draw_text(bus_hw, "Next time:\n" + next_time.strftime("%H:%M:%S"))
            draw_text(bus_sw14, "Next time:\n 16:24:21")
            draw_text(bus_sw13, "Next time:\n 12:23:01")

        else:
            draw_text(bus_hw, "Medication:\n Tylenol")
            draw_text(bus_sw14, "Medication:\n Advil")
            draw_text(bus_sw13, "Medication:\n Benadryl")

    except Exception as e:
        print("Error:", e)
        oled.fill(0)
        oled.show()

    time.sleep(0.2)