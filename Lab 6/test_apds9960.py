#!/usr/bin/env python3
"""
Quick test script for APDS-9960 RGB sensor
Run this on your Pi to verify the sensor is working
"""

import board
import busio
import adafruit_apds9960.apds9960
import time

print("=" * 50)
print("APDS-9960 RGB Sensor Test")
print("=" * 50)

try:
    # Initialize I2C
    print("\n1. Initializing I2C...")
    i2c = busio.I2C(board.SCL, board.SDA)
    print("   ✓ I2C initialized")
    
    # Initialize sensor
    print("\n2. Initializing APDS-9960...")
    sensor = adafruit_apds9960.apds9960.APDS9960(i2c)
    print("   ✓ Sensor found")
    
    # Enable color sensing
    print("\n3. Enabling color sensor...")
    sensor.enable_color = True
    time.sleep(0.5)  # Let sensor stabilize
    print("   ✓ Color sensing enabled")
    
    print("\n" + "=" * 50)
    print("Reading colors... (Press Ctrl+C to stop)")
    print("=" * 50)
    print()
    
    # Read colors continuously
    while True:
        # Wait for valid color data
        while not sensor.color_data_ready:
            time.sleep(0.01)
        
        # Read RGBC values
        r, g, b, c = sensor.color_data
        
        # Normalize to 0-255 range (sensor returns 0-65535)
        r_norm = min(255, int((r / 65535) * 255))
        g_norm = min(255, int((g / 65535) * 255))
        b_norm = min(255, int((b / 65535) * 255))
        
        # Display results
        print(f"R: {r:5d} ({r_norm:3d})  |  "
              f"G: {g:5d} ({g_norm:3d})  |  "
              f"B: {b:5d} ({b_norm:3d})  |  "
              f"Clear: {c:5d}")
        
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n\nTest stopped by user")
    print("=" * 50)

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Check I2C is enabled: sudo raspi-config -> Interface Options -> I2C")
    print("  2. Check sensor is connected properly")
    print("  3. Run: i2cdetect -y 1")
    print("     (APDS-9960 should appear at address 0x39)")
