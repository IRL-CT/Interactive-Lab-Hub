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
PUBLISH_INTERVAL = 2.0


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
        cs_pin = digitalio.DigitalInOut(board.CE0)
        dc_pin = digitalio.DigitalInOut(board.D25)
        reset_pin = None

        # Config for display baudrate
        BAUDRATE = 64000000

        backlight = digitalio.DigitalInOut(board.D22)
        backlight.switch_to_output()
        backlight.value = True
        
        buttonA = digitalio.DigitalInOut(board.D23)
        buttonB = digitalio.DigitalInOut(board.D24)
        buttonA.switch_to_input()
        buttonB.switch_to_input()

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
        )

        height = disp.height
        width = disp.width
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)

        return disp, draw, image, buttonA, buttonB
    except Exception as e:
        print(f"Error setting up display: {e}")
        return None, None, None, None, None


def on_connect(client, userdata, flags, rc):
    """Callback when MQTT client connects"""
    if rc == 0:
        print(f"✓ Connected to MQTT broker: {MQTT_BROKER}")
    else:
        print(f"✗ Connection failed with code {rc}")


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
    print("✓ Color sensor ready")
    
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
    except Exception as e:
        print(f"✗ Failed to connect to MQTT broker: {e}")
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
            
            # Convert from 16-bit to 8-bit color
            # Normalize by ambient light (alpha channel)
            if a > 0:
                r = int(min(255, (r * 255) // a))
                g = int(min(255, (g * 255) // a))
                b = int(min(255, (b * 255) // a))
            else:
                r = g = b = 0
            
            # Update display if available
            if draw and image and disp:
                draw.rectangle((0, 0, image.width, image.height), fill=(r, g, b))
                
                # Add text overlay
                try:
                    font = ImageFont.load_default()
                    text_color = (255, 255, 255) if (r + g + b) < 384 else (0, 0, 0)
                    draw.text((10, 10), f"R:{r}", font=font, fill=text_color)
                    draw.text((10, 30), f"G:{g}", font=font, fill=text_color)
                    draw.text((10, 50), f"B:{b}", font=font, fill=text_color)
                    draw.text((10, 80), "Publishing...", font=font, fill=text_color)
                except:
                    pass
                
                disp.image(image)
            
            # Publish to MQTT at specified interval
            current_time = time.time()
            if current_time - last_publish_time >= PUBLISH_INTERVAL:
                # Create JSON payload
                payload = json.dumps({
                    'mac': mac_address,
                    'ip': ip_address,
                    'r': r,
                    'g': g,
                    'b': b,
                    'timestamp': int(current_time)
                })
                
                # Publish to MQTT
                result = client.publish(MQTT_TOPIC, payload)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"✓ Streaming: RGB({r:3d}, {g:3d}, {b:3d}) | {mac_address[:17]}")
                else:
                    print(f"✗ Publish failed: {result.rc}")
                
                last_publish_time = current_time
            
            time.sleep(0.1)  # Small delay to prevent CPU spinning
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)


if __name__ == '__main__':
    main()
