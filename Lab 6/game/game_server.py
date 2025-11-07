"""
MQTT Shooting Game Server
Backend server that bridges MQTT messages to web clients via Socket.IO
"""
import time
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
from datetime import datetime
from joystick import JoystickEvent

import json
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shooting-game-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# MQTT Configuration
MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

# Game topics
TOPIC_PLAYER1 = 'IDD/game/player1'
TOPIC_PLAYER2 = 'IDD/game/player2'

mqtt_client = None

# Game state
game_state = {
    'player1': {
        'x': 50,
        'y': 300,
        'target_x': 50,
        'target_y': 300,
        'hits': 0,
        'alive': True
    },
    'player2': {
        'x': 1150,
        'y': 300,
        'target_x': 1150,
        'target_y': 300,
        'hits': 0,
        'alive': True
    },
    'bullets': [],
    'game_over': False,
    'winner': None
}

# ========== JOYSTICK INTEGRATION ==========

def start_joystick_controller(player_number):
    """Start joystick controller in background thread"""
    try:
        joystick = JoystickEvent(player_number=player_number)
        joystick.run()  # This will continuously read hardware and publish
    except Exception as e:
        print(f"Joystick controller error: {e}")

# ========== MQTT FUNCTIONS ==========

def on_connect(client, userdata, flags, rc):
    """MQTT connected"""
    if rc == 0:
        print(f'MQTT connected to {MQTT_BROKER}:{MQTT_PORT}')
        client.subscribe(TOPIC_PLAYER1)
        client.subscribe(TOPIC_PLAYER2)
        print(f'Subscribed to game topics')
    else:
        print(f'MQTT connection failed: {rc}')


def on_message(client, userdata, msg):
    """MQTT message received - process game controls"""
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        
        # Broadcast to all connected web clients
        message_data = {
            'topic': msg.topic,
            'payload': payload
        }
        
        socketio.emit('mqtt_message', message_data, namespace='/')
        
    except Exception as e:
        print(f'Error processing message: {e}')


def start_mqtt_client():
    """Start MQTT client"""
    global mqtt_client
    
    try:
        mqtt_client = mqtt.Client(str(uuid.uuid1()))
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        
        mqtt_client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        
        print('MQTT client started')
        return True
        
    except Exception as e:
        print(f'MQTT client failed: {e}')
        return False


@app.route('/')
def index():
    """Main game page"""
    return render_template('game.html')


@app.route('/controller')
def controller():
    """Controller page for testing"""
    return render_template('controller.html')


@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print('Web client connected')
    # Send current game state
    emit('game_state', game_state)


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print('Web client disconnected')

@socketio.on('mqtt_publish')
def handle_mqtt_publish(data):
    topic = data['topic']
    message = data['message']
    mqtt_client.publish(topic, message)
    
@socketio.on('restart_game')
def handle_restart():
    """Reset game state"""
    global game_state
    
    game_state = {
        'player1': {
            'x': 50,
            'y': 300,
            'target_x': 50,
            'target_y': 300,
            'hits': 0,
            'alive': True
        },
        'player2': {
            'x': 1150,
            'y': 300,
            'target_x': 1150,
            'target_y': 300,
            'hits': 0,
            'alive': True
        },
        'bullets': [],
        'game_over': False,
        'winner': None
    }
    
    emit('game_state', game_state, broadcast=True)
    print('Game restarted')


@socketio.on('update_config')
def handle_config(data):
    """Update MQTT configuration (topic prefixes, etc)"""
    print(f'Config updated: {data}')
    # Could implement dynamic topic changes here
    emit('config_updated', data)


if __name__ == '__main__':
    print("=" * 60)
    print("  MQTT Shooting Game Server")
    print("=" * 60)
    print(f"  Game URL:     http://0.0.0.0:5002")
    print(f"  Controller:   http://0.0.0.0:5002/controller")
    print(f"  MQTT Broker:  {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  Topics:")
    print(f"    Player 1:   {TOPIC_PLAYER1}")
    print(f"    Player 2:   {TOPIC_PLAYER2}")
    print("=" * 60)
    
    # Start MQTT client
    start_mqtt_client()
    
    joystick1_thread = threading.Thread(
        target=start_joystick_controller,
        args=(1,),
        daemon=True
    )
    joystick1_thread.start()
    
    print("=" * 60)
    print()
    
    # Run Flask app on port 5002
    socketio.run(app, host='0.0.0.0', port=5002, debug=False, allow_unsafe_werkzeug=True)