"""
Collaborative Pixel Grid Server
Fullscreen real-time pixel grid for up to 100 Raspberry Pis
Based on Tinkerbelle architecture with WebSocket live updates
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json
from collections import OrderedDict
from datetime import datetime
import math

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pixel-grid-2025'

# Try eventlet first, fall back to threading if not available
try:
    import eventlet
    eventlet.monkey_patch()
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
except ImportError:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store pixel data: {mac_address: {'color': [r,g,b], 'position': int, 'last_update': datetime}}
pixels = OrderedDict()


@app.route('/')
def index():
    """Serve the fullscreen pixel grid visualization"""
    return render_template('grid.html')


@app.route('/controller')
def controller():
    """Serve the color picker controller (like Jane Wren)"""
    return render_template('controller.html')


@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print(f'Client connected: {request.sid}')
    # Send current state to new client
    emit('grid_state', {
        'pixels': [
            {
                'mac': mac,
                'color': data['color'],
                'position': data['position']
            }
            for mac, data in pixels.items()
        ]
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print(f'Client disconnected: {request.sid}')


@socketio.on('color_update')
def handle_color_update(data):
    """Handle color update from controller or Pi"""
    try:
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
            # Assign next available position
            position = len(pixels)
            pixels[mac] = {
                'color': [r, g, b],
                'position': position,
                'last_update': datetime.now()
            }
            print(f'✓ New pixel: {mac[:17]} at position {position}')
        else:
            # Update existing pixel
            pixels[mac]['color'] = [r, g, b]
            pixels[mac]['last_update'] = datetime.now()
        
        # Broadcast to all clients
        emit('pixel_update', {
            'mac': mac,
            'color': [r, g, b],
            'position': pixels[mac]['position'],
            'is_new': is_new,
            'total': len(pixels)
        }, broadcast=True)
        
    except Exception as e:
        print(f'Error handling color update: {e}')


@socketio.on('clear_grid')
def handle_clear_grid():
    """Clear all pixels"""
    pixels.clear()
    emit('grid_cleared', broadcast=True)
    print('Grid cleared')


if __name__ == '__main__':
    print("=" * 60)
    print("  Collaborative Pixel Grid Server")
    print("=" * 60)
    print(f"  Fullscreen Grid:    http://0.0.0.0:5000")
    print(f"  Controller:         http://0.0.0.0:5000/controller")
    print("=" * 60)
    
    # Optional: Enable MQTT bridge
    # Uncomment to enable MQTT -> WebSocket forwarding
    try:
        from mqtt_bridge import start_mqtt_bridge
        start_mqtt_bridge(socketio, pixels)
    except ImportError:
        print("  MQTT bridge not available (install paho-mqtt)")
    except Exception as e:
        print(f"  MQTT bridge disabled: {e}")
    
    print("=" * 60)
    print()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
