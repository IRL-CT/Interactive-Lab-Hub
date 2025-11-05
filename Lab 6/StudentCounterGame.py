"""
Distributed Bird Guessing Game Server
Bridged Architecture:
- Listens to Web UI via Flask-SocketIO
- Communicates with Pi clients via MQTT
"""

# --- EVENTLET PATCHING ---
# This MUST be at the very top, before any other imports
import eventlet
eventlet.monkey_patch()
# -------------------------

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json
import paho.mqtt.client as mqtt
import random
import time
import os

# --- Flask & Socket.IO Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'idd-bird-game-2025'
socketio = SocketIO(app, async_mode='eventlet')

# --- MQTT Configuration (from your example) ---
MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

# Define our new game topics
MQTT_TOPIC_PREFIX = 'IDD/birdgame'
MQTT_TOPIC_REGISTER = f'{MQTT_TOPIC_PREFIX}/client/register'
MQTT_TOPIC_SUBMIT_GUESS = f'{MQTT_TOPIC_PREFIX}/client/submit_guess'

MQTT_TOPIC_NEW_ROUND = f'{MQTT_TOPIC_PREFIX}/broadcast/new_round'
MQTT_TOPIC_TIMES_UP = f'{MQTT_TOPIC_PREFIX}/broadcast/times_up'
MQTT_TOPIC_ROUND_IDLE = f'{MQTT_TOPIC_PREFIX}/broadcast/round_idle'

# --- Flask Routes ---
@app.route('/')
def index():
    """Serve the main game screen."""
    return render_template('index.html')

# --- Global Game State ---
# Use a thread-safe dictionary for player data
# { 'mac_address': {'guess': int} }
players = {}
GAME_STATE = 'IDLE'     # IDLE, GUESSING, RESULTS
CORRECT_ANSWER = 0
game_loop_task = None
mqtt_client = None

# Game settings
COUNTDOWN_TIME = 10
RESULTS_TIME = 10
SUBMIT_GRACE_PERIOD = 3


# --- MQTT Bridge Callbacks ---

def handle_pi_registration(mac):
    """A Pi client has registered via MQTT."""
    if not mac:
        return
    
    if mac not in players:
        print(f'MQTT: Pi registered: {mac}')
        players[mac] = {'guess': None}
        
        # --- FIX: Use eventlet.spawn to emit from MQTT thread ---
        eventlet.spawn(
            socketio.emit,
            'player_joined',
            {'mac': mac, 'count': len(players)}
        )
    else:
        print(f'MQTT: Pi re-registered: {mac}')

def handle_pi_guess(mac, guess):
    """A Pi client has submitted a guess via MQTT."""
    if mac in players:
        # Only accept guesses during the GUESSING or RESULTS (grace period) state
        if GAME_STATE == 'GUESSING' or GAME_STATE == 'RESULTS':
            try:
                int_guess = int(guess)
                players[mac]['guess'] = int_guess
                print(f'MQTT: Guess received from {mac}: {int_guess}')
                
                # --- FIX: Use eventlet.spawn to emit live guess from MQTT thread ---
                eventlet.spawn(
                    socketio.emit,
                    'live_guess',
                    {'mac': mac, 'guess': int_guess}
                )
                
            except ValueError:
                print(f'MQTT: Invalid guess from {mac}: {guess}')
        else:
            print(f'MQTT: Guess from {mac} rejected (game not active)')
    else:
        print(f'MQTT: Guess from unknown MAC {mac} rejected')

def on_mqtt_connect(client, userdata, flags, rc):
    """Callback when the server connects to the MQTT broker."""
    if rc == 0:
        print(f"[OK] MQTT Bridge connected to {MQTT_BROKER}")
        # Subscribe to topics FROM the Pi clients
        client.subscribe(MQTT_TOPIC_REGISTER)
        client.subscribe(MQTT_TOPIC_SUBMIT_GUESS)
        print(f"MQTT: Subscribed to {MQTT_TOPIC_REGISTER}")
        print(f"MQTT: Subscribed to {MQTT_TOPIC_SUBMIT_GUESS}")
    else:
        print(f"[ERROR] MQTT Connection failed with code {rc}")

def on_mqtt_message(client, userdata, msg):
    """Callback for all messages received from the broker."""
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        mac = data.get('mac')
        
        print(f"MQTT RX on {msg.topic}: {payload}")

        if msg.topic == MQTT_TOPIC_REGISTER:
            handle_pi_registration(mac)
            
        elif msg.topic == MQTT_TOPIC_SUBMIT_GUESS:
            handle_pi_guess(mac, data.get('guess'))
            
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# --- Background Game Loop ---
def game_loop(mqtt_client):
    """Main game loop, runs in a background green-thread."""
    global GAME_STATE, CORRECT_ANSWER, players

    while True:
        # --- IDLE State ---
        # Wait until a game is started (via Socket.IO)
        while GAME_STATE == 'IDLE':
            socketio.sleep(0.1)
        
        # --- GUESSING State ---
        print("\n" + "="*20 + " NEW ROUND " + "="*20)
        # Reset player guesses for the new round
        for mac in players:
            players[mac]['guess'] = None
            
        CORRECT_ANSWER = random.randint(5, 20)
        print(f"Correct answer is: {CORRECT_ANSWER}")
        
        # --- MQTT PUBLISH ---
        # Tell Pis (via MQTT) about the new round
        mqtt_client.publish(MQTT_TOPIC_NEW_ROUND, json.dumps({
            'bird_count': CORRECT_ANSWER, # Use 'bird_count' for compatibility
            'countdown': COUNTDOWN_TIME
        }))
        
        # --- SOCKET.IO EMIT ---
        # Tell Web UI (via Socket.IO) about the new round
        socketio.emit('new_round', {
            'bird_count': CORRECT_ANSWER, # Use 'bird_count' for compatibility
            'countdown': COUNTDOWN_TIME
        })
        
        # Run countdown
        socketio.sleep(COUNTDOWN_TIME)
        
        
        # --- RESULTS State ---
        GAME_STATE = 'RESULTS'
        print("Time's up! Calculating results...")

        # --- MQTT PUBLISH ---
        # Tell Pis (via MQTT) that time is up
        mqtt_client.publish(MQTT_TOPIC_TIMES_UP)
        
        # Give Pis a grace period to send their final guess
        socketio.sleep(SUBMIT_GRACE_PERIOD)
        
        # Calculate winners
        guesses = []
        winners = []
        min_diff = float('inf')
        
        for mac, data in players.items():
            guess = data['guess']
            guesses.append({'mac': mac, 'guess': guess})
            
            if guess is not None:
                diff = abs(guess - CORRECT_ANSWER)
                if diff < min_diff:
                    min_diff = diff
                    winners = [mac] # New best, clear old list
                elif diff == min_diff:
                    winners.append(mac) # Tied for best
        
        print(f"Winners: {winners} (diff={min_diff})")

        # --- SOCKET.IO EMIT ---
        # Tell Web UI (via Socket.IO) the results
        socketio.emit('show_results', {
            'correct_answer': CORRECT_ANSWER,
            'guesses': guesses,
            'winners': winners
        })
        
        # Display results for a few seconds
        socketio.sleep(RESULTS_TIME)
        
        # --- Back to IDLE ---
        GAME_STATE = 'IDLE'
        print("Returning to IDLE state.")
        
        # --- MQTT PUBLISH ---
        # Tell Pis (via MQTT) to go idle
        mqtt_client.publish(MQTT_TOPIC_ROUND_IDLE)
        
        # --- SOCKET.IO EMIT ---
        # Tell Web UI (via Socket.IO) to go idle
        socketio.emit('round_idle')

# --- SocketIO Handlers (for Web UI only) ---

@socketio.on('connect')
def handle_connect():
    """A web client connected."""
    print(f'Web UI client connected: {request.sid}')
    # Send current game state to this client
    socketio.emit('game_state', {
        'state': GAME_STATE,
        'answer': CORRECT_ANSWER
    }, to=request.sid)
    
    # Send current players
    socketio.emit('current_players', {
        'players': list(players.keys())
    }, to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    """A web client disconnected."""
    print(f'Web UI client disconnected: {request.sid}')

@socketio.on('start_game')
def handle_start_game():
    """Web UI user clicked 'Start Game'."""
    global GAME_STATE  # <-- THIS IS THE FIX
    if GAME_STATE == 'IDLE':
        print("\n>>> 'Start Game' signal received. Starting new round...")
        GAME_STATE = 'GUESSING' # This un-blocks the game_loop
    else:
        print("Warning: 'Start Game' signal received while game not idle.")

# --- Main ---
if __name__ == '__main__':
    # --- Setup MQTT Client ---
    mqtt_client = mqtt.Client("bird-game-server")
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    
    try:
        mqtt_client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        mqtt_client.loop_start() # Start MQTT client in background thread
    except Exception as e:
        print(f"CRITICAL: Could not connect to MQTT broker: {e}")
        print("Server cannot start without MQTT.")
        exit(1)

    # --- Start Game Loop ---
    # Start the game loop in a background green-thread
    game_loop_task = socketio.start_background_task(game_loop, mqtt_client)
    
    # --- Start Server ---
    print("=" * 60)
    print("  Distributed Student Guessing Game Server (MQTT)")
    print("=" * 60)
    # Use port 5001 to avoid conflicts on macOS
    print(f"Main Screen: http://0.0.0.0:5001") 
    print("=" * 60)
    print("Game loop started in background.")
    print("Waiting for connections and 'Start Game' signal...")
    
    # Run the Flask-SocketIO server
    # We use '0.0.0.0' to make it accessible on the local network
    # debug=False is important for eventlet/threading to work properly
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
