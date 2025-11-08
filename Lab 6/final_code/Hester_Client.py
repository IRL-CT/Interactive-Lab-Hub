import paho.mqtt.client as mqtt
import qwiic_joystick
import time
import sys

# ===== CONFIG =====
BROKER = "farlab.infosci.cornell.edu"
PORT = 1883
USERNAME = "idd"
PASSWORD = "device@theFarm"

TASK_TOPIC = "game/hester/task"
RESULT_TOPIC = "game/hester/result"
STATUS_TOPIC = "game/status"
STORY_TOPIC = "game/story"   # subscribe to story narration

# ===== JOYSTICK SETUP =====
joystick = qwiic_joystick.QwiicJoystick()
if not joystick.begin():
    print("Joystick not detected. Check wiring and I2C.")
    sys.exit(1)

print("Joystick ready and connected.\n")

# ===== STATE =====
current_task = None
last_action_time = 0
COOLDOWN = 0.3
TIMEOUT = 8

# ===== THRESHOLDS =====
LEFT_THRESHOLD  = 300
RIGHT_THRESHOLD = 700
UP_THRESHOLD    = 700
DOWN_THRESHOLD  = 300


def get_direction(x, y, btn):
    if btn == 0:
        return "joystick_press"
    if x < LEFT_THRESHOLD:
        return "joystick_left"
    if x > RIGHT_THRESHOLD:
        return "joystick_right"
    if y > UP_THRESHOLD:
        return "joystick_up"
    if y < DOWN_THRESHOLD:
        return "joystick_down"
    return None


# ===== MQTT CALLBACKS =====
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker: {BROKER}")
        client.subscribe(TASK_TOPIC)
        client.subscribe(STATUS_TOPIC)
        client.subscribe(STORY_TOPIC)   # subscribe to story text
    else:
        print("Connection failed. rc =", rc)


def on_message(client, userdata, msg):
    global current_task, last_action_time
    payload = msg.payload.decode().strip()

    if msg.topic == TASK_TOPIC:
        current_task = payload
        last_action_time = time.time()
        print("\nNew Task:", payload)
        print("Perform within", TIMEOUT, "seconds.")

    elif msg.topic == STATUS_TOPIC:
        if payload == "game_success":
            print("\nGAME SUCCESS. All tasks completed.\n")
        elif payload == "game_fail":
            print("\nGAME FAILED. A task was not completed.\n")

    elif msg.topic == STORY_TOPIC:
        print("\n--- STORY NARRATION ---")
        print(payload)
        print("-----------------------\n")


# ===== MQTT SETUP =====
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker...")
client.connect(BROKER, PORT, 60)
client.loop_start()


# ===== MAIN LOOP =====
try:
    while True:
        x = joystick.horizontal
        y = joystick.vertical
        btn = joystick.button

        if current_task:
            now = time.time()
            move = get_direction(x, y, btn)

            if move == current_task and (now - last_action_time) > COOLDOWN:
                print("Task completed:", move)
                client.publish(RESULT_TOPIC, "success")
                current_task = None
                time.sleep(0.3)
                continue

            if now - last_action_time > TIMEOUT:
                print("Timeout. Failed to perform:", current_task)
                client.publish(RESULT_TOPIC, "fail")
                current_task = None
                continue

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    client.loop_stop()
    client.disconnect()