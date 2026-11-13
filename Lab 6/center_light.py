# Center Pi: counts break votes over MQTT and shows the result on the Mini PiTFT.
# Top button = my own vote. Run: python center_light.py 4
import sys, time, board, digitalio
import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

TEAM = "IDD/huadiweilao"
NEEDED = int(sys.argv[1]) if len(sys.argv) > 1 else 4   # votes needed for a break
VOTE_TTL = 60        # a vote counts for 60 seconds
BREAK_SECONDS = 10   # how long the break signal stays on

# Mini PiTFT screen used as a big light
bl = digitalio.DigitalInOut(board.D22); bl.switch_to_output(); bl.value = True
button = digitalio.DigitalInOut(board.D23); button.switch_to_input(pull=digitalio.Pull.UP)
disp = st7789.ST7789(board.SPI(), cs=digitalio.DigitalInOut(board.D5),
                     dc=digitalio.DigitalInOut(board.D25), rst=None, baudrate=64000000,
                     width=135, height=240, x_offset=53, y_offset=40, rotation=90)
W, H = 240, 135
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
except OSError:
    font = ImageFont.load_default()

def show(color, text):
    img = Image.new("RGB", (W, H), color)
    d = ImageDraw.Draw(img)
    box = d.textbbox((0, 0), text, font=font)
    d.text(((W - box[2]) / 2, (H - box[3]) / 2), text, font=font, fill=(0, 0, 0))
    disp.image(img)

votes = {}   # name -> time of last vote

def on_message(client, userdata, msg):
    name = msg.topic.split("/")[-1]
    votes[name] = time.time()
    print("vote from", name)

client = mqtt.Client(); client.username_pw_set("idd", "device@theFarm")
client.on_message = on_message
client.connect("farlab.infosci.cornell.edu", 1883)
client.subscribe(f"{TEAM}/vote/#")
client.loop_start()

print(f"Center ready. Need {NEEDED} votes. Press the top button to vote.")
last, last_press = "", 0
try:
    while True:
        # my own vote: top button on the PiTFT
        if not button.value and time.time() - last_press > 1:
            client.publish(f"{TEAM}/vote/jin", "1"); last_press = time.time()
        # count votes from the last 60 seconds
        now = time.time()
        live = sorted(n for n, t in votes.items() if now - t < VOTE_TTL)
        s = f"{len(live)}/{NEEDED} want a break: {', '.join(live) or 'nobody'}"
        if s != last:
            client.publish(f"{TEAM}/status", s); print(s); last = s
            show((90, 90, 90) if not live else (255, 200, 0), f"{len(live)}/{NEEDED}")
        # everyone voted: green screen for 10 seconds, then reset
        if len(live) >= NEEDED:
            client.publish(f"{TEAM}/status", "BREAK TIME!"); print("*** BREAK TIME! ***")
            show((0, 220, 80), "BREAK!")
            time.sleep(BREAK_SECONDS); votes.clear(); last = ""
        time.sleep(0.1)
except KeyboardInterrupt:
    show((0, 0, 0), "")
