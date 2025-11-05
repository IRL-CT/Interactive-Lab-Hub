"""
Distributed Bird Guessing Game - Pi Client
Communicates with the server via MQTT.
Controls:
- Button A (GPIO 23): Increment guess
- Button B (GPIO 24): Decrement guess
- ST7789 Display: Shows game state and current guess
"""
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import paho.mqtt.client as mqtt
import uuid
import signal
import ssl
import json
import socket
import subprocess
import time

# --- MQTT Configuration (MUST match server) ---
MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

MQTT_TOPIC_PREFIX = 'IDD/birdgame'
MQTT_TOPIC_REGISTER = f'{MQTT_TOPIC_PREFIX}/client/register'
MQTT_TOPIC_SUBMIT_GUESS = f'{MQTT_TOPIC_PREFIX}/client/submit_guess'

MQTT_TOPIC_NEW_ROUND = f'{MQTT_TOPIC_PREFIX}/broadcast/new_round'
MQTT_TOPIC_TIMES_UP = f'{MQTT_TOPIC_PREFIX}/broadcast/times_up'
MQTT_TOPIC_ROUND_IDLE = f'{MQTT_TOPIC_PREFIX}/broadcast/round_idle'

# --- Pi Hardware Setup ---
# Config for display CS and DC pins
CS_PIN = digitalio.DigitalInOut(board.D5)    # GPIO5 (PIN 29)
DC_PIN = digitalio.DigitalInOut(board.D25)   # GPIO25 (PIN 22)
RESET_PIN = None
BAUDRATE = 64000000
# Config for buttons
BUTTON_A_PIN = board.D23  # Increment
BUTTON_B_PIN = board.D24  # Decrement

# --- Global State ---
MAC_ADDRESS = "00:00:00:00:00:00"  # Will be set in setup
disp = None
draw = None
image = None
font = None
buttonA = None
buttonB = None
mqtt_client = None

game_state = 'IDLE'     # IDLE, GUESSING, RESULTS
current_guess = 0
display_needs_update = True
last_button_press = 0

# --- Utility Functions ---

def get_mac_address():
    """Get the MAC address to uniquely identify this Pi."""
    try:
        result = subprocess.run(['cat', '/sys/class/net/eth0/address'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        result = subprocess.run(['cat', '/sys/class/net/wlan0/address'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Error getting MAC address: {e}")
    return str(uuid.uuid1()) # Fallback

# --- Display Functions ---

def setup_display_and_buttons():
    """Initialize the ST7789 display and buttons."""
    global disp, draw, image, font, buttonA, buttonB
    try:
        spi = board.SPI()
        disp = st7789.ST7789(
            spi, cs=CS_PIN, dc=DC_PIN, rst=RESET_PIN, baudrate=BAUDRATE,
            width=135, height=240, x_offset=53, y_offset=40, rotation=90
        )
        # After rotation, width/height are swapped
        image = Image.new("RGB", (disp.height, disp.width))
        draw = ImageDraw.Draw(image)
        
        # Turn on backlight
        backlight = digitalio.DigitalInOut(board.D22)
        backlight.switch_to_output()
        backlight.value = True
        
        # Setup buttons
        buttonA = digitalio.DigitalInOut(BUTTON_A_PIN)
        buttonB = digitalio.DigitalInOut(BUTTON_B_PIN)
        buttonA.switch_to_input(pull=digitalio.Pull.UP)
        buttonB.switch_to_input(pull=digitalio.Pull.UP)

        # Load a font
        try:
            # --- SMALLER FONT ---
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 20)
        except IOError:
            try:
                # Try a slightly smaller one
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
            except IOError:
                font = ImageFont.load_default()
            
        print("[OK] Display and buttons initialized")
        return True
    except Exception as e:
        print(f"[ERROR] Could not set up display: {e}")
        return False

def draw_display_text(line1, line2, line3, line4, line5):
    """Helper to draw 5 lines of text to the display."""
    if not draw: return
    draw.rectangle((0, 0, disp.height, disp.width), outline=0, fill=(0, 0, 0)) # Clear
    # --- ADJUSTED SPACING (for 135px height) ---
    draw.text((5, 5), line1, font=font, fill="#FFFFFF")
    draw.text((5, 30), line2, font=font, fill="#FFFF00") # Yellow
    draw.text((5, 55), line3, font=font, fill="#FFFFFF")
    draw.text((5, 80), line4, font=font, fill="#FFFFFF")
    draw.text((5, 105), line5, font=font, fill="#00FF00") # Green
    disp.image(image)

def update_display():
    """Updates the display based on the current game state."""
    global display_needs_update
    if not display_needs_update:
        return
        
    try:
        if game_state == 'IDLE':
            # --- SHORTER TEXT ---
            draw_display_text(
                "Bird Game!",
                "Waiting...",
                "",
                "",
                f"MAC: {MAC_ADDRESS[-5:]}"
            )
        elif game_state == 'GUESSING':
            # --- SHORTER TEXT ---
            draw_display_text(
                "GUESS!",
                f"--> {current_guess:02d} <--",
                "",
                "A=Up / B=Down",
                f"MAC: {MAC_ADDRESS[-5:]}"
            )
        elif game_state == 'RESULTS':
            # --- SHORTER TEXT ---
            draw_display_text(
                "TIME'S UP!",
                "Final guess:",
                f"{current_guess:02d}",
                "Submitting...",
                ""
            )
        display_needs_update = False
    except Exception as e:
        print(f"Error updating display: {e}")


# --- MQTT Callbacks ---

def on_mqtt_connect(client, userdata, flags, rc):
    """Callback when this Pi connects to the MQTT broker."""
    global display_needs_update
    if rc == 0:
        print(f"[OK] Connected to MQTT broker: {MQTT_BROKER}")
        # Subscribe to broadcast topics from the server
        client.subscribe(MQTT_TOPIC_NEW_ROUND)
        client.subscribe(MQTT_TOPIC_TIMES_UP)
        client.subscribe(MQTT_TOPIC_ROUND_IDLE)
        
        # Register this Pi with the server
        payload = json.dumps({'mac': MAC_ADDRESS})
        client.publish(MQTT_TOPIC_REGISTER, payload)
        print(f"MQTT TX to {MQTT_TOPIC_REGISTER}: {payload}")
        display_needs_update = True
    else:
        print(f"[ERROR] MQTT Connection failed with code {rc}")

def on_mqtt_message(client, userdata, msg):
    """Callback for messages received from the broker."""
    global game_state, current_guess, display_needs_update
    
    try:
        payload = msg.payload.decode('utf-8')
        print(f"MQTT RX on {msg.topic}: {payload}")

        if msg.topic == MQTT_TOPIC_NEW_ROUND:
            # Server started a new round
            game_state = 'GUESSING'
            current_guess = 0
            
        elif msg.topic == MQTT_TOPIC_TIMES_UP:
            # Time is up! Submit our guess
            game_state = 'RESULTS'
            payload = json.dumps({'mac': MAC_ADDRESS, 'guess': current_guess})
            client.publish(MQTT_TOPIC_SUBMIT_GUESS, payload)
            print(f"MQTT TX to {MQTT_TOPIC_SUBMIT_GUESS}: {payload}")
            
        elif msg.topic == MQTT_TOPIC_ROUND_IDLE:
            # Round is over, back to idle
            game_state = 'IDLE'
            
        display_needs_update = True
        
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# --- Main Loop ---

def poll_buttons():
    """Check for button presses and update state."""
    global current_guess, display_needs_update, last_button_press
    
    # Simple debounce
    now = time.monotonic()
    if (now - last_button_press) < 0.2:
        return

    # Only allow guessing during the 'GUESSING' state
    if game_state == 'GUESSING':
        if not buttonA.value:  # Button A pressed (pulled low)
            current_guess += 1
            display_needs_update = True
            last_button_press = now
            print(f"Guess incremented: {current_guess}")
            
        elif not buttonB.value:  # Button B pressed
            current_guess = max(0, current_guess - 1) # Don't go below 0
            display_needs_update = True
            last_button_press = now
            print(f"Guess decremented: {current_guess}")

def signal_handler(signum, frame):
    """Graceful shutdown."""
    print("\nShutting down...")
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    draw_display_text("Offline.", "", "", "", "")
    print("Client shut down.")
    exit(0)

def main():
    global MAC_ADDRESS, mqtt_client
    
    print("=" * 50)
    print("  Bird Guessing Game - Pi Client (MQTT)")
    print("=" * 50)
    
    MAC_ADDRESS = get_mac_address()
    print(f"MAC Address: {MAC_ADDRESS}")
    
    # Setup display
    if not setup_display_and_buttons():
        print("Continuing in headless mode (no display)")
    
    # Setup MQTT
    mqtt_client = mqtt.Client(f"pi-client-{MAC_ADDRESS}")
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    
    try:
        print(f"Connecting to MQTT broker {MQTT_BROKER}...")
        mqtt_client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        mqtt_client.loop_start() # Starts background thread
    except Exception as e:
        print(f"CRITICAL: Could not connect to MQTT broker: {e}")
        draw_display_text("ERROR", "MQTT Connect", "Failed.", "", "")
        exit(1)

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\nClient running. Waiting for game to start...")
    print("Press Ctrl+C to exit.")
    
    # Main loop
    while True:
        poll_buttons()
        update_display()
        time.sleep(0.05) # Prevent high CPU usage

if __name__ == '__main__':
    main()
