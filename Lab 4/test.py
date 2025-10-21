import time
import sys
import qwiic
import qwiic_proximity
from adafruit_servokit import ServoKit

# ---------------- Servo Setup ----------------
kit = ServoKit(channels=16)

# Define multiple servos on channels 0, 2, and 4
servos = [kit.servo[i] for i in [0, 2, 4]]
for s in servos:
    s.set_pulse_width_range(500, 2500)

# ---------------- VL53L1X Distance Sensor Setup ----------------
print("VL53L1X Qwiic Test\n")
ToF = qwiic.QwiicVL53L1X(address=0x60)
if ToF.sensor_init() is None:
    print("VL53L1X Sensor online!\n")
else:
    print("Error initializing VL53L1X")

# ---------------- Proximity Sensor Setup ----------------
print("SparkFun Proximity Sensor VCN4040 Init\n")
oProx = qwiic_proximity.QwiicProximity()

if not oProx.connected:
    print("The Qwiic Proximity device isn't connected. Please check wiring.", file=sys.stderr)
    sys.exit(1)

oProx.begin()
print("Proximity Sensor online!\n")

# ---------------- Main Loop ----------------
try:
    while True:
        # --- Read distance sensor ---
        ToF.start_ranging()
        time.sleep(0.005)
        distance = ToF.get_distance()  # in mm
        ToF.stop_ranging()

        # --- Read proximity sensor ---
        proxValue = oProx.get_proximity()

        # --- Convert and print readings ---
        distanceFeet = (distance / 25.4) / 12.0
        print(f"Distance(mm): {distance} | Distance(ft): {distanceFeet:.2f} | Proximity: {proxValue}")

        # --- Servo Control ---
        if proxValue > 350:
            time.sleep(1)
            # for s in servos:
            servos[0].angle = 180
            servos[1].angle = 0
        else:
            # for s in servos:
            servos[0].angle = 0
            servos[1].angle = 180

        time.sleep(0.4)

except KeyboardInterrupt:
    print("\nProgram stopped by user. Resetting servos...")
    for s in servos:
        s.angle = 0
    time.sleep(0.5)
    sys.exit(0)
