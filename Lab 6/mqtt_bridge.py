"""
MQTT Bridge for Pixel Grid
Enable this to connect MQTT -> WebSocket
"""

import paho.mqtt.client as mqtt
import ssl
import json
from flask_socketio import SocketIO

# MQTT Configuration
MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_TOPIC = 'IDD/pixelgrid/colors'
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

mqtt_client = None


def on_connect(client, userdata, flags, rc):
    """MQTT connected"""
    if rc == 0:
        print(f'✓ MQTT connected to {MQTT_BROKER}:{MQTT_PORT}')
        client.subscribe(MQTT_TOPIC)
        print(f'✓ Subscribed to {MQTT_TOPIC}')
    else:
        print(f'✗ MQTT connection failed: {rc}')


def on_message(client, userdata, msg):
    """MQTT message received - forward to WebSocket"""
    try:
        data = json.loads(msg.payload.decode('UTF-8'))
        
        # Forward to WebSocket with pixel_update event (matches what frontend expects)
        socketio = userdata['socketio']
        socketio.emit('pixel_update', {
            'mac': data.get('mac'),
            'r': data.get('r', 0),
            'g': data.get('g', 0),
            'b': data.get('b', 0)
        })
        
        print(f'MQTT → WS: {data.get("mac", "unknown")[:17]}')
        
    except Exception as e:
        print(f'Error processing MQTT message: {e}')


def start_mqtt_bridge(socketio_instance):
    """Start MQTT client that forwards to WebSocket"""
    global mqtt_client
    
    try:
        import uuid
        mqtt_client = mqtt.Client(str(uuid.uuid1()))
        
        # Only use TLS if port is 8883
        if MQTT_PORT == 8883:
            mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.user_data_set({'socketio': socketio_instance})
        
        mqtt_client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        
        print('MQTT bridge started')
        return True
        
    except Exception as e:
        print(f'⚠️  MQTT bridge failed: {e}')
        print('    Server will run with WebSocket only')
        return False


def stop_mqtt_bridge():
    """Stop MQTT client"""
    global mqtt_client
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print('MQTT bridge stopped')
