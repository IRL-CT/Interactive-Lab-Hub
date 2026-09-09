import board
import busio
 
# Try to create an I2C device
i2c = busio.I2C(board.SCL, board.SDA)
print("I2C ok!")
# ids = '\n'.join(map(str,i2c.scan()))
# print(f"I2C device ID's found:\n{ids}")
 
while not i2c.try_lock():
    pass
 
print("I2C addresses found:", [hex(device_address) for device_address in i2c.scan()])
i2c.unlock()