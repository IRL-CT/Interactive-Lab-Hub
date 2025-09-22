#!/usr/bin/env python3
"""
Ollama Flask Web Interface for Lab 3
Web-based voice assistant using Ollama

This extends the existing Flask app in demo/app.py to include Ollama integration
"""

import eventlet
eventlet.monkey_patch()

from flask import Flask, Response, render_template, request, jsonify
from flask_socketio import SocketIO, send, emit
import requests
import json
import subprocess
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"

def query_ollama(prompt, model=DEFAULT_MODEL):
    """Query Ollama and return response"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
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
    """Text-to-speech using espeak"""
    try:
        subprocess.run(['espeak', f'"{text}"'], shell=True, check=False)
    except Exception as e:
        print(f"TTS Error: {e}")

@app.route('/')
def index():
    """Main web interface"""
    return render_template('ollama_chat.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """REST API endpoint for chat"""
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Query Ollama
    response = query_ollama(user_message)
    
    return jsonify({
        'user_message': user_message,
        'ai_response': response
    })

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat message via WebSocket"""
    user_message = data.get('message', '')
    
    if user_message:
        # Query Ollama
        ai_response = query_ollama(user_message)
        
        # Send response back to client
        emit('ai_response', {
            'user_message': user_message,
            'ai_response': ai_response
        })

@socketio.on('speak_request')
def handle_speak_request(data):
    """Handle text-to-speech request"""
    text = data.get('text', '')
    if text:
        speak_text(text)
        emit('speak_complete', {'text': text})

@socketio.on('voice_chat')
def handle_voice_chat(data):
    """Handle voice chat request (text in, voice out)"""
    user_message = data.get('message', '')
    
    if user_message:
        # Query Ollama
        ai_response = query_ollama(user_message)
        
        # Speak the response
        speak_text(ai_response)
        
        # Send response to client
        emit('voice_response', {
            'user_message': user_message,
            'ai_response': ai_response
        })

@app.route('/status')
def status():
    """Check Ollama status"""
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

if __name__ == '__main__':
    print("🚀 Starting Ollama Flask Web Interface...")
    print("Open your browser to http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)