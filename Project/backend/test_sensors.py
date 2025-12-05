#!/usr/bin/env python3
"""
Test script to verify all sensors and hardware are working correctly.
Run this before running the main music_box.py to troubleshoot hardware issues.
"""

import time
import board

print("=" * 60)
print("Interactive Music Box - Hardware Test")
print("=" * 60)

# Test APDS9960 (Color and Gesture Sensor)
print("\n1. Testing APDS9960 (Color/Gesture Sensor)...")
try:
    from adafruit_apds9960.apds9960 import APDS9960
    from adafruit_apds9960 import colorutility
    
    i2c = board.I2C()
    apds = APDS9960(i2c)
    apds.enable_color = True
    apds.enable_proximity = True
    apds.enable_gesture = True
    
    print("   [OK] APDS9960 initialized")
    
    # Test color reading
    print("   Reading color data...")
    for i in range(3):
        while not apds.color_data_ready:
            time.sleep(0.01)
        r, g, b, c = apds.color_data
        lux = colorutility.calculate_lux(r, g, b)
        print(f"   Sample {i+1}: R={r}, G={g}, B={b}, Lux={lux:.1f}")
        time.sleep(0.5)
    
    print("   [OK] Color sensor working")
    print("   Wave your hand over the sensor to test gestures...")
    for i in range(10):
        gesture = apds.gesture()
        if gesture != 0:
            gestures = {0x01: "UP", 0x02: "DOWN", 0x03: "LEFT", 0x04: "RIGHT"}
            print(f"   [OK] Gesture detected: {gestures.get(gesture, 'UNKNOWN')}")
        time.sleep(0.2)
    print("   [OK] Gesture sensor ready")
    
except Exception as e:
    print(f"   [ERROR] APDS9960 error: {e}")
    print("   Check I2C connections and ensure sensor is at address 0x39")

# Test Rotary Encoder (Seesaw)
print("\n2. Testing Rotary Encoder (Seesaw)...")
try:
    from adafruit_seesaw import seesaw, rotaryio
    
    seesaw_board = seesaw.Seesaw(board.I2C(), addr=0x36)
    
    # Verify it's the correct product
    seesaw_product = (seesaw_board.get_version() >> 16) & 0xFFFF
    print(f"   Found Seesaw product ID: {seesaw_product}")
    if seesaw_product != 4991:
        print(f"   [WARNING] Expected product ID 4991, got {seesaw_product}")
    
    encoder = rotaryio.IncrementalEncoder(seesaw_board)
    
    print("   [OK] Rotary encoder initialized")
    print("   Rotate the encoder knob...")
    
    last_position = -encoder.position
    for i in range(20):
        position = -encoder.position
        if position != last_position:
            print(f"   [OK] Position changed: {position}")
            last_position = position
        time.sleep(0.1)
    
    print("   [OK] Rotary encoder working")
    
except Exception as e:
    print(f"   [ERROR] Rotary encoder error: {e}")
    print("   Check I2C connections and ensure Seesaw is at address 0x36")
    print("   Run 'i2cdetect -y 1' to scan for I2C devices")
    print("   Install adafruit-circuitpython-seesaw if missing: pip3 install adafruit-circuitpython-seesaw")

# Test Servo
print("\n3. Testing Servo Motor (PCA9685)...")
try:
    from adafruit_servokit import ServoKit
    
    kit = ServoKit(channels=16)
    servo = kit.servo[0]
    servo.set_pulse_width_range(500, 2500)
    
    print("   [OK] Servo controller initialized")
    print("   Testing servo movement...")
    
    for angle in [90, 0, 180, 90]:
        servo.angle = angle
        print(f"   [OK] Servo moved to {angle} degrees")
        time.sleep(1)
    
    print("   [OK] Servo motor working")
    
except Exception as e:
    print(f"   [ERROR] Servo error: {e}")
    print("   Check PCA9685 servo hat connections and power supply")

# Test Audio
print("\n4. Testing Audio System...")
try:
    import pygame
    pygame.mixer.init()
    print("   [OK] Pygame mixer initialized")
    
    # Check if music directory exists
    from pathlib import Path
    music_dir = Path(__file__).parent / "music"
    if music_dir.exists():
        music_files = list(music_dir.glob("*.mp3")) + \
                     list(music_dir.glob("*.wav")) + \
                     list(music_dir.glob("*.ogg"))
        print(f"   [OK] Found {len(music_files)} music file(s)")
        if music_files:
            print(f"   Sample file: {music_files[0].name}")
    else:
        print(f"   [WARNING] Music directory not found: {music_dir}")
        print("   Create it and add music files to enable playback")
    
    print("   [OK] Audio system ready")
    
except Exception as e:
    print(f"   [ERROR] Audio error: {e}")
    print("   Install pygame: pip3 install pygame")

# I2C Scan
print("\n5. Scanning I2C Bus...")
try:
    import adafruit_bus_device
    i2c = board.I2C()
    
    print("   I2C devices found:")
    while not i2c.try_lock():
        pass
    
    try:
        devices = i2c.scan()
        if devices:
            for addr in devices:
                print(f"   [OK] Address 0x{addr:02X}")
        else:
            print("   [WARNING] No I2C devices found")
    finally:
        i2c.unlock()
    
except Exception as e:
    print(f"   [ERROR] I2C scan error: {e}")

print("\n" + "=" * 60)
print("Hardware Test Complete!")
print("=" * 60)
print("\nIf all tests passed, you can run: python3 music_box.py")
print("If any tests failed, check the error messages above and verify hardware connections.\n")

