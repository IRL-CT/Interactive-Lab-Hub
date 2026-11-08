"""
Telephone Charades: shared settings, MQTT topics and a small wrapper around paho-mqtt.

Every Pi (and the host) imports this, so they all agree on the broker and the topic names.
All topics live under IDD/<team>/charades/..., the team's own space on the class broker.

    IDD/<team>/charades/players/<name>   retained   a player says "I'm here" (empty = left)
    IDD/<team>/charades/state            retained   the host's game state (phase, round, who does what)
    IDD/<team>/charades/submit                      a player hands in an acting clip or a guess
    IDD/<team>/charades/clip/<game>/<key>           one JPEG frame of an acting clip
    IDD/<team>/charades/control                     "start" (a player holds the button in the lobby)
    IDD/<team>/charades/want                        "please resend clip <key>" (a Pi that restarted)
"""
import base64
import json
import random
import threading
import time
import uuid

VERSION = "1.4"          # every Pi must run the same version; the host warns when they don't

BROKER = "farlab.infosci.cornell.edu"
PORT = 1883
USERNAME = "idd"
PASSWORD = "device@theFarm"
DEFAULT_TEAM = "charades-arnav"

PROMPTS = [
    "brushing your teeth", "riding a horse", "playing the guitar", "a cat chasing a laser",
    "swimming", "making a pizza", "lifting heavy weights", "taking a selfie", "skiing",
    "flying a kite", "playing basketball", "a T-rex eating", "walking a big dog", "a zombie",
    "rowing a boat", "drinking very hot coffee", "doing yoga", "a robot dancing", "playing the drums",
    "fishing", "a chicken", "boxing", "painting a wall", "riding a bike", "a monkey",
    "putting on tight jeans", "conducting an orchestra", "a ballerina", "chopping onions",
    "climbing a ladder", "playing tennis", "surfing", "a penguin", "typing on a laptop",
    "blowing up a balloon", "shoveling snow", "a superhero flying", "milking a cow",
    "juggling", "walking on ice", "a magician pulling a rabbit out of a hat", "bowling",
]


def topics(team):
    base = f"IDD/{team}/charades"
    return {
        "base": base,
        "players": f"{base}/players",
        "state": f"{base}/state",
        "submit": f"{base}/submit",
        "clip": f"{base}/clip",
        "control": f"{base}/control",
        "want": f"{base}/want",
    }


def default_rounds(n):
    """Alternate act / guess and always end on a guess, so every chain ends with words to compare.
    3 players -> 4 rounds (act, guess, act, guess). In the last round you see what became of your own prompt."""
    return n if n % 2 == 0 else n + 1


def pick_prompts(n, pool=None, rng=random):
    pool = list(pool or PROMPTS)
    return rng.sample(pool, n) if n <= len(pool) else [rng.choice(pool) for _ in range(n)]


def b64(data):
    return base64.b64encode(data).decode()


def unb64(text):
    return base64.b64decode(text)


def topic_matches(pattern, topic):
    """MQTT wildcard match: + is one level, # is the rest."""
    p, t = pattern.split("/"), topic.split("/")
    for i, part in enumerate(p):
        if part == "#":
            return True
        if i >= len(t) or (part != "+" and part != t[i]):
            return False
    return len(p) == len(t)


def decode(payload):
    if not payload:
        return None
    try:
        return json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        return None


class Bus:
    """paho-mqtt with the few things the game needs: subscribe with a handler, publish JSON,
    resubscribe after a reconnect, and a last will. Works with paho-mqtt 1.x and 2.x."""

    def __init__(self, name, broker=BROKER, port=PORT, username=USERNAME, password=PASSWORD):
        import paho.mqtt.client as mqtt
        cid = f"charades-{name}-{uuid.uuid4().hex[:6]}"
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=cid)
        except AttributeError:                       # paho-mqtt 1.x
            self.client = mqtt.Client(client_id=cid)
        self.client.username_pw_set(username, password)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.broker, self.port = broker, port
        self.handlers = []
        self.hooks = []                              # called after every (re)connect
        self.connected = threading.Event()
        self.client.reconnect_delay_set(1, 10)

    def will(self, topic, payload=b"", retain=True):
        self.client.will_set(topic, payload, qos=1, retain=retain)

    def on_connected(self, fn):
        """Run fn() after every (re)connect, e.g. to say "I'm here" again after the Wi-Fi dropped."""
        self.hooks.append(fn)

    def subscribe(self, pattern, handler):
        self.handlers.append((pattern, handler))
        if self.connected.is_set():
            self.client.subscribe(pattern, qos=1)

    def publish(self, topic, obj, retain=False, qos=1):
        payload = obj if isinstance(obj, (bytes, str)) else json.dumps(obj)
        return self.client.publish(topic, payload, qos=qos, retain=retain)

    def start(self, timeout=15):
        self.client.connect_async(self.broker, self.port, keepalive=30)
        self.client.loop_start()
        if not self.connected.wait(timeout):
            raise ConnectionError(f"could not reach the MQTT broker {self.broker}:{self.port} "
                                  f"(on Cornell wifi? try: ping {self.broker})")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    # -- paho callbacks
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            for pattern, _ in self.handlers:
                client.subscribe(pattern, qos=1)
            self.connected.set()
            for fn in self.hooks:
                threading.Thread(target=fn, daemon=True).start()
        else:
            print(f"[mqtt] connection refused (code {rc})", flush=True)

    def _on_disconnect(self, client, userdata, rc):
        self.connected.clear()
        if rc != 0:
            print("[mqtt] lost the broker, reconnecting...", flush=True)

    def _on_message(self, client, userdata, msg):
        for pattern, handler in self.handlers:
            if topic_matches(pattern, msg.topic):
                try:
                    handler(msg.topic, msg.payload)
                except Exception as err:            # one bad message must not kill the device
                    print(f"[mqtt] error handling {msg.topic}: {err}", flush=True)


def now():
    return time.time()


class Log:
    """print() that also keeps a copy in charades/logs/<name>-<date-time>.log, so after a game we can
    see exactly what each Pi received and sent."""

    def __init__(self, name, echo=True, folder=None):
        import pathlib
        self.echo = echo
        self.path = None
        try:
            d = pathlib.Path(folder or pathlib.Path(__file__).resolve().parent / "logs")
            d.mkdir(exist_ok=True)
            self.path = d / f"{name}-{time.strftime('%Y%m%d-%H%M%S')}.log"
        except OSError:
            pass
        self.lock = threading.Lock()

    def __call__(self, *parts):
        msg = " ".join(str(p) for p in parts)
        if self.echo:
            print(msg, flush=True)
        if self.path:
            with self.lock, open(self.path, "a") as f:
                for line in msg.splitlines() or [""]:
                    f.write(f"{time.strftime('%H:%M:%S')} {line}\n")
