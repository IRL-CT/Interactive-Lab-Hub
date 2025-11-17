import sys, json, uuid
from urllib.parse import urlparse
from paho.mqtt import client as mqtt

if len(sys.argv) < 3:
    print("Usage: python wss_sub_test.py <mqtt|ws|wss URL> <topic>")
    sys.exit(1)

url, topic = sys.argv[1], sys.argv[2]
u = urlparse(url)

transport = "websockets" if u.scheme in ("ws","wss") else "tcp"
host = u.hostname or "127.0.0.1"
port = u.port or (443 if u.scheme=="wss" else 80 if u.scheme=="ws" else 1883)
path = u.path if (u.path and u.path != "") else "/"
use_tls = (u.scheme == "wss")

client = mqtt.Client(
    client_id=f"sub-{uuid.uuid4().hex[:6]}",
    transport=transport,
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
)
client.enable_logger()

if transport == "websockets":
    client.ws_set_options(path=path)
    if use_tls:
        client.tls_set()  # system CA

def on_connect(cli, userdata, flags, rc, properties=None):
    print(f"Connected rc={rc}; subscribing {topic}")
    cli.subscribe(topic, qos=0)

def on_message(cli, userdata, msg):
    print(f"{msg.topic} {msg.payload[:120]}{'...' if len(msg.payload)>120 else ''}")

print(f"Connecting to {host}:{port} ({transport}{path})")
client.on_connect = on_connect
client.on_message = on_message
client.connect(host, port, keepalive=60)
client.loop_forever()
