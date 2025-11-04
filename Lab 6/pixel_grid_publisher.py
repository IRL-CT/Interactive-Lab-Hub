#!/usr/bin/env python3
"""
Pixel Grid Pi Publisher
Reads RGB color sensor and publishes to collaborative pixel grid
Each Pi is identified by MAC address and gets a stable position in the grid
"""

import board
import busio
import adafruit_apds9960.apds9960
import time
import paho.mqtt.client as mqtt
import uuid
import signal
import ssl
import json
import socket
import subprocess

# Optional: Display support (comment out if no display)
try:
    import digitalio
    from PIL import Image, ImageDraw, ImageFont
    import adafruit_rgb_display.st7789 as st7789
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False
    print("Display libraries not available - running in headless mode")


# MQTT Configuration
MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883  # Changed to non-TLS port
MQTT_TOPIC = 'IDD/pixelgrid/colors'
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

# Publishing interval (seconds)
PUBLISH_INTERVAL = 0.1


def get_mac_address():
    """Get the MAC address of the primary network interface"""
    try:
        # Try to get MAC from eth0 or wlan0
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
    
    # Fallback to UUID if MAC can't be determined
    return str(uuid.uuid1())


def get_ip_address():
    """Get the IP address of this device"""
    try:
        # Connect to external host to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def setup_display():
    """Setup the MiniPiTFT display if available"""
    if not DISPLAY_AVAILABLE:
        return None, None, None, None, None
    
    try:
        # Configuration for CS and DC pins
        # Use GPIO5 instead of CE0 to avoid SPI conflicts
        cs_pin = digitalio.DigitalInOut(board.D5)   # GPIO5 (PIN 29)
        dc_pin = digitalio.DigitalInOut(board.D25)  # GPIO25 (PIN 22)
        reset_pin = None

        # Config for display baudrate
        BAUDRATE = 64000000

        backlight = digitalio.DigitalInOut(board.D22)
        backlight.switch_to_output()
        backlight.value = True
        
        # Buttons with pull-ups (active LOW when pressed)
        buttonA = digitalio.DigitalInOut(board.D23)
        buttonB = digitalio.DigitalInOut(board.D24)
        buttonA.switch_to_input(pull=digitalio.Pull.UP)
        buttonB.switch_to_input(pull=digitalio.Pull.UP)

        # Setup SPI bus using hardware SPI
        spi = board.SPI()

        # Create the ST7789 display
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
            rotation=90  # Rotate 90 degrees for vertical orientation
        )

        # After rotation, width and height are swapped
        width = 240
        height = 135
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        
        print("[OK] Display initialized (240x135 rotated)")

        return disp, draw, image, buttonA, buttonB
    except Exception as e:
        print(f"Error setting up display: {e}")
        return None, None, None, None, None


def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print(f"[OK] Connected to MQTT broker: {MQTT_BROKER}")
    else:
        print(f"[ERROR] Connection failed with code {rc}")


def main():
    print("=" * 50)
    print("  Collaborative Pixel Grid - Pi Publisher")
    print("=" * 50)
    
    # Get device identifiers
    mac_address = get_mac_address()
    ip_address = get_ip_address()
    
    print(f"MAC Address: {mac_address}")
    print(f"IP Address: {ip_address}")
    print(f"MQTT Topic: {MQTT_TOPIC}")
    print()
    
    # Setup display (if available)
    disp, draw, image, buttonA, buttonB = setup_display()
    
    # Setup I2C and color sensor
    print("Initializing color sensor...")
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_apds9960.apds9960.APDS9960(i2c)
    sensor.enable_color = True
    
    # Adjust integration time and gain for better color detection
    # Lower gain = better for bright colors, higher gain = better for dim colors
    try:
        sensor.color_gain = 1  # Try 1x gain first (options: 1, 4, 16, 64)
        sensor.integration_time = 10  # milliseconds (range: 2.78 - 712ms)
        print("[OK] Color sensor ready (gain=1x, integration=10ms)")
    except:
        print("[OK] Color sensor ready (default settings)")
    
    # Setup MQTT client
    print("Connecting to MQTT broker...")
    client = mqtt.Client(str(uuid.uuid1()))
    # Remove TLS for non-encrypted connection
    # client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    
    try:
        client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        client.loop_start()
        # Wait a bit for connection to establish
        time.sleep(2)
        
        # Check if connected
        if client.is_connected():
            print(f"[OK] MQTT connected and ready")
        else:
            print("[WARNING] MQTT connection pending...")
    except Exception as e:
        print(f"[ERROR] Failed to connect to MQTT broker: {e}")
        return
    
    # Graceful exit handler
    def signal_handler(signum, frame):
        print("\nShutting down gracefully...")
        client.loop_stop()
        client.disconnect()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n" + "=" * 50)
    print("Streaming color data to pixel grid...")
    print(f"Update frequency: {PUBLISH_INTERVAL}s ({1/PUBLISH_INTERVAL:.1f} updates/sec)")
    print("Press Ctrl+C to exit")
    print("=" * 50 + "\n")
    
    last_publish_time = 0
    
    # Main loop
    while True:
        try:
            # Read color sensor
            r, g, b, a = sensor.color_data
            
            # Color boost - APDS9960 sensors need calibration
            r = int(r * 1.2)  # Boost red by 20% for better yellows/oranges
            g = int(g * 1.2)  # Boost green by 20% for better yellows
            b = int(b * 1.7)  # Boost blue by 70% (blue is most underreported)
            
            # Convert from 16-bit to 8-bit color with better scaling
            # Use a different normalization approach
            if r > 0 or g > 0 or b > 0:
                # Find max value to scale proportionally
                max_val = max(r, g, b)
                if max_val > 0:
                    # Scale to 8-bit range while preserving ratios
                    scale = 255.0 / max_val
                    r = int(min(255, r * scale))
                    g = int(min(255, g * scale))
                    b = int(min(255, b * scale))
                else:
                    r = g = b = 0
            else:
                r = g = b = 0
            
            # Create JSON payload for display and MQTT
            payload = json.dumps({
                'mac': mac_address,
                'ip': ip_address,
                'r': r,
                'g': g,
                'b': b,
                'timestamp': int(time.time())
            }, indent=2)
            
            # Update display if available - show color + payload
            if draw and image and disp:
                # Fill entire screen with the sensor color
                draw.rectangle((0, 0, image.width, image.height), fill=(r, g, b))
                
                # Add payload text overlay
                try:
                    # Use larger font - try truetype, fall back to default
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
                    except:
                        font = ImageFont.load_default()
                    
                    # Choose text color based on background brightness
                    text_color = (255, 255, 255) if (r + g + b) < 384 else (0, 0, 0)
                    
                    # Display payload on screen with line breaks
                    y_offset = 5
                    for line in payload.split('\n'):
                        draw.text((5, y_offset), line, font=font, fill=text_color)
                        y_offset += 16  # Increased spacing for larger font
                except Exception as e:
                    pass
                
                disp.image(image)
            
            # Publish to MQTT at specified interval
            current_time = time.time()
            if current_time - last_publish_time >= PUBLISH_INTERVAL:
                # Re-create compact payload for MQTT (without indentation)
                mqtt_payload = json.dumps({
                    'mac': mac_address,
                    'ip': ip_address,
                    'r': r,
                    'g': g,
                    'b': b,
                    'timestamp': int(current_time)
                })
                
                # Publish to MQTT
                result = client.publish(MQTT_TOPIC, mqtt_payload)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"[OK] Streaming: RGB({r:3d}, {g:3d}, {b:3d}) | {mac_address[:17]} | rc:{result.rc} mid:{result.mid}")
                    print(f"     Payload: {mqtt_payload}")
                else:
                    print(f"[ERROR] Publish failed: rc={result.rc}")
                    if not client.is_connected():
                        print("[ERROR] MQTT client disconnected! Attempting to reconnect...")
                        try:
                            client.reconnect()
                        except Exception as e:
                            print(f"[ERROR] Reconnect failed: {e}")
                
                last_publish_time = current_time
            
            time.sleep(0.1)  # Small delay to prevent CPU spinning
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)


if __name__ == '__main__':
    main()
