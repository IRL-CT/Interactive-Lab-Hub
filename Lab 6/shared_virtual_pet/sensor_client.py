"""One station program for all three Raspberry Pis."""
import argparse
import logging
import statistics
import time
import config
from display import PetDisplay
from sensor_triggers import CycleTrigger, GestureTrigger, is_food
from station import Station


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--role', choices=('feed', 'play', 'rest'), required=True)
    p.add_argument('--device-id', help='Default: role mapping from .env')
    p.add_argument('--simulate', action='store_true', help='Send one simulated action and exit')
    p.add_argument('--no-display', action='store_true')
    p.add_argument('--debug', action='store_true')
    p.add_argument('--play-mode', choices=('gesture', 'proximity'), default='gesture')
    p.add_argument('--red-min', type=float, default=.46)
    p.add_argument('--blue-max', type=float, default=.25)
    p.add_argument('--clear-min', type=int, default=10)
    p.add_argument('--stable-readings', type=int, default=3)
    p.add_argument('--dark-ratio', type=float, default=.25)
    p.add_argument('--release-ratio', type=float, default=.55)
    p.add_argument('--dark-hold', type=float, default=2)
    p.add_argument('--proximity-near', type=int, default=100)
    p.add_argument('--proximity-far', type=int, default=40)
    p.add_argument('--gain', type=int, choices=range(4), default=1, help='0=1x, 1=4x, 2=16x, 3=64x')
    p.add_argument('--integration-cycles', type=int, default=10, help='Each cycle is 2.78ms (1..256)')
    p.add_argument('--gesture-rotation', type=int, choices=(0, 90, 180, 270), default=0)
    return p


def main():
    p = parser()
    a = p.parse_args()
    if not (0 < a.dark_ratio < a.release_ratio < 1 and 0 <= a.proximity_far < a.proximity_near <= 255
            and 1 <= a.integration_cycles <= 256 and a.stable_readings > 0 and a.dark_hold > 0
            and 0 < a.red_min < 1 and 0 < a.blue_max < 1):
        p.error('Invalid calibration thresholds')
    config.logging_setup(a.debug)
    device = a.device_id or ('sim-' + a.role if a.simulate else config.DEVICES[a.role])
    station = Station(device)
    display = PetDisplay(a.role, a.no_display or a.simulate)
    i2c = None
    station.mqtt.start()
    try:
        if a.simulate:
            station.wait_ready()
            station.send(a.role, True)
            return
        try:
            import board
            import busio
            from adafruit_apds9960.apds9960 import APDS9960
            i2c = busio.I2C(board.SCL, board.SDA)
            sensor = APDS9960(i2c, rotation=a.gesture_rotation)
            sensor.enable_color = a.role != 'play'
            sensor.color_gain = a.gain
            sensor.color_integration_time = a.integration_cycles
            sensor.enable_proximity = a.role == 'play'
            sensor.enable_gesture = a.role == 'play' and a.play_mode == 'gesture'
        except Exception as exc:
            raise RuntimeError(f'APDS-9960 initialization failed: {exc}. Check I2C/0x39; use --simulate for laptop testing.') from exc
        baseline = 0
        if a.role == 'rest':
            logging.info('Rest calibration: leave sensor UNCOVERED for 3 seconds')
            samples = []
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if sensor.color_data_ready:
                    samples.append(sensor.color_data[3])
                time.sleep(.1)
            baseline = statistics.median(samples) if samples else 0
            if baseline < a.clear_min:
                raise RuntimeError('Ambient light too low to calibrate. Add light and restart.')
            logging.info('Clear baseline %.1f; cover < %.1f; release > %.1f', baseline,
                         baseline * a.dark_ratio, baseline * a.release_ratio)
        trigger = CycleTrigger(a.stable_readings, a.dark_hold if a.role == 'rest' else 0)
        gesture = GestureTrigger()
        feedback, until, pending = '', 0, None
        logging.info('Station %s (%s) ready; debug=%s', a.role, device, a.debug)
        while True:
            now = time.monotonic()
            fire = False
            if a.role == 'play':
                if a.play_mode == 'gesture':
                    value = sensor.gesture()
                    fire = gesture.update(value, now)
                    logging.debug('gesture=%s (3=left 4=right)', value)
                else:
                    value = sensor.proximity
                    fire = trigger.update(value >= a.proximity_near, value <= a.proximity_far, now)
                    logging.debug('proximity=%s', value)
            elif sensor.color_data_ready:
                r, g, b, clear = sensor.color_data
                total = max(1, r + g + b)
                logging.debug('RGB=(%s,%s,%s) normalized=(%.2f,%.2f,%.2f) clear=%s',
                              r, g, b, r / total, g / total, b / total, clear)
                if a.role == 'feed':
                    active = is_food(r, g, b, clear, a.red_min, a.blue_max, a.clear_min)
                    fire = trigger.update(active, not active, now)
                else:
                    fire = trigger.update(clear < baseline * a.dark_ratio,
                                          clear > baseline * a.release_ratio, now)
            if fire:
                try:
                    pending = station.send(a.role)['event_id']
                    feedback = 'Sent; awaiting engine'
                except (ConnectionError, TimeoutError) as exc:
                    logging.warning('%s', exc)
                    feedback = 'Offline / retry action'
                until = time.monotonic() + 4
            snap = station.snapshot()
            if pending and snap['state'] and snap['state'].get('last_event_id') == pending:
                feedback, pending, until = a.role.title() + ' accepted!', None, time.monotonic() + 3
            display.show(snap, feedback if time.monotonic() < until else '')
            time.sleep(.1)
    except KeyboardInterrupt:
        logging.info('Station stopped')
    except (RuntimeError, ConnectionError, TimeoutError, OSError) as exc:
        p.exit(1, str(exc) + '\n')
    finally:
        station.mqtt.close()
        display.close()
        if i2c:
            i2c.deinit()


if __name__ == '__main__':
    main()
