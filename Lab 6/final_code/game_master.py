import random
import time
import paho.mqtt.client as mqtt

BROKER = "farlab.infosci.cornell.edu"
PORT = 1883
USERNAME = "idd"
PASSWORD = "device@theFarm"

# Shared narration topic
STORY_TOPIC = "game/story"

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
    "sandy": ["color_red"]
}

waiting_for = None
game_over = False

def broadcast_story(text):
    print("\n" + text + "\n")
    client.publish(STORY_TOPIC, text)

def on_message(client, userdata, msg):
    global waiting_for, game_over

    if waiting_for is None:
        return
    
    payload = msg.payload.decode()
    print(f"[RECV] {msg.topic} -> {payload}")

    if payload == "success":
        waiting_for = None
    else:
        broadcast_story("Your action falters. The mechanism rejects your attempt. The temple seals itself. The heist has failed.")
        client.publish("game/status", "game_fail")
        game_over = True

def play_game():
    global waiting_for, game_over

    game_over = False

    # Opening story
    broadcast_story(
        "You are part of a legendary trio of master thieves known as the Silent Serpents. "
        "You have infiltrated the Temple of the Sleeping Star in search of the Heart of Dawn. "
        "The temple is protected by layered traps that require perfect cooperation to overcome."
    )

    assigned_tasks = {
        p["name"]: random.choice(task_bank[p["name"]])
        for p in players
    }

    print("\nGenerated Tasks:")
    for p in players:
        print(f"  {p['name']} must perform {assigned_tasks[p['name']]}")

    # Player order story + execution
    for p in players:
        if game_over:
            return

        task = assigned_tasks[p["name"]]

        if p["name"] == "joy":
            broadcast_story(
                "A wall of ancient runes glows faintly. The correct touch will unlock the mechanism. "
                "Choose wisely, for a wrong move will seal the chamber forever."
            )
        
        elif p["name"] == "hester":
            broadcast_story(
                "A shifting stone walkway activates beneath your feet. You must step in the correct direction "
                "to avoid the concealed spikes below."
            )
        
        elif p["name"] == "sandy":
            broadcast_story(
                "A spectral barrier blocks your passage. Its surface ripples with shifting color. "
                "Only by matching the correct hue can the barrier dissolve."
            )

        print(f"Sending task to {p['name']} : {task}")
        client.publish(p["task_topic"], task)

        waiting_for = p["name"]

        # wait for success
        t = time.time()
        while waiting_for is not None and time.time() - t < 15:
            time.sleep(0.1)

        if waiting_for is not None:
            broadcast_story("Time slips away. The mechanism locks permanently. The heist ends here.")
            client.publish("game/status", "game_fail")
            return

        broadcast_story("Your action is precise. The mechanism responds. The path forward opens.")

    broadcast_story(
        "The final seal breaks. The chamber reveals the Heart of Dawn, shimmering in the darkness. "
        "You lift the relic and escape into the night. The Silent Serpents succeed once again."
    )
    client.publish("game/status", "game_success")


# MQTT Setup
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_message = on_message
client.connect(BROKER, PORT, 60)

for p in players:
    client.subscribe(p["result_topic"])

client.loop_start()

print("===== Game Master Started =====")

while True:
    input("\nPress Enter to begin the next attempt...")
    play_game()
