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
        socketio = userdata['socketio']
        pixels = userdata['pixels']
        
        mac = data.get('mac')
        r = int(data.get('r', 0))
        g = int(data.get('g', 0))
        b = int(data.get('b', 0))
        
        # Validate
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        # Check if new pixel
        is_new = mac not in pixels
        
        if is_new:
            # Import here to avoid circular dependency
            from datetime import datetime
            # Assign next available position
            position = len(pixels)
            pixels[mac] = {
                'color': [r, g, b],
                'position': position,
                'last_update': datetime.now()
            }
            print(f'✓ MQTT pixel: {mac[:17]} at position {position} RGB({r},{g},{b})')
        else:
            from datetime import datetime
            # Update existing pixel
            pixels[mac]['color'] = [r, g, b]
            pixels[mac]['last_update'] = datetime.now()
        
        # Broadcast to all clients
        socketio.emit('pixel_update', {
            'mac': mac,
            'color': [r, g, b],
            'position': pixels[mac]['position'],
            'is_new': is_new,
            'total': len(pixels)
        }, namespace='/')
        
    except Exception as e:
        print(f'Error processing MQTT message: {e}')


def start_mqtt_bridge(socketio_instance, pixels_dict):
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
        mqtt_client.user_data_set({'socketio': socketio_instance, 'pixels': pixels_dict})
        
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
