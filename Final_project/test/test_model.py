#!/usr/bin/env python3
"""
Simple Model Test Script
Just tests if your Edge Impulse model works with LSM6DS3
"""

import time
import sys
from smbus2 import SMBus

# Import Edge Impulse library
try:
    from edge_impulse_linux.runner import ImpulseRunner
except ImportError:
    print("Error: Edge Impulse library not found")
    print("Install with: pip3 install edge-impulse-linux --break-system-packages")
    sys.exit(1)


class LSM6DS3:
    """Simple LSM6DS3 driver"""
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
        self.bus.write_byte_data(self.address, self.CTRL1_XL, 0x50)
        self.bus.write_byte_data(self.address, self.CTRL2_G, 0x50)
        time.sleep(0.1)
    
    def read_accel(self):
        data = self.bus.read_i2c_block_data(self.address, self.OUTX_L_XL, 6)
        x = self._convert_accel(data[0] | (data[1] << 8))
        y = self._convert_accel(data[2] | (data[3] << 8))
        z = self._convert_accel(data[4] | (data[5] << 8))
        return x, y, z
    
    def read_gyro(self):
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


def collect_window(sensor, window_size=200, sample_rate=100):
    """Collect one window of data for classification"""
    features = []
    interval = 1.0 / sample_rate
    
    for _ in range(window_size):
        loop_start = time.time()
        
        accel = sensor.read_accel()
        gyro = sensor.read_gyro()
        
        features.extend([
            accel[0], accel[1], accel[2],
            gyro[0], gyro[1], gyro[2]
        ])
        
        elapsed = time.time() - loop_start
        if elapsed < interval:
            time.sleep(interval - elapsed)
    
    return features


def main():
    print("=" * 60)
    print("Edge Impulse Model Test")
    print("=" * 60)
    
    # Check arguments
    if len(sys.argv) < 2:
        print("\nUsage: python3 test_model.py <model.eim>")
        print("\nExample:")
        print("  python3 test_model.py my-movement-model.eim")
        sys.exit(1)
    
    model_path = sys.argv[1]
    
    # Initialize sensor
    print("\n[1/3] Initializing LSM6DS3 sensor...")
    try:
        sensor = LSM6DS3()
        print("✓ Sensor initialized")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  - Run: i2cdetect -y 1")
        print("  - Enable I2C: sudo raspi-config")
        sys.exit(1)
    
    # Load model
    print(f"\n[2/3] Loading model: {model_path}")
    try:
        runner = ImpulseRunner(model_path)
        model_info = runner.init()
        
        print("✓ Model loaded successfully!")
        print(f"  Project: {model_info['project']['name']}")
        print(f"  Owner: {model_info['project']['owner']}")
        
        labels = model_info['model_parameters']['labels']
        print(f"  Labels: {', '.join(labels)}")
        
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        print("\nCheck:")
        print("  - Model file exists and is correct .eim file")
        print("  - Edge Impulse library is installed")
        sys.exit(1)
    
    # Run test classifications
    print("\n[3/3] Running test classifications...")
    print("=" * 60)
    print("Collecting 2 seconds of data and classifying...")
    print("Press Ctrl+C to stop\n")
    
    test_count = 0
    
    try:
        while True:
            test_count += 1
            print(f"Test #{test_count}")
            print("-" * 60)
            
            # Collect data
            print("  Collecting data... ", end='', flush=True)
            features = collect_window(sensor, window_size=200, sample_rate=100)
            print("Done!")
            
            # Classify
            print("  Running inference... ", end='', flush=True)
            result = runner.classify(features)
            print("Done!")
            
            # Display results
            classification = result['result']['classification']
            timing = result['timing']
            
            print(f"\n  Inference time: {timing['dsp'] + timing['classification']:.0f} ms")
            print(f"  (DSP: {timing['dsp']:.0f} ms, Classification: {timing['classification']:.0f} ms)")
            print("\n  Predictions:")
            
            # Sort by confidence
            sorted_predictions = sorted(
                classification.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            for label, confidence in sorted_predictions:
                # Create confidence bar
                bar_length = int(confidence * 40)
                bar = '█' * bar_length + '░' * (40 - bar_length)
                
                # Color code the top prediction
                if label == sorted_predictions[0][0]:
                    print(f"  ✓ {label:15} {bar} {confidence*100:5.1f}%")
                else:
                    print(f"    {label:15} {bar} {confidence*100:5.1f}%")
            
            print("\n" + "=" * 60)
            
            # Wait a bit before next test
            time.sleep(2)
    
    except KeyboardInterrupt:
        print(f"\n\n✓ Test complete! Ran {test_count} classifications")
        print("\nModel is working correctly!")


if __name__ == "__main__":
    main()