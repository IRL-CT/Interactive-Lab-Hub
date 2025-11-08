import time
import board
import busio
import paho.mqtt.client as mqtt
import adafruit_mpr121

BROKER = "test.mosquitto.org"   
PORT = 1883

TASK_TOPIC = "game/joy/task"
RESULT_TOPIC = "game/joy/result"

i2c = busio.I2C(board.SCL, board.SDA)
touch_sensor = adafruit_mpr121.MPR121(i2c)

current_task = None
task_start_time = 0

def on_message(client, userdata, msg):
    global current_task, task_start_time
    payload = msg.payload.decode()
    print(f"[TASK RECEIVED] {payload}")

    # payload exp: "touch_3"
    if payload.startswith("touch_"):
        current_task = int(payload.split("_")[1])
        task_start_time = time.time()

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_message = on_message
client.connect(BROKER, PORT, 60)

client.subscribe(TASK_TOPIC)
client.loop_start()

print("=== Player A (joy) READY ===")
print("waiting for the task...")

while True:
    if current_task is not None:
        # time out
        if time.time() - task_start_time > 8:
            print(" Timeout, FAIL")
            client.publish(RESULT_TOPIC, "fail")
            current_task = None
            continue

        # monitor touch
        if touch_sensor[current_task].value:
            print(f" Touch {current_task} detected → SUCCESS")
            client.publish(RESULT_TOPIC, "success")
            current_task = None

    time.sleep(0.05)
