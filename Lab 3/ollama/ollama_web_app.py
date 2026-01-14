#!/usr/bin/env python3
"""
Ollama Flask Web Interface for Lab 3
Web-based voice assistant using Ollama AI

This script extends a standard Flask app with:
- Ollama AI integration
- REST API chat endpoint
- WebSocket support for real-time chat
- Text-to-speech via espeak
"""

import eventlet
eventlet.monkey_patch()  # Patch standard libraries to work with eventlet

from flask import Flask, Response, render_template, request, jsonify
from flask_socketio import SocketIO, send, emit
import requests
import subprocess

# Initialize Flask app
app = Flask(__name__)
# Enable WebSocket support with CORS allowed from all origins
socketio = SocketIO(app, cors_allowed_origins="*")

# --------------------
# Ollama configuration
# --------------------
OLLAMA_URL = "http://localhost:11434"  # Ollama local server
DEFAULT_MODEL = "phi3:mini"            # Default AI model

# --------------------
# Helper functions
# --------------------
def query_ollama(prompt, model=DEFAULT_MODEL):
    """
    Query Ollama API and return the AI's response.
    Handles timeout and general exceptions.
    """
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get('response', 'No response generated')
        else:
            return f"Error: Ollama returned status {response.status_code}"
    except requests.exceptions.Timeout:
        return "Sorry, the response took too long. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"

def speak_text(text):
    """
    Convert text to speech using espeak.
    Runs as a subprocess to speak asynchronously.
    """
    try:
        subprocess.run(['espeak', f'"{text}"'], shell=True, check=False)
    except Exception as e:
        print(f"TTS Error: {e}")

# --------------------
# Flask routes
# --------------------
@app.route('/')
def index():
    """Render the main web interface"""
    return render_template('ollama_chat.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """
    REST API endpoint for chat messages.
    Expects JSON with a 'message' field.
    Returns AI response in JSON format.
    """
    data = request.get_json()
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    response = query_ollama(user_message)
    return jsonify({'user_message': user_message, 'ai_response': response})

@app.route('/status')
def status():
    """
    Endpoint to check Ollama server status.
    Returns connected models and current model.
    """
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({
                'status': 'connected',
                'models': [m['name'] for m in models],
                'current_model': DEFAULT_MODEL
            })
        else:
            return jsonify({'status': 'error', 'message': 'Ollama not responding'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --------------------
# WebSocket handlers
# --------------------
@socketio.on('chat_message')
def handle_chat_message(data):
    """
    Handle real-time chat messages from client via WebSocket.
    Sends AI response back using 'ai_response' event.
    """
    user_message = data.get('message', '')
    if user_message:
        ai_response = query_ollama(user_message)
        emit('ai_response', {'user_message': user_message, 'ai_response': ai_response})

@socketio.on('speak_request')
def handle_speak_request(data):
    """
    Handle TTS requests from client.
    Converts provided text to speech using espeak.
    """
    text = data.get('text', '')
    if text:
        speak_text(text)
        emit('speak_complete', {'text': text})

@socketio.on('voice_chat')
def handle_voice_chat(data):
    """
    Handle combined voice chat requests:
    - User sends text
    - Ollama generates a response
    - Response is spoken aloud via TTS
    - Response sent back to client
    """
    user_message = data.get('message', '')
    if user_message:
        ai_response = query_ollama(user_message)
        speak_text(ai_response)
        emit('voice_response', {'user_message': user_message, 'ai_response': ai_response})

# --------------------
# Main entry point
# --------------------
if __name__ == '__main__':
    # Print UTF-8 safe startup message
    print("Starting Ollama Flask Web Interface...")
    print("Open your browser to http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
