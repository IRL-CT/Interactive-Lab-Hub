"""
MQTT Shooting Game Server (4-Player Relay & Bot Controller)
Relays MQTT messages and runs AI bots for disconnected players.
"""
import time
import threading
import json
import uuid
import random
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt

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
TOPIC_PLAYER3 = 'IDD/game/player3'
TOPIC_PLAYER4 = 'IDD/game/player4'

ALL_TOPICS = [TOPIC_PLAYER1, TOPIC_PLAYER2, TOPIC_PLAYER3, TOPIC_PLAYER4]
PLAYER_NAMES = ['player1', 'player2', 'player3', 'player4']

mqtt_client = None
mqtt_connected = False

# Game state - NOW ONLY tracks connection times and bot status
game_state = {
    'player1': {'last_message_time': 0, 'bot_active': False},
    'player2': {'last_message_time': 0, 'bot_active': False},
    'player3': {'last_message_time': 0, 'bot_active': False},
    'player4': {'last_message_time': 0, 'bot_active': False},
}

# Lock for thread-safe game state updates
game_state_lock = threading.Lock()

# Bot Configuration
PLAYER_TIMEOUT = 5.0  # Seconds of inactivity before bot takes over
BOT_TICK_RATE = 0.5   # How often the bot makes a decision

# ========== MQTT FUNCTIONS ==========

def on_connect(client, userdata, flags, rc):
    """MQTT connected"""
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print(f'[OK] MQTT connected to {MQTT_BROKER}:{MQTT_PORT}')
        for topic in ALL_TOPICS:
            client.subscribe(topic)
            print(f'[OK] Subscribed to {topic}')
    else:
        mqtt_connected = False
        print(f'[FAIL] MQTT connection failed: {rc}')

def on_disconnect(client, userdata, rc):
    """MQTT disconnected"""
    global mqtt_connected
    mqtt_connected = False
    print(f'[FAIL] MQTT disconnected: {rc}')
    if rc != 0:
        print("  Attempting to reconnect...")

def on_message(client, userdata, msg):
    """MQTT message received - update timestamp and relay"""
    try:
        payload_str = msg.payload.decode('utf-8')
        payload = json.loads(payload_str)
        player_name = None

        if msg.topic == TOPIC_PLAYER1:
            player_name = 'player1'
        elif msg.topic == TOPIC_PLAYER2:
            player_name = 'player2'
        elif msg.topic == TOPIC_PLAYER3:
            player_name = 'player3'
        elif msg.topic == TOPIC_PLAYER4:
            player_name = 'player4'

        if player_name:
            # Update last message time to prevent bot takeover
            with game_state_lock:
                game_state[player_name]['last_message_time'] = time.time()
        
        # Relay message to all web clients
        message_data = {
            'topic': msg.topic,
            'payload': payload,
            'timestamp': time.time()
        }
        socketio.emit('mqtt_message', message_data)
        
    except Exception as e:
        print(f'Error processing message: {e}')

def start_mqtt_client():
    """Start MQTT client with reconnection"""
    global mqtt_client
    try:
        mqtt_client = mqtt.Client(str(uuid.uuid1()))
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message
        mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)
        mqtt_client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        print('[OK] MQTT client started')
        return True
    except Exception as e:
        print(f'[FAIL] MQTT client failed: {e}')
        return False

# ========== BOT CONTROLLER ==========

def bot_controller():
    """
    Checks for disconnected players and publishes bot commands.
    """
    print(f"[BOT] Bot Controller thread started. Timeout: {PLAYER_TIMEOUT}s, Tick: {BOT_TICK_RATE}s")
    while True:
        try:
            with game_state_lock:
                now = time.time()
                for player_name in PLAYER_NAMES:
                    player_state = game_state[player_name]
                    is_disconnected = (now - player_state['last_message_time']) > PLAYER_TIMEOUT
                    
                    if is_disconnected:
                        # This player is a bot now
                        if not player_state['bot_active']:
                            print(f"[BOT] Player {player_name} timed out. Activating bot.")
                            player_state['bot_active'] = True
                            socketio.emit('bot_status', {'player': player_name, 'active': True})
                        
                        run_bot_logic(player_name)
                    else:
                        # This player is human-controlled
                        if player_state['bot_active']:
                            print(f"[BOT] Player {player_name} reconnected. Deactivating bot.")
                            player_state['bot_active'] = False
                            socketio.emit('bot_status', {'player': player_name, 'active': False})

            time.sleep(BOT_TICK_RATE)
        except Exception as e:
            print(f"[BOT] Error in bot loop: {e}")
            time.sleep(5) # Avoid spamming errors

def run_bot_logic(player_name):
    """Generates and publishes a random command for a bot player."""
    
    # Simple bot: move randomly and shoot sometimes
    bot_joy_x = random.uniform(-1, 1)
    bot_joy_y = random.uniform(-1, 1)
    bot_shoot = random.random() < 0.05 # 5% chance to shoot per tick
    
    payload = {
        "joy_x": bot_joy_x,
        "joy_y": bot_joy_y,
        "shoot": bot_shoot,
        "timestamp": time.time()
    }
    
    topic = f'IDD/game/{player_name}'
    
    if mqtt_client and mqtt_connected:
        try:
            mqtt_client.publish(topic, json.dumps(payload))
        except Exception as e:
            print(f"[BOT] Failed to publish bot message to {topic}: {e}")

# ========== FLASK ROUTES ==========

@app.route('/')
def index():
    """Main game page"""
    return render_template('game.html')

@app.route('/controller')
def controller():
    """Controller page for testing"""
    return render_template('controller.html')

# ========== SOCKET.IO HANDLERS ==========

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print('[IO] Web client connected')
    # Send current bot status to new client
    with game_state_lock:
        for player_name in PLAYER_NAMES:
            emit('bot_status', {'player': player_name, 'active': game_state[player_name]['bot_active']})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print('[IO] Web client disconnected')

@socketio.on('restart_game')
def handle_restart():
    """Reset bot timers"""
    print('[GAME] Restart signal received. Resetting bot timers.')
    with game_state_lock:
        for player_name in PLAYER_NAMES:
            game_state[player_name]['last_message_time'] = time.time() # Give players time to reconnect
            if game_state[player_name]['bot_active']:
                game_state[player_name]['bot_active'] = False
                socketio.emit('bot_status', {'player': player_name, 'active': False}, broadcast=True)
    
    emit('game_state', {}, broadcast=True) # Send a generic reset, though client handles it

# ========== MAIN ==========

if __name__ == '__main__':
    print("=" * 60)
    print("  MQTT 4-PLAYER SHOOTING GAME SERVER (RELAY & BOTS)")
    print("=" * 60)
    print(f"  Game URL:     http://0.0.0.0:5002")
    print(f"  MQTT Broker:  {MQTT_BROKER}:{MQTT_PORT}")
    print("=" * 60)
    
    # Start MQTT client
    if not start_mqtt_client():
        print("[WARN] MQTT failed to start, exiting...")
        exit(1)
    
    # Start bot controller thread
    bot_thread = threading.Thread(
        target=bot_controller,
        daemon=True,
        name="BotController"
    )
    bot_thread.start()
    
    print("[OK] All systems started. Running Flask server.")
    print("=" * 60)
    
    # Run Flask app
    socketio.run(app, host='0.0.0.0', port=5002, debug=False)