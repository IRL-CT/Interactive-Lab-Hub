
import board
import busio
 
# modified from https://www.digikey.com/en/maker/projects/circuitpython-basics-i2c-and-spi/9799e0554de14af3850975dfb0174ae3

# Try to create an I2C device
i2c = busio.I2C(board.SCL, board.SDA)
print("I2C ok!")

REGISTERS = (0, 32)  # Range of registers to read, from the first up to (but
                      # not including!) the second value.
 
REGISTER_SIZE = 2     # Number of bytes to read from each register.

while not i2c.try_lock():
    pass
# Find the first I2C device available.
devices = i2c.scan()
while len(devices) < 1:
    devices = i2c.scan()
device = devices[0]
print(f"Found device with address: {hex(device)}")

# Scan all the registers and read their byte values.
result = bytearray(REGISTER_SIZE)
for register in range(*REGISTERS):
    try:
        i2c.writeto(device, bytes([register]))
        i2c.readfrom_into(device, result)
        print(f"Address {hex(register)}: {[hex(x) for x in result]}")
    except OSError:
        continue  # Ignore registers that don't exist

i2c.unlock()