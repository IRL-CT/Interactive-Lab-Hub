#!/usr/bin/env python3
"""
Interactive Pet Robot: LSM6DS3 Movement + MPR121 Touch + NeoPixels
Combines movement classification with touch-based interactions
"""

import time
import sys
import threading
import numpy as np
from smbus2 import SMBus
import adafruit_mpr121
import busio
import board
import subprocess
import os
import neopixel

# Try to import Edge Impulse library
try:
    from edge_impulse_linux.runner import ImpulseRunner
except ImportError:
    print("Warning: Edge Impulse library not found")
    print("Run without movement classification or install: pip3 install edge-impulse-linux --break-system-packages")
    ImpulseRunner = None


# ========== NeoPixel Setup ==========
PIXEL_PIN = board.D12
NUM_PIXELS = 24
BRIGHTNESS = 0.3

pixels = neopixel.NeoPixel(
    PIXEL_PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False
)

# ========== MPR121 Setup ==========
i2c_touch = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c_touch)

# ========== Sound State ==========
purr_process = None
meow_process = None

# ========== Movement State (Shared between threads) ==========
current_movement = "unknown"
movement_confidence = 0.0
movement_lock = threading.Lock()


# ========== LSM6DS3 Driver ==========
class LSM6DS3:
    """Driver for LSM6DS3 IMU sensor"""
    
    ADDRESS = 0x6A
    CTRL1_XL = 0x10
    CTRL2_G = 0x11
    OUTX_L_G = 0x22
    OUTX_L_XL = 0x28
    
    def __init__(self, bus=1, address=ADDRESS):
        self.bus = SMBus(bus)
        self.address = address
        self.init_sensor()
    
    def init_sensor(self):
        """Initialize sensor at 100 Hz"""
        self.bus.write_byte_data(self.address, self.CTRL1_XL, 0x50)
        self.bus.write_byte_data(self.address, self.CTRL2_G, 0x50)
        time.sleep(0.1)
    
    def read_accel(self):
        """Read accelerometer in g"""
        data = self.bus.read_i2c_block_data(self.address, self.OUTX_L_XL, 6)
        x = self._convert_accel(data[0] | (data[1] << 8))
        y = self._convert_accel(data[2] | (data[3] << 8))
        z = self._convert_accel(data[4] | (data[5] << 8))
        return x, y, z
    
    def read_gyro(self):
        """Read gyroscope in dps"""
        data = self.bus.read_i2c_block_data(self.address, self.OUTX_L_G, 6)
        x = self._convert_gyro(data[0] | (data[1] << 8))
        y = self._convert_gyro(data[2] | (data[3] << 8))
        z = self._convert_gyro(data[4] | (data[5] << 8))
        return x, y, z
    
    def _convert_accel(self, raw):
        if raw > 32767:
            raw -= 65536
        return raw * 4.0 / 32768.0
    
    def _convert_gyro(self, raw):
        if raw > 32767:
            raw -= 65536
        return raw * 2000.0 / 32768.0


# ========== Movement Classifier (Background Thread) ==========
class MovementClassifier:
    """Background movement classification"""
    
    def __init__(self, model_path, sensor, window_size=200, sample_rate=100):
        self.sensor = sensor
        self.window_size = window_size
        self.sample_rate = sample_rate
        self.interval = 1.0 / sample_rate
        self.running = False
        
        if ImpulseRunner is None:
            raise ImportError("Edge Impulse library not available")
        
        # Initialize model
        self.runner = ImpulseRunner(model_path)
        model_info = self.runner.init()
        print(f"✓ Model loaded: {model_info['project']['name']}")
        self.labels = model_info['model_parameters']['labels']
        print(f"✓ Labels: {', '.join(self.labels)}")
    
    def collect_window(self):
        """Collect one window of sensor data"""
        features = []
        for _ in range(self.window_size):
            loop_start = time.time()
            accel = self.sensor.read_accel()
            gyro = self.sensor.read_gyro()
            features.extend([accel[0], accel[1], accel[2], gyro[0], gyro[1], gyro[2]])
            elapsed = time.time() - loop_start
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
        return features
    
    def classify_once(self):
        """Run one classification"""
        features = self.collect_window()
        result = self.runner.classify(features)
        classification = result['result']['classification']
        top_label = max(classification, key=classification.get)
        confidence = classification[top_label]
        return top_label, confidence
    
    def run_continuous(self):
        """Background classification loop"""
        global current_movement, movement_confidence
        print("✓ Movement classifier started")
        
        self.running = True
        while self.running:
            try:
                label, conf = self.classify_once()
                with movement_lock:
                    current_movement = label
                    movement_confidence = conf
            except Exception as e:
                print(f"Classification error: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop the classifier"""
        self.running = False


# ========== Sound Helpers ==========
def stop_all():
    """Stop all sounds and turn off LEDs"""
    global purr_process, meow_process
    os.system("pkill aplay")
    purr_process = None
    meow_process = None
    pixels.fill((0, 0, 0))
    pixels.show()

def play_purr():
    """Play purr sound"""
    global purr_process
    if purr_process is None:
        purr_process = subprocess.Popen(["aplay", "-q", "sound/purr.wav"])

def play_meow():
    """Play meow sound"""
    global meow_process
    if meow_process is None:
        meow_process = subprocess.Popen(["aplay", "-q", "sound/meow.wav"])


# ========== LED Animations ==========
def breathing(color, steps=20, speed=0.08):
    """Breathing animation"""
    r, g, b = color
    for i in range(steps):
        level = i / steps
        pixels.fill((int(r*level), int(g*level), int(b*level)))
        pixels.show()
        time.sleep(speed)
    for i in range(steps, -1, -1):
        level = i / steps
        pixels.fill((int(r*level), int(g*level), int(b*level)))
        pixels.show()
        time.sleep(speed)

def movement_indicator(movement, confidence):
    """Show movement status on LEDs"""
    if confidence < 0.5:
        return  # Don't show low confidence movements
    
    # Different colors for different movements
    colors = {
        'idle': (50, 50, 50),      # Gray
        'walking': (0, 150, 255),  # Blue
        'running': (255, 100, 0),  # Orange
        'jumping': (255, 0, 255),  # Magenta
        'waving': (0, 255, 150),   # Cyan
    }
    
    color = colors.get(movement, (100, 100, 100))
    
    # Show intensity based on confidence
    intensity = int(confidence * NUM_PIXELS)
    pixels.fill((0, 0, 0))
    for i in range(min(intensity, NUM_PIXELS)):
        pixels[i] = color
    pixels.show()


# ========== Main Loop ==========
def main():
    global current_movement, movement_confidence
    
    print("=" * 60)
    print("Interactive Pet Robot")
    print("=" * 60)
    
    # Parse arguments
    use_movement_classifier = False
    model_path = None
    
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
        use_movement_classifier = True
    
    # Initialize movement classifier if model provided
    classifier = None
    classifier_thread = None
    
    if use_movement_classifier:
        try:
            print("\nInitializing LSM6DS3 sensor...")
            sensor = LSM6DS3()
            print("✓ LSM6DS3 initialized")
            
            print(f"Loading model: {model_path}")
            classifier = MovementClassifier(model_path, sensor)
            
            # Start classifier in background thread
            classifier_thread = threading.Thread(target=classifier.run_continuous, daemon=True)
            classifier_thread.start()
            
        except Exception as e:
            print(f"✗ Movement classifier error: {e}")
            print("Continuing without movement classification...")
            use_movement_classifier = False
    
    print("\n" + "=" * 60)
    print("Touch Controls:")
    print("  Pad 1: Purr (Purple)")
    print("  Pad 2: Meow (Orange)")
    if use_movement_classifier:
        print("\nMovement Detection:")
        print("  LEDs show current movement")
    print("\nPress Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    last_release_time = None
    last_movement_display = time.time()
    
    try:
        while True:
            touched_1 = mpr121[1].value
            touched_2 = mpr121[2].value
            
            # Touch interaction takes priority
            if touched_1:
                last_release_time = None
                play_purr()
                breathing((80, 40, 150))
                
            elif touched_2:
                last_release_time = None
                play_meow()
                breathing((255, 80, 10))
                
            else:
                # No touch - handle release timer and show movement
                if last_release_time is None:
                    last_release_time = time.time()
                
                elapsed = time.time() - last_release_time
                
                if elapsed >= 3.0:
                    # 3 seconds passed, stop sounds
                    stop_all()
                    last_release_time = None
                
                # Show movement on LEDs when not touched
                if use_movement_classifier and elapsed < 3.0:
                    # Update movement display every 0.5 seconds
                    if time.time() - last_movement_display > 0.5:
                        with movement_lock:
                            movement_indicator(current_movement, movement_confidence)
                            print(f"\rMovement: {current_movement:10} ({movement_confidence*100:5.1f}%)", 
                                  end='', flush=True)
                        last_movement_display = time.time()
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
        if classifier:
            classifier.stop()
        stop_all()
        print("Goodbye!")


if __name__ == "__main__":
    main()