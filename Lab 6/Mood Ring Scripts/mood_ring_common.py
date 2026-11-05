"""Shared MQTT settings for the mood ring.

Change the team name if another group is using "moodring" on the
same broker:  MOODRING_TEAM=team3 python mood_ring_server.py
"""

import os

MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

TEAM = os.environ.get('MOODRING_TEAM', 'moodring')
COLOR_TOPIC = f'IDD/{TEAM}/colors'
