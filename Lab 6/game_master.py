import random
import time
import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"   
PORT = 1883

# define player and MQTT topic
players = [
    {"name": "joy", "task_topic": "game/joy/task", "result_topic": "game/joy/result"},
    {"name": "hester", "task_topic": "game/hester/task", "result_topic": "game/hester/result"},
    {"name": "sandy", "task_topic": "game/sandy/task", "result_topic": "game/sandy/result"}
]

# task instance
task_bank = {
    "joy": ["touch_1", "touch_3", "touch_5"],
    "hester": ["joystick_up", "joystick_down", "joystick_left", "joystick_right", "joystick_press"],
    "sandy": ["color_red", "color_green", "color_blue"]
}

# condition
waiting_for = None
game_over = False

def on_message(client, userdata, msg):
    global waiting_for, game_over

    if waiting_for is None:
        return
    
    payload = msg.payload.decode()
    print(f"[RECV] {msg.topic} → {payload}")

    if payload == "success":
        waiting_for = None  
    else:
        print("\n Someone failed! Game Over.\n")
        client.publish("game/status", "game_fail")
        game_over = True

def play_game():
    global waiting_for, game_over

    game_over = False

    assigned_tasks = {
        p["name"]: random.choice(task_bank[p["name"]])
        for p in players
    }

    print("\n Generated Tasks:")
    for p in players:
        print(f"  {p['name']} has {assigned_tasks[p['name']]}")

    for p in players:
        if game_over:
            return

        task = assigned_tasks[p["name"]]
        print(f"\n Sending task to {p['name']} : {task}")
        client.publish(p["task_topic"], task)

        waiting_for = p["name"]

        # time waiting 8s
        t = time.time()
        while waiting_for is not None and time.time() - t < 8:
            time.sleep(0.1)

        if waiting_for is not None:
            print("\n Timeout! Task failed.\n")
            client.publish("game/status", "game_fail")
            return

    print("\n All succeeded! Broadcasting Success!\n")
    client.publish("game/status", "game_success")


# MQTT Setup
client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT, 60)

for p in players:
    client.subscribe(p["result_topic"])

client.loop_start()

print("===== Game Master Started =====")

while True:
    input("\n press Enter start new game...")
    play_game()
