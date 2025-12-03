#!/usr/bin/env python3
"""
LSM6DS3 Data Collector for Edge Impulse
Collects accelerometer and gyroscope data and saves in Edge Impulse CSV format
"""

import time
import csv
import json
from datetime import datetime
from smbus2 import SMBus
import sys

class LSM6DS3:
    """Driver for LSM6DS3 IMU sensor"""
    
    # I2C address
    ADDRESS = 0x6A  # or 0x6B depending on your module
    
    # Register addresses
    CTRL1_XL = 0x10  # Accelerometer control
    CTRL2_G = 0x11   # Gyroscope control
    
    # Output registers
    OUTX_L_G = 0x22  # Gyroscope X-axis low byte
    OUTX_L_XL = 0x28 # Accelerometer X-axis low byte
    
    def __init__(self, bus=1, address=ADDRESS):
        self.bus = SMBus(bus)
        self.address = address
        self.init_sensor()
    
    def init_sensor(self):
        """Initialize the sensor with default settings"""
        # Configure accelerometer: 416 Hz, ±4g
        self.bus.write_byte_data(self.address, self.CTRL1_XL, 0x60)
        # Configure gyroscope: 416 Hz, 2000 dps
        self.bus.write_byte_data(self.address, self.CTRL2_G, 0x6C)
        time.sleep(0.1)
    
    def read_accel(self):
        """Read accelerometer data (x, y, z) in g"""
        data = self.bus.read_i2c_block_data(self.address, self.OUTX_L_XL, 6)
        
        x = self._convert_accel(data[0] | (data[1] << 8))
        y = self._convert_accel(data[2] | (data[3] << 8))
        z = self._convert_accel(data[4] | (data[5] << 8))
        
        return x, y, z
    
    def read_gyro(self):
        """Read gyroscope data (x, y, z) in dps"""
        data = self.bus.read_i2c_block_data(self.address, self.OUTX_L_G, 6)
        
        x = self._convert_gyro(data[0] | (data[1] << 8))
        y = self._convert_gyro(data[2] | (data[3] << 8))
        z = self._convert_gyro(data[4] | (data[5] << 8))
        
        return x, y, z
    
    def _convert_accel(self, raw):
        """Convert raw accelerometer value to g (±4g range)"""
        if raw > 32767:
            raw -= 65536
        return raw * 4.0 / 32768.0
    
    def _convert_gyro(self, raw):
        """Convert raw gyroscope value to dps (2000 dps range)"""
        if raw > 32767:
            raw -= 65536
        return raw * 2000.0 / 32768.0
    
    def read_all(self):
        """Read both accelerometer and gyroscope"""
        accel = self.read_accel()
        gyro = self.read_gyro()
        return accel, gyro


class EdgeImpulseCollector:
    """Collects sensor data in Edge Impulse format"""
    
    def __init__(self, sensor, sample_rate=100):
        self.sensor = sensor
        self.sample_rate = sample_rate
        self.interval = 1.0 / sample_rate
    
    def collect_sample(self, label, duration_seconds, filename=None):
        """
        Collect a sample for a specific label
        
        Args:
            label: Movement label (e.g., 'idle', 'walking', 'running')
            duration_seconds: How long to collect data
            filename: Optional filename, auto-generated if not provided
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{label}_{timestamp}.csv"
        
        print(f"\nCollecting '{label}' for {duration_seconds} seconds...")
        print("Starting in 3 seconds - get ready!")
        time.sleep(3)
        
        samples = []
        start_time = time.time()
        sample_count = 0
        
        print("Recording... ", end='', flush=True)
        
        while time.time() - start_time < duration_seconds:
            loop_start = time.time()
            
            # Read sensor data
            accel, gyro = self.sensor.read_all()
            
            # Calculate timestamp in milliseconds
            timestamp_ms = int((time.time() - start_time) * 1000)
            
            # Store sample
            samples.append({
                'timestamp': timestamp_ms,
                'accX': accel[0],
                'accY': accel[1],
                'accZ': accel[2],
                'gyrX': gyro[0],
                'gyrY': gyro[1],
                'gyrZ': gyro[2]
            })
            
            sample_count += 1
            
            # Maintain sample rate
            elapsed = time.time() - loop_start
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
        
        print(f"Done! Collected {sample_count} samples")
        
        # Save to CSV
        self.save_csv(samples, filename, label)
        print(f"Saved to: {filename}")
        
        return filename
    
    def save_csv(self, samples, filename, label):
        """Save samples to CSV in Edge Impulse format"""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header row
            writer.writerow(['timestamp', 'accX', 'accY', 'accZ', 'gyrX', 'gyrY', 'gyrZ'])
            # Data rows
            for sample in samples:
                writer.writerow([
                    sample['timestamp'],
                    f"{sample['accX']:.6f}",
                    f"{sample['accY']:.6f}",
                    f"{sample['accZ']:.6f}",
                    f"{sample['gyrX']:.6f}",
                    f"{sample['gyrY']:.6f}",
                    f"{sample['gyrZ']:.6f}"
                ])
    
    def save_json(self, samples, filename, label):
        """Alternative: Save in JSON format"""
        data = {
            "protected": {
                "ver": "v1",
                "alg": "HS256",
                "iat": int(time.time())
            },
            "signature": "",
            "payload": {
                "device_name": "raspberry-pi",
                "device_type": "LSM6DS3",
                "interval_ms": int(self.interval * 1000),
                "sensors": [
                    {"name": "accX", "units": "g"},
                    {"name": "accY", "units": "g"},
                    {"name": "accZ", "units": "g"},
                    {"name": "gyrX", "units": "dps"},
                    {"name": "gyrY", "units": "dps"},
                    {"name": "gyrZ", "units": "dps"}
                ],
                "values": [[
                    s['accX'], s['accY'], s['accZ'],
                    s['gyrX'], s['gyrY'], s['gyrZ']
                ] for s in samples]
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


def main():
    """Main data collection interface"""
    print("=" * 60)
    print("LSM6DS3 Data Collector for Edge Impulse")
    print("=" * 60)
    
    # Initialize sensor
    try:
        print("\nInitializing LSM6DS3 sensor...")
        sensor = LSM6DS3()
        print("Sensor initialized successfully")
    except Exception as e:
        print(f"Error initializing sensor: {e}")
        print("\nTroubleshooting:")
        print("- Check I2C is enabled: sudo raspi-config")
        print("- Check sensor connection")
        print("- Try address 0x6B if 0x6A doesn't work")
        sys.exit(1)
    
    # Initialize collector
    sample_rate = 100  # Hz
    collector = EdgeImpulseCollector(sensor, sample_rate=sample_rate)
    
    print(f"\nConfiguration:")
    print(f"- Sample rate: {sample_rate} Hz")
    print(f"- Accelerometer range: ±4g")
    print(f"- Gyroscope range: 2000 dps")
    
    # Define your movement labels
    movements = ['idle', 'shake', 'rock', 'jumping', 'waving']
    
    print("\n" + "=" * 60)
    print("Data Collection Menu")
    print("=" * 60)
    print("\nAvailable movements:")
    for i, movement in enumerate(movements, 1):
        print(f"{i}. {movement}")
    print(f"{len(movements) + 1}. Custom label")
    print("0. Exit")
    
    while True:
        print("\n" + "-" * 60)
        choice = input("\nSelect movement to record (or 0 to exit): ").strip()
        
        if choice == '0':
            print("Exiting...")
            break
        
        try:
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(movements):
                label = movements[choice_num - 1]
            elif choice_num == len(movements) + 1:
                label = input("Enter custom label: ").strip()
            else:
                print("Invalid choice!")
                continue
            
            # Get duration
            duration_input = input(f"Duration in seconds (default 10): ").strip()
            duration = int(duration_input) if duration_input else 5
            
            # Collect sample
            collector.collect_sample(label, duration)
            
            # Ask if want to continue
            continue_choice = input("\nCollect another sample? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("\nDone collecting! Upload CSV files to Edge Impulse.")
                break
                
        except ValueError:
            print("Invalid input!")
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()