# sandy_client.py
import paho.mqtt.client as mqtt
import board
import adafruit_apds9960.apds9960
import time

BROKER = "farlab.infosci.cornell.edu"
PORT = 1883
USERNAME = "idd"
PASSWORD = "device@theFarm"

MY_NAME = "sandy"
TASK_TOPIC = "game/sandy/task"
RESULT_TOPIC = "game/sandy/result"
STATUS_TOPIC = "game/status"
STORY_TOPIC = "game/story"   # subscribe to story narration

print("Initializing color sensor...")
try:
    i2c = board.I2C()
    sensor = adafruit_apds9960.apds9960.APDS9960(i2c)
    sensor.enable_color = True
    print("Sensor ready\n")
except Exception as e:
    print(f"Sensor init failed: {e}")
    exit(1)

current_task = None
task_completed = False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[OK] Successfully connected to MQTT broker")
        client.subscribe(TASK_TOPIC)
        client.subscribe(STATUS_TOPIC)
        client.subscribe(STORY_TOPIC)   # <—— added
        print(f"[OK] Subscribed to: {TASK_TOPIC}")
        print(f"[OK] Subscribed to: {STATUS_TOPIC}")
        print(f"[OK] Subscribed to: {STORY_TOPIC}")
    else:
        print(f"[ERROR] Connection failed with code {rc}")

def on_message(client, userdata, msg):
    global current_task, task_completed
    
    payload = msg.payload.decode()
    
    if msg.topic == TASK_TOPIC:
        print(f"\n>>> Message received on topic: {msg.topic}")
        print(f">>> Payload: {payload}")
        current_task = payload
        task_completed = False
        
        print("\nTask received:", current_task)
        print("="*40)
        
        if current_task == "color_red":
            print("RED - Place red object near sensor")
        elif current_task == "color_green":
            print("GREEN - Place green object near sensor")
        elif current_task == "color_blue":
            print("BLUE - Place blue object near sensor")
        
        print("="*40)
    
    elif msg.topic == STATUS_TOPIC:
        if payload == "game_success":
            print("\nGame Success!\n")
        elif payload == "game_fail":
            print("\nGame Failed!\n")

    elif msg.topic == STORY_TOPIC:
        print("\n--- STORY NARRATION ---")
        print(payload)
        print("-----------------------\n")

def check_color(target_color):
    while not sensor.color_data_ready:
        time.sleep(0.01)
    
    r, g, b, c = sensor.color_data
    print(f"   RGB=({r:4d}, {g:4d}, {b:4d})", end='\r')
    
    if c < 1000:
        return False
    
    total = r + g + b
    if total == 0:
        return False
    
    r_ratio = r / total
    g_ratio = g / total
    b_ratio = b / total
    
    if target_color == "color_red":
        if r_ratio > 0.45 and r > g and r > b:
            return True
    elif target_color == "color_green":
        if g_ratio > 0.40 and g > r and g > b:
            return True
    elif target_color == "color_blue":
        if b_ratio > 0.35 and b > r and b > g:
            return True
    
    return False

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to {BROKER}:{PORT}...")
try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    time.sleep(2)
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

print("\n" + "="*40)
print(f"   Player {MY_NAME.upper()} Ready!")
print("   Waiting for game...")
print("="*40 + "\n")

try:
    while True:
        if current_task and not task_completed:
            if check_color(current_task):
                print("\nColor matched! Task done!")
                client.publish(RESULT_TOPIC, "success")
                print("Result sent: success")
                task_completed = True
                current_task = None
                print("\nWaiting for next round...\n")
        
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\n\nGame ended!")
    client.loop_stop()
    client.disconnect()