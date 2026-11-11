# Voter Pi: shake the LSM6DS3 to vote for a break.
# Run: python voter_shake.py <your_name>
import sys, time, math, struct, board
import paho.mqtt.client as mqtt
from adafruit_bus_device.i2c_device import I2CDevice

TEAM = "IDD/huadiweilao"
NAME = sys.argv[1] if len(sys.argv) > 1 else "shaker"
SHAKE = 0.7      # how hard to shake (g above normal gravity)
COOLDOWN = 3     # seconds between votes

# find the sensor at 0x6A or 0x6B
i2c = board.I2C()
while not i2c.try_lock():
    pass
found = i2c.scan()
i2c.unlock()
addr = 0x6B if 0x6B in found else 0x6A
dev = I2CDevice(i2c, addr)

def write_reg(reg, val):
    with dev:
        dev.write(bytes([reg, val]))

def read_regs(reg, n):
    buf = bytearray(n)
    with dev:
        dev.write_then_readinto(bytes([reg]), buf)
    return buf

write_reg(0x10, 0x40)   # accelerometer on: 104 Hz, +-2g

def accel_g():
    x, y, z = struct.unpack("<hhh", read_regs(0x28, 6))
    return [v * 0.061 / 1000 for v in (x, y, z)]   # raw -> g

client = mqtt.Client(); client.username_pw_set("idd", "device@theFarm")
client.on_message = lambda c, u, m: print("[status]", m.payload.decode())
client.connect("farlab.infosci.cornell.edu", 1883)
client.subscribe(f"{TEAM}/status")
client.loop_start()

print(NAME, "ready. Shake the sensor to vote.")
last = 0
while True:
    x, y, z = accel_g()
    strength = abs(math.sqrt(x * x + y * y + z * z) - 1.0)   # 0 when still
    if strength > SHAKE and time.time() - last > COOLDOWN:
        client.publish(f"{TEAM}/vote/{NAME}", "1")
        print(f"Shake! Voted. (strength {strength:.2f} g)")
        last = time.time()
    time.sleep(0.02)
