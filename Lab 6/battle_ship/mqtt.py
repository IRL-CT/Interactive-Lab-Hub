import paho.mqtt.client as mqtt
import ssl
import json
import uuid
import threading
import queue

MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_TOPIC = 'IDD/battleship/game'
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

mqtt_client = None
game_event = threading.Event()
latest_message = None
event_queue = queue.Queue()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f'Connected to {MQTT_BROKER}:{MQTT_PORT}')
        client.subscribe(MQTT_TOPIC)
        print(f'Subscribed to topic: {MQTT_TOPIC}')
    else:
        print(f'MQTT connection failed: {rc}')

def on_message(client, userdata, msg):
    global latest_message
    try:
        payload = msg.payload.decode('utf-8')
        data = {}
        try:
            data = json.loads(payload)
        except Exception:
            data = {'raw': payload}
        latest_message = data
        game_event.set()
        try:
            event_queue.put_nowait(data)
        except queue.Full:
            pass
        print(f'Received: {data}')
    except Exception as e:
        print(f'Error in on_message: {e}')

def wait_for_message(timeout=None):
    """Block until any MQTT message is received."""
    global latest_message
    if game_event.wait(timeout):
        game_event.clear()
        msg = latest_message
        latest_message = None
        return msg
    return None

def start_mqtt():
    global mqtt_client
    try:
        mqtt_client = mqtt.Client(str(uuid.uuid1()))
        if MQTT_PORT == 8883:
            mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        print('MQTT bridge started.')
        return True
    except Exception as e:
        print(f'MQTT failed to start: {e}')
        return False

def stop_mqtt():
    global mqtt_client
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        mqtt_client = None
        print('MQTT stopped.')

def send_message(payload):
    """Send any message to the unified topic."""
    global mqtt_client
    if not mqtt_client:
        print('MQTT not running')
        return False
    try:
        mqtt_client.publish(MQTT_TOPIC, json.dumps(payload), qos=1)
        print(f'→ Published: {payload}')
        return True
    except Exception as e:
        print(f'Error publishing: {e}')
        return False

