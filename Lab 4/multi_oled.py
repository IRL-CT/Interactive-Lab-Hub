# import smbus2
# from PIL import Image, ImageDraw, ImageFont
# import time

# # --- I2C addresses ---
# OLED_HW_ADDR   = 0x3C  # Hardware I2C
# OLED_SW15_ADDR = 0x3C  # Software I2C bus 15
# OLED_SW16_ADDR = 0x3C  # Software I2C bus 16

# # --- Open I2C buses ---
# bus_hw   = smbus2.SMBus(1)    # Hardware I2C
# # bus_sw15 = smbus2.SMBus(15)   # Software bus 15
# bus_sw16 = smbus2.SMBus(16)   # Software bus 16

# # --- SSD1306 init for 128x32 OLED ---
# def ssd1306_init(bus, addr):
#     cmds = [
#         0xAE,       # Display OFF
#         0xD5, 0x80, # Set display clock divide
#         0xA8, 0x1F, # Set multiplex to 31 (32 rows)
#         0xD3, 0x00, # Set display offset
#         0x40,       # Set start line
#         0x8D, 0x14, # Charge pump
#         0x20, 0x00, # Memory addressing mode: horizontal
#         0xA1,       # Segment remap
#         0xC8,       # COM scan direction
#         0xDA, 0x02, # COM pins hardware config
#         0x81, 0x7F, # Contrast
#         0xD9, 0xF1, # Precharge
#         0xDB, 0x40, # VCOM detect
#         0xA4,       # Display RAM
#         0xA6,       # Normal display
#         0xAF        # Display ON
#     ]
#     for cmd in cmds:
#         bus.write_byte_data(addr, 0x00, cmd)

# # --- Clear display ---
# def clear_display(bus, addr):
#     for page in range(4):  # 32 pixels = 4 pages
#         bus.write_byte_data(addr, 0xB0 + page, 0x00)
#         for col in range(128):
#             bus.write_byte_data(addr, 0x40, 0x00)

# # --- Draw TTF text to buffer ---
# def text_to_buffer(text, font_path="DejaVuSans-Bold.ttf", font_size=16):
#     font = ImageFont.truetype(font_path, font_size)
#     img = Image.new("1", (128, 32), color=0)  # Monochrome
#     draw = ImageDraw.Draw(img)
#     draw.text((0, 0), text, font=font, fill=1)
    
#     # Convert to SSD1306 buffer (4 pages × 128 columns)
#     buffer = []
#     for page in range(0, 32, 8):
#         for x in range(128):
#             byte = 0
#             for bit in range(8):
#                 y = page + bit
#                 if y >= 32:
#                     continue
#                 pixel = img.getpixel((x, y))
#                 byte |= (1 if pixel else 0) << bit
#             buffer.append(byte)
#     return buffer

# # --- Write buffer to OLED ---
# def write_buffer(bus, addr, buffer):
#     for page in range(4):
#         bus.write_byte_data(addr, 0xB0 + page, 0x00)
#         for col in range(128):
#             bus.write_byte_data(addr, 0x40, buffer[page*128 + col])

# # --- Initialize all OLEDs ---
# for bus, addr in [(bus_hw, OLED_HW_ADDR),
#                 #   (bus_sw15, OLED_SW15_ADDR),
#                   (bus_sw16, OLED_SW16_ADDR)]:
#     ssd1306_init(bus, addr)
#     clear_display(bus, addr)

# # --- Write different text to each screen ---
# texts = ["HW OLED", "SW15 OLED", "SW16 OLED"]
# buses = [bus_hw, bus_sw16]
# addrs = [OLED_HW_ADDR, OLED_SW15_ADDR, OLED_SW16_ADDR]

# for bus, addr, text in zip(buses, addrs, texts):
#     buf = text_to_buffer(text, font_size=16)
#     write_buffer(bus, addr, buf)

# print("All OLEDs updated with TTF text!")


import smbus2
from PIL import Image, ImageDraw, ImageFont
import time

# ---------------------------
# CONFIGURATION
# ---------------------------

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

# ---------------------------
# DRAW NUMBERS
# ---------------------------
# Load font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)

def draw_text(bus, number):
    # Create monochrome image
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    
    # Draw number at top-left
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
# ---------------------------
# TEST LOOP
# ---------------------------
# Draw different numbers on each OLED
draw_text(bus_sw14, "hello")
draw_text(bus_sw13, "hi")
draw_text(bus_hw, 5678)