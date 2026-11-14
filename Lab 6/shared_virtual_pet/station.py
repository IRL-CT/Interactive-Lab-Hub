"""MQTT state cache and event publisher used by every client."""
import logging
import threading
import time
from events import decode_state, make_event
from mqtt_client import MQTTConnection


class Station:
    def __init__(self, device_id):
        self.device_id = device_id
        self.state = None
        self.received_at = 0
        self.lock = threading.Lock()
        self.mqtt = MQTTConnection(device_id, ('state',), self.receive)

    def receive(self, msg):
        try:
            state = decode_state(msg.payload)
        except (ValueError, UnicodeError) as exc:
            logging.warning('Invalid state: %s', exc)
            return
        with self.lock:
            self.state, self.received_at = state, time.monotonic()

    def snapshot(self):
        with self.lock:
            state = dict(self.state) if self.state else None
            age = time.monotonic() - self.received_at
        # Retained state can survive an engine shutdown; check its timestamp too.
        fresh = bool(state and age < 5 and abs(time.time() - state.get('published_at', 0)) < 5)
        return {'state': state, 'connected': self.mqtt.connected.is_set(), 'fresh': fresh}

    def wait_ready(self, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            snap = self.snapshot()
            if snap['connected'] and snap['fresh']:
                return
            time.sleep(.1)
        raise TimeoutError('No fresh engine state. Check broker credentials, prefix, and engine.')

    def send(self, action, simulated=False):
        snap = self.snapshot()
        if not snap['fresh']:
            raise ConnectionError('Engine state is stale or missing; wait for the engine')
        event = make_event(action, self.device_id, snap['state']['round_id'], simulated)
        self.mqtt.publish('control/reset' if action == 'reset' else 'event/' + action,
                          event, wait=True)
        logging.info('%s %s sent; broker acknowledged, engine acceptance pending (%s)',
                     'SIM' if simulated else 'REAL', action, event['event_id'])
        return event
