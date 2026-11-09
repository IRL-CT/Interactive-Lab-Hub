"""Run exactly one engine for a project namespace, on Pi 1 OR laptop."""
import argparse
import fcntl
import hashlib
import logging
from pathlib import Path
import queue
import tempfile
import time
import config
from events import validate_event
from mqtt_client import MQTTConnection
from pet_logic import PetGame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-simulation', action='store_true')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    config.logging_setup(args.debug)
    key = hashlib.sha256(f'{config.BROKER}:{config.PORT}/{config.PREFIX}'.encode()).hexdigest()[:16]
    lock = open(Path(tempfile.gettempdir()) / f'sharedpet-{key}.lock', 'a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.exit(1, 'An engine for this broker/namespace is already running on this machine.\n')
    inbox = queue.Queue(maxsize=256)

    def receive(msg):
        if msg.retain:
            logging.warning('Ignoring retained action')
            return
        try:
            inbox.put_nowait((msg.topic.rsplit('/', 1)[-1], msg.payload))
        except queue.Full:
            logging.warning('Event queue full; ignoring excess input')

    game = PetGame(time.monotonic())
    mqtt = MQTTConnection('engine', ('event/+', 'control/reset'), receive)
    mqtt.start()
    logging.info('New round %s; simulation=%s. Only ONE engine across all machines!', game.round_id, args.allow_simulation)
    last_publish = 0
    try:
        while True:
            now = time.monotonic()
            game.tick(now)
            changed = False
            # Bound each batch so floods cannot starve game clock or publication.
            for _ in range(100):
                try:
                    action, payload = inbox.get_nowait()
                except queue.Empty:
                    break
                try:
                    event = validate_event(payload, action, game.round_id, config.DEVICES, args.allow_simulation)
                    accepted, reason = game.apply(event, time.monotonic())
                    logging.info('%s %s from %s [%s]: %s', 'SIM' if event.get('simulated') else 'REAL',
                                 action, event['device_id'], event['event_id'], reason)
                    changed |= accepted
                except ValueError as exc:
                    logging.warning('Rejected event: %s', exc)
            if mqtt.connected.is_set() and (changed or now - last_publish >= 1):
                state = {**game.snapshot(), 'published_at': time.time()}
                try:
                    mqtt.publish('state', state, retain=True)
                    last_publish = now
                except ConnectionError as exc:
                    logging.warning('%s', exc)
            time.sleep(.05)
    except KeyboardInterrupt:
        logging.info('Engine stopped; restart begins a new round')
    finally:
        mqtt.close()
        lock.close()


if __name__ == '__main__':
    main()
