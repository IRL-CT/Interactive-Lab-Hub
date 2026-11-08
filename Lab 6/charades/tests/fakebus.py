"""An in-memory MQTT broker for tests: same interface as common.Bus, retained messages, last wills,
and delivery on a separate thread (like a real broker), so whole games can run without a network."""
import queue
import threading

from common import topic_matches


class FakeBroker:
    def __init__(self):
        self.retained = {}
        self.clients = []
        self.q = queue.Queue()
        self.log = []
        self.lose = None          # lose(topic, payload) -> True loses the message in transit (a flaky network)
        threading.Thread(target=self._deliver, daemon=True).start()

    def _deliver(self):
        while True:
            client, topic, payload = self.q.get()
            client._dispatch(topic, payload)
            self.q.task_done()

    def publish(self, topic, payload, retain=False):
        if isinstance(payload, str):
            payload = payload.encode()
        self.log.append((topic, len(payload)))
        if self.lose and self.lose(topic, payload):
            return
        if retain:
            if payload:
                self.retained[topic] = payload
            else:
                self.retained.pop(topic, None)
        for c in list(self.clients):
            if any(topic_matches(p, topic) for p, _ in c.handlers):
                self.q.put((c, topic, payload))

    def connect(self, client):
        self.clients.append(client)
        for topic, payload in list(self.retained.items()):
            if any(topic_matches(p, topic) for p, _ in client.handlers):
                self.q.put((client, topic, payload))

    def drop(self, client):
        """The client vanished without saying goodbye: fire its last will."""
        self.clients.remove(client)
        if client._will:
            self.publish(*client._will)

    def settle(self):
        self.q.join()


class FakeBus:
    def __init__(self, name, broker):
        import json
        self.json = json
        self.name, self.broker = name, broker
        self.handlers, self.hooks = [], []
        self.connected = threading.Event()
        self._will = None

    def will(self, topic, payload=b"", retain=True):
        self._will = (topic, payload, retain)

    def on_connected(self, fn):
        self.hooks.append(fn)

    def subscribe(self, pattern, handler):
        self.handlers.append((pattern, handler))

    def publish(self, topic, obj, retain=False, qos=1):
        payload = obj if isinstance(obj, (bytes, str)) else self.json.dumps(obj)
        self.broker.publish(topic, payload, retain)

    def start(self, timeout=5):
        self.broker.connect(self)
        self.connected.set()
        for fn in self.hooks:
            fn()

    def stop(self):
        if self in self.broker.clients:
            self.broker.clients.remove(self)
        self.connected.clear()

    def _dispatch(self, topic, payload):
        for pattern, handler in self.handlers:
            if topic_matches(pattern, topic):
                handler(topic, payload)
