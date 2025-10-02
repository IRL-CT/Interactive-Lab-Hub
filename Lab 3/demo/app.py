from flask import Flask, Response, render_template, send_from_directory, send_file
from flask_socketio import SocketIO, send, emit
from subprocess import Popen, call, PIPE
import threading
import time
import board
import busio
import json
import socket
import struct
import signal
import sys
import queue

# Sensor imports - uncomment the one you're using
# For Fall 2025+ (Pi 5 compatible):
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
# For earlier years:
# from adafruit_msa3xx import MSA311
# import adafruit_mpu6050

i2c = board.I2C()  # Pi 5 compatible
# i2c = busio.I2C(board.SCL, board.SDA)  # Alternative for older setups

# Initialize sensor - uncomment the one you're using
sensor = LSM6DS3(i2c)  # Fall 2025+
# sensor = MSA311(i2c)  # Earlier years
# sensor = adafruit_mpu6050.MPU6050(i2c)  # MPU6050 users

hostname = socket.gethostname()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Audio streaming - simple approach using parecord
audio_streaming = False  # For visualization (always on)
audio_playback_active = False  # For actual audio playback
audio_thread = None
audio_queue = queue.Queue(maxsize=20)  # Smaller buffer for faster streaming

def stream_audio():
    """Stream audio data in real-time using parecord"""
    global audio_streaming
    
    # Use parecord with smaller chunks for faster, more responsive streaming
    # Format: 8-bit mono, 11025 Hz for fast, low-quality stream
    cmd = ['parecord', '--format=u8', '--rate=11025', '--channels=1', '--raw', '--latency-msec=50']
    
    try:
        process = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=0)  # No buffering
        print("Audio streaming: Started parecord for fast, low-quality audio capture")
        
        chunk_size = 441  # ~0.04 seconds at 11025 Hz, 8-bit samples (smaller chunks = faster)
        
        while audio_streaming:
            # Read audio chunk
            audio_data = process.stdout.read(chunk_size)  # 1 byte per sample for 8-bit
            
            if len(audio_data) == chunk_size:
                # Add to queue for HTTP streaming - keep it moving
                try:
                    audio_queue.put_nowait(audio_data)
                except queue.Full:
                    # Aggressively clear old data to prevent blocking
                    while not audio_queue.empty():
                        try:
                            audio_queue.get_nowait()
                        except queue.Empty:
                            break
                    audio_queue.put_nowait(audio_data)
                
                # Convert to integers for visualization (8-bit unsigned to signed for display)
                audio_samples = [x - 128 for x in audio_data]  # Convert to signed
                # Send every 4th sample for visualization to reduce data
                audio_viz = audio_samples[::4]
                socketio.emit('audio-data', audio_viz)
            
            # No sleep - keep it as fast as possible
            
    except Exception as e:
        print(f"Audio streaming error: {e}")
    finally:
        if 'process' in locals():
            process.terminate()
        print("Audio streaming stopped")

def create_wav_header():
    """Create a WAV header for 8-bit mono 11025 Hz audio"""
    # WAV header for streaming (optimized for low quality, fast streaming)
    header = b'RIFF'
    header += (0xFFFFFFFF).to_bytes(4, 'little')  # File size (unknown for stream)
    header += b'WAVE'
    header += b'fmt '
    header += (16).to_bytes(4, 'little')  # Format chunk size
    header += (1).to_bytes(2, 'little')   # Audio format (PCM)
    header += (1).to_bytes(2, 'little')   # Number of channels (mono)
    header += (11025).to_bytes(4, 'little')  # Sample rate (lower for speed)
    header += (11025).to_bytes(4, 'little')  # Byte rate (sample_rate * channels * bits/8)
    header += (1).to_bytes(2, 'little')   # Block align (channels * bits/8)
    header += (8).to_bytes(2, 'little')   # Bits per sample (8-bit for speed)
    header += b'data'
    header += (0xFFFFFFFF).to_bytes(4, 'little')  # Data size (unknown for stream)
    return header

def generate_audio():
    """Generate audio data for HTTP streaming - only when playback is active"""
    global audio_playback_active
    
    # Send WAV header first
    yield create_wav_header()
    
    while audio_playback_active:
        try:
            # Get audio data from queue with minimal timeout for responsiveness
            data = audio_queue.get(timeout=0.1)
            yield data
        except queue.Empty:
            # Send minimal silence to keep stream alive
            yield b'\x80' * 220  # ~0.02 seconds of 8-bit silence (128 = middle value for unsigned 8-bit)

@socketio.on('speak')
def handel_speak(val):
    # Use pulseaudio for Bluetooth speaker output
    call(f"espeak '{val}' --stdout | paplay", shell=True)

@socketio.on('start-audio')
def start_audio():
    global audio_playback_active
    audio_playback_active = True
    emit('audio-status', {'status': 'started'})
    print("Audio playback started")

@socketio.on('stop-audio')
def stop_audio():
    global audio_playback_active
    audio_playback_active = False
    emit('audio-status', {'status': 'stopped'})
    print("Audio playback stopped")

@socketio.on('connect')
def test_connect():
    print('connected')
    emit('after connect',  {'data':'Lets dance'})
    # Automatically start audio visualization (not streaming)
    global audio_streaming, audio_thread
    if not audio_streaming:
        audio_streaming = True
        audio_thread = threading.Thread(target=stream_audio)
        audio_thread.daemon = True
        audio_thread.start()
        print('Audio visualization started automatically')

@socketio.on('ping-gps')
def handle_message(val):
    # Get acceleration data (works for LSM6DS3, MSA311, and MPU6050)
    accel_data = sensor.acceleration
    emit('pong-gps', accel_data) 



@app.route('/')
def index():
    return render_template('index.html', hostname=hostname)

@app.route('/3las')
def threelas_client():
    """Serve the official 3LAS client for ultra-low latency audio streaming"""
    try:
        return send_file('3LAS/example/client/index.html')
    except FileNotFoundError:
        return "3LAS client not found. Please ensure the 3LAS submodule is initialized.", 404

@app.route('/3las/<path:filename>')
def threelas_static(filename):
    """Serve 3LAS static files"""
    import os
    return send_from_directory(os.path.join('3LAS/example/client'), filename)

# Add specific routes for script and style files
@app.route('/script/<path:filename>')
def threelas_scripts(filename):
    """Serve 3LAS script files"""
    import os
    return send_from_directory('3LAS/example/client/script', filename)

@app.route('/style/<path:filename>')
def threelas_client_styles(filename):
    """Serve 3LAS style files"""
    import os
    return send_from_directory('3LAS/example/client/style', filename)

@app.route('/img/<path:filename>')
def threelas_images(filename):
    """Serve 3LAS image files"""
    import os
    return send_from_directory('3LAS/example/client/img', filename)

@app.route('/3LAS/<path:filename>')
def threelas_direct(filename):
    """Serve 3LAS files from the main 3LAS directory"""
    import os
    return send_from_directory('3LAS', filename)

@app.route('/static/3las/<path:filename>')
def threelas_client_src(filename):
    """Serve 3LAS client src files"""
    import os
    return send_from_directory('3LAS/client/src', filename)



@app.route('/audio-stream')
def audio_stream():
    """Serve live audio stream as raw PCM"""
    return Response(generate_audio(),
                   mimetype="audio/wav",
                   headers={
                       'Cache-Control': 'no-cache, no-store, must-revalidate',
                       'Pragma': 'no-cache',
                       'Expires': '0',
                       'Connection': 'keep-alive',
                       'Content-Type': 'audio/wav',
                       'Transfer-Encoding': 'chunked'
                   })

def signal_handler(sig, frame):
    print('Closing Gracefully')
    global audio_streaming
    audio_streaming = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)


