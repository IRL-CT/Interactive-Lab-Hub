"""
MQTT Message Viewer
Lightweight debugging tool to view all MQTT messages in real-time
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
from datetime import datetime
from collections import deque
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mqtt-viewer-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store recent messages (limited to prevent memory issues)
MAX_MESSAGES = 100
recent_messages = deque(maxlen=MAX_MESSAGES)

# MQTT Configuration
MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_TOPIC = 'IDD/#'  # Subscribe to all IDD topics
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
    """MQTT message received - broadcast to web clients"""
    try:
        # Try to parse as JSON, otherwise use as plain text
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            payload_str = json.dumps(payload, indent=2)
            is_json = True
        except:
            payload_str = msg.payload.decode('utf-8', errors='replace')
            is_json = False
        
        # Create message object
        message = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'topic': msg.topic,
            'payload': payload_str,
            'is_json': is_json
        }
        
        # Add to recent messages
        recent_messages.append(message)
        
        # Broadcast to all connected web clients
        socketio.emit('mqtt_message', message, namespace='/')
        
    except Exception as e:
        print(f'Error processing message: {e}')


def start_mqtt_client():
    """Start MQTT client"""
    global mqtt_client
    
    try:
        import uuid
        mqtt_client = mqtt.Client(str(uuid.uuid1()))
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        
        mqtt_client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        
        print('MQTT viewer started')
        return True
        
    except Exception as e:
        print(f'⚠️  MQTT client failed: {e}')
        return False


@app.route('/')
def index():
    """Main viewer page"""
    return render_template('mqtt_viewer.html')


@socketio.on('connect')
def handle_connect():
    """Client connected - send recent messages"""
    print(f'Web client connected')
    # Send recent messages to newly connected client
    for msg in recent_messages:
        emit('mqtt_message', msg)


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print(f'Web client disconnected')


@socketio.on('clear_messages')
def handle_clear():
    """Clear message history"""
    recent_messages.clear()
    emit('messages_cleared', broadcast=True)
    print('Messages cleared')


@socketio.on('update_filter')
def handle_filter(data):
    """Update topic filter settings"""
    # Just acknowledge - filtering happens client-side
    print(f'Filter updated: {data}')
    emit('filter_updated', data)


if __name__ == '__main__':
    print("=" * 60)
    print("  MQTT Message Viewer")
    print("=" * 60)
    print(f"  Viewer URL:  http://0.0.0.0:5001")
    print(f"  Monitoring:  {MQTT_TOPIC} on {MQTT_BROKER}")
    print("=" * 60)
    
    # Start MQTT client
    start_mqtt_client()
    
    print("=" * 60)
    print()
    
    # Run Flask app on port 5001 (different from main app)
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
