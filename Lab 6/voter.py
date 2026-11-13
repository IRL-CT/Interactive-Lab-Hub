# Voter Pi: wave a hand over the APDS-9960 to vote for a break.
# Run: python voter.py <your_name>
import sys, time, board
import paho.mqtt.client as mqtt
from adafruit_apds9960.apds9960 import APDS9960

TEAM = "IDD/huadiweilao"
NAME = sys.argv[1] if len(sys.argv) > 1 else "voter"
THRESHOLD = 50   # higher = hand must be closer
COOLDOWN = 3     # seconds between votes

sensor = APDS9960(board.I2C())
sensor.enable_proximity = True

client = mqtt.Client(); client.username_pw_set("idd", "device@theFarm")
client.on_message = lambda c, u, m: print("[status]", m.payload.decode())
client.connect("farlab.infosci.cornell.edu", 1883)
client.subscribe(f"{TEAM}/status")
client.loop_start()

print(NAME, "ready. Wave your hand to vote for a break.")
last = 0
while True:
    if sensor.proximity > THRESHOLD and time.time() - last > COOLDOWN:
        client.publish(f"{TEAM}/vote/{NAME}", "1")
        print("Voted!")
        last = time.time()
    time.sleep(0.05)
