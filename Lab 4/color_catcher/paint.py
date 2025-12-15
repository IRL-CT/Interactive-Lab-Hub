# MiniPiTFT joystick painter + APDS9960 color brush
import os, time, sys
from PIL import Image, ImageDraw

# ------- Hardware libs -------
import qwiic_joystick
import board, digitalio, busio
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
from adafruit_seesaw import seesaw as ss_mod, rotaryio as srotaryio, digitalio as sdio
from adafruit_apds9960.apds9960 import APDS9960
import adafruit_mpr121

# ------- Audio (VLC) -------
import vlc

# ------- Display backends -------
# Toggle this: False -> Pygame desktop window (easy with RealVNC)
#               True  -> MiniPiTFT ST7789
USE_TFT = False
ROTATION = 90

# Canvas and scaling settings
# Option 1: Small canvas, scaled up (good for lower-end phones)
# W, H = 440, 250
# SCALE = 2

# Option 2: Medium canvas, scaled up (balanced)
# W, H = 600, 338
# SCALE = 2

# Option 3: Full phone resolution (best quality, no scaling needed)
# Common phone resolutions:
# - 1080p: 1920x1080 (landscape) or 1080x1920 (portrait)
# - 720p:  1280x720 (landscape) or 720x1280 (portrait)
# For landscape display via VNC:
W, H = 1280, 720           # 720p landscape
SCALE = 1                  # No upscaling needed

# If your phone screen is different, adjust W and H to match
# To find your phone resolution, you can check your VNC viewer settings

# ============================================================
#                      SOUND SETUP (VLC)
# ============================================================
state = {
    "instance": vlc.Instance('--aout=alsa', '--no-video'),
    "media_player": None,
    "current_sound": None
}
draw_sound = "sounds/draw.mp3"
erase_sound = "sounds/eraser.mp3"
sounds = [draw_sound, erase_sound]

def play_sound(song, state=state):
    if state["media_player"] and state["current_sound"] != song:
        state["media_player"].stop()
        state["media_player"].release()
        state["media_player"] = None
    if not state["media_player"]:
        media_player = state["instance"].media_player_new()
        media = state["instance"].media_new(song)
        media.add_option('input-repeat=-1')  # loop
        media_player.set_media(media)
        media_player.audio_set_volume(70)
        media_player.play()
        state["media_player"] = media_player
        state["current_sound"] = song

def pause_sound(state=state):
    if state["media_player"] and state["media_player"].is_playing():
        state["media_player"].pause()

def unpause_sound(state=state):
    if state["media_player"]:
        state["media_player"].play()

def stop_sound(state=state):
    if state["media_player"]:
        state["media_player"].stop()
        state["media_player"].release()
        state["media_player"] = None
        state["current_sound"] = None

# ============================================================
#                      DISPLAY SETUP
# ============================================================
disp = None
screen = None  # pygame screen if USE_TFT == False

if USE_TFT:
    import adafruit_rgb_display.st7789 as st7789
    cs_pin = digitalio.DigitalInOut(board.D5)
    dc_pin = digitalio.DigitalInOut(board.D25)
    reset_pin = None
    BAUDRATE = 64_000_000
    spi = board.SPI()
    disp = st7789.ST7789(
        spi, cs=cs_pin, dc=dc_pin, rst=reset_pin, baudrate=BAUDRATE,
        width=135, height=240, x_offset=53, y_offset=40
    )
else:
    import pygame
    pygame.init()
    pygame.display.set_caption("Pi Painter")
    screen = pygame.display.set_mode((W * SCALE, H * SCALE))

def push_frame(pil_img):
    """Show current frame on the selected output."""
    if USE_TFT:
        disp.image(pil_img, ROTATION)
    else:
        # Handle app close events so window remains responsive
        import pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        img = pil_img.rotate(ROTATION, expand=True)
        if img.mode != "RGB":
            img = img.convert("RGB")
        surf = pygame.image.frombuffer(img.tobytes(), img.size, "RGB")
        disp_surf = pygame.transform.scale(surf, (W * SCALE, H * SCALE))
        screen.blit(disp_surf, (0, 0))
        pygame.display.flip()

# ============================================================
#                      CANVAS INIT
# ============================================================
background_color = (0, 0, 0)           # RGB (not RGBA)
img = Image.new("RGB", (W, H), background_color)
draw = ImageDraw.Draw(img)
push_frame(img)

# ============================================================
#                      INPUT DEVICES
# ============================================================
# I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Touch (MPR121)
mpr121 = adafruit_mpr121.MPR121(i2c)

# IMU (LSM6DS3)
sensor = LSM6DS3(i2c)

# Qwiic Joystick
js = qwiic_joystick.QwiicJoystick()
if not js.connected:
    print("Qwiic Joystick not found.", file=sys.stderr); sys.exit(1)
js.begin()

# Seesaw Encoder (0x36)
ss = ss_mod.Seesaw(board.I2C(), addr=0x36)
prod = (ss.get_version() >> 16) & 0xFFFF
print(f"Seesaw product: {prod}")
ss.pin_mode(24, ss.INPUT_PULLUP)
enc_button = sdio.DigitalIO(ss, 24)
encoder = srotaryio.IncrementalEncoder(ss)
last_position = encoder.position

# APDS9960 color
apds = APDS9960(board.I2C())
apds.enable_color = True

# ============================================================
#                      STATE
# ============================================================
x, y = W // 2, H // 2
prev_x, prev_y = x, y  # Track previous position for smooth lines
brush = 4
brush_type = "circle"
auto_color = True
curr_color = (255, 255, 255)
prev_js_btn = 1
isDrawing = False
isErasing = False
last_audio_played = None

def clamp(v, lo, hi): return max(lo, min(hi, v))

def rot_vec(dx, dy, rot):
    r = rot % 360
    if r == 0:   return dx, dy
    if r == 90:  return dy, -dx
    if r == 180: return -dx, -dy
    if r == 270: return -dy, dx
    return dx, dy

def rgb_from_apds(r, g, b, c):
    if c <= 0:
        return (0, 0, 0)
    rn = int(255 * r / c)
    gn = int(255 * g / c)
    bn = int(255 * b / c)
    return (clamp(rn, 0, 255), clamp(gn, 0, 255), clamp(bn, 0, 255))

def lerp(a, b, t): return int(a + (b - a) * t)

def smooth_rgb(old, new, alpha=0.3):
    return (lerp(old[0], new[0], alpha),
            lerp(old[1], new[1], alpha),
            lerp(old[2], new[2], alpha))

def invert_color(color):
    """Return the inverted color for visibility"""
    return (255 - color[0], 255 - color[1], 255 - color[2])

def draw_pointer(display_img, x, y, brush_size, color, is_drawing):
    """Draw a pointer/cursor on the display image"""
    temp_draw = ImageDraw.Draw(display_img)
    pointer_color = invert_color(background_color)
    
    # Draw crosshair
    crosshair_size = 10
    temp_draw.line((x - crosshair_size, y, x + crosshair_size, y), fill=pointer_color, width=1)
    temp_draw.line((x, y - crosshair_size, x, y + crosshair_size), fill=pointer_color, width=1)
    
    # Draw brush preview circle
    if is_drawing:
        # Show brush size with current color
        preview_color = color
    else:
        # Show brush size with inverted background color
        preview_color = pointer_color
    
    bx1, by1 = x - brush_size, y - brush_size
    bx2, by2 = x + brush_size, y + brush_size
    temp_draw.ellipse((bx1, by1, bx2, by2), outline=preview_color, width=2)

# Ensure save directory exists
os.makedirs("drawing", exist_ok=True)

try:
    while True:
        # ----- accelerometer read -----
        accel_x, accel_y, accel_z = sensor.acceleration

        # ----- joystick movement -----
        jx = js.horizontal   # 0..1023
        jy = js.vertical
        js_btn = js.button   # 0 when pressed

        # Deadzone + scale
        dead = 40
        raw_dx = jx - 512
        raw_dy = jy - 512
        if abs(raw_dx) < dead: raw_dx = 0
        if abs(raw_dy) < dead: raw_dy = 0

        sens = 64.0
        dx, dy = int(raw_dx / sens), int(raw_dy / sens)
        dx, dy = rot_vec(dx, dy, ROTATION)

        # Sound logic
        if (dx != 0 or dy != 0):
            if isDrawing and not isErasing:
                if last_audio_played != 'draw':
                    last_audio_played = 'draw'
                    play_sound(sounds[0])
                else:
                    unpause_sound()
            elif isErasing:
                if last_audio_played != 'erase':
                    last_audio_played = 'erase'
                    play_sound(sounds[1])
                else:
                    unpause_sound()
        else:
            if last_audio_played is not None:
                pause_sound()

        # Cursor move
        old_x, old_y = x, y
        x = clamp(x + dx, 0, W - 1)
        y = clamp(y + dy, 0, H - 1)

        # JS button: toggle draw on press edge
        if prev_js_btn == 1 and js_btn == 0:
            isDrawing = not isDrawing
            if isDrawing and apds.color_data_ready:
                r, g, b, c = apds.color_data
                sensed = rgb_from_apds(r, g, b, c)
                curr_color = smooth_rgb(curr_color, sensed, 0.35)
            print(f"ON with color {curr_color}" if isDrawing else "OFF")
        prev_js_btn = js_btn

        # Encoder brush size
        pos = encoder.position
        if pos != last_position:
            diff = pos - last_position
            last_position = pos
            brush = clamp(brush + diff, 1, 30)
            print(f"Brush: {brush}")

        # Clean when the accelerometer is tilted forward
        # NOTE: if your forward is +Y, "tilted forward" makes Ay negative
        if accel_y < 0.0:
            img.paste((0,0,0), [0, 0, img.size[0], img.size[1]])
            print("Canvas cleared")
            time.sleep(0.5)  # debounce

        # Choose brush color every frame (safe default)
        brush_color = curr_color

        # MPR121 touch options
        for i in range(12):
            if mpr121[i].value:
                if i == 6:
                    # ERASE mode
                    print("ERASING")
                    auto_color = False
                    brush_color = (0,0,0)
                    isErasing = True

                if i == 3:
                    print("DRAWING")
                    isErasing = False
                    auto_color = True
                    brush_type = "circle" if brush_type == "rectangle" else "rectangle"
                    print(f"Brush type: {brush_type}")

                if i == 5:
                    # SAVE
                    path = f"drawing/my_drawing_{int(time.time())}.png"
                    img.save(path)
                    print(f"Image saved to {path}")

                if i == 8:
                    # SET background = current color and clear
                    background_color = brush_color
                    img.paste(background_color, [0, 0, img.size[0], img.size[1]])
                    print("Background color set")

                time.sleep(0.3)  # debounce

        # Draw
        if isDrawing and (dx != 0 or dy != 0):  # Only draw when moving
            # keep eraser color if isErasing
            if isErasing:
                brush_color = (0,0,0)
            elif auto_color and apds.color_data_ready:
                # gentle periodic color refresh while drawing
                r, g, b, c = apds.color_data
                sensed = rgb_from_apds(r, g, b, c)
                curr_color = smooth_rgb(curr_color, sensed, 0.25)
                brush_color = curr_color

            # Draw line from previous position to current position for smooth strokes
            if brush_type == "rectangle":
                # For rectangle, draw at current position
                bx1, by1, bx2, by2 = x - brush, y - brush, x + brush, y + brush
                draw.rectangle((bx1, by1, bx2, by2), outline=brush_color, width=brush)
            else:
                # For circle, draw a line with circular brush
                draw.line((old_x, old_y, x, y), fill=brush_color, width=brush * 2)

        # Create display image with pointer overlay
        display_img = img.copy()
        draw_pointer(display_img, x, y, brush, brush_color, isDrawing)
        
        # Push frame with pointer
        push_frame(display_img)
        time.sleep(0.016)  # ~60 FPS

except KeyboardInterrupt:
    pass
finally:
    stop_sound()
    if not USE_TFT:
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass