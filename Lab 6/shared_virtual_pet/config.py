import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))
BROKER = os.getenv('MQTT_BROKER', 'farlab.infosci.cornell.edu')
PORT = int(os.getenv('MQTT_PORT', '1883'))
PREFIX = os.getenv('MQTT_PREFIX', 'IDD/jindi-sharedpet-2026').strip('/')
if not PREFIX or any(c in PREFIX for c in '#+\x00'):
    raise ValueError('MQTT_PREFIX must be a nonempty topic without wildcards')
USERNAME = os.getenv('MQTT_USERNAME')
PASSWORD = os.getenv('MQTT_PASSWORD')
TLS = os.getenv('MQTT_TLS', '0') == '1'
DEVICES = {r: os.getenv(r.upper() + '_DEVICE_ID', 'pi' + str(i))
           for i, r in enumerate(('feed', 'play', 'rest'), 1)}
if len(set(DEVICES.values())) != 3:
    raise ValueError('Each real role must have a different device ID')


def logging_setup(debug=False):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
