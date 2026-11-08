"""Publish one simulated action, or type actions in an interactive session."""
import argparse
import logging
from station import Station
import config


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--role', choices=('feed', 'play', 'rest'))
    group.add_argument('--reset', action='store_true', help='Manual new game (also works in hardware mode)')
    group.add_argument('--interactive', action='store_true')
    p.add_argument('--debug', action='store_true')
    args = p.parse_args()
    config.logging_setup(args.debug)
    client = Station('sim-console')
    client.mqtt.start()
    try:
        client.wait_ready()
        if args.interactive:
            print('SIMULATION / DEVELOPER MODE. Engine needs --allow-simulation. Wait 3s between actions.')
            while True:
                action = input('feed / play / rest / reset / quit > ').strip().lower()
                if action in ('q', 'quit'):
                    break
                if action not in ('feed', 'play', 'rest', 'reset'):
                    continue
                client.device_id = 'sim-' + action
                try:
                    client.send(action, simulated=action != 'reset')
                except (ConnectionError, TimeoutError) as exc:
                    print(exc)
        else:
            action = 'reset' if args.reset else args.role
            client.device_id = 'sim-' + action
            client.send(action, simulated=action != 'reset')
    except (ConnectionError, TimeoutError) as exc:
        p.exit(1, str(exc) + '\n')
    except (KeyboardInterrupt, EOFError):
        logging.info('Stopped')
    finally:
        client.mqtt.close()


if __name__ == '__main__':
    main()
