import board
import busio
import time

i2c = busio.I2C(board.SCL, board.SDA)

print("Press and hold button, then release, watch for changes...")

while True:
    try:
        while not i2c.try_lock():
            pass
        
        # Try different read lengths
        for byte_len in [1, 2, 4]:
            try:
                result = bytearray(byte_len)
                i2c.readfrom_into(0x6f, result)
                print(f"Length {byte_len}: {[f'0x{b:02x}' for b in result]}")
            except:
                print(f"Length {byte_len}: Failed")
        
        print("---")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            i2c.unlock()
        except:
            pass
    time.sleep(0.3)