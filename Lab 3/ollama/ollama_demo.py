#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Ollama Demo for Lab 3
Basic example of integrating Ollama with voice I/O

This script demonstrates:
1. Text input to Ollama
2. Voice input to Ollama  
3. Voice output from Ollama
"""

import requests
import json
import subprocess
import sys
import os
import tempfile
import wave

# Suppress ALSA warnings before importing pyaudio
os.environ['PYAUDIO_NO_ERROR_MESSAGES'] = '1'
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Try to import speech recognition
try:
    from vosk import Model, KaldiRecognizer
    import pyaudio
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Note: Vosk not available. Voice input will be disabled.")

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'UTF-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'UTF-8':
    import codecs
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Additional ALSA error suppression
from ctypes import *
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
def py_error_handler(filename, line, function, err, fmt):
    pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
try:
    asound = cdll.LoadLibrary('libasound.so.2')
    asound.snd_lib_error_set_handler(c_error_handler)
except:
    pass

# Global variables for Vosk model (load once, reuse)
VOSK_MODEL = None
VOSK_MODEL_LOADED = False

def load_vosk_model():
    """Load Vosk model once and cache it"""
    global VOSK_MODEL, VOSK_MODEL_LOADED
    
    if VOSK_MODEL_LOADED:
        return VOSK_MODEL
    
    if not VOSK_AVAILABLE:
        return None
    
    # Check for Vosk model in multiple locations
    possible_paths = [
        os.path.expanduser("~/.cache/vosk/vosk-model-small-en-us-0.15"),
        "/usr/share/vosk-model-small-en-us-0.15",
        "/usr/local/share/vosk-model-small-en-us-0.15",
        os.path.expanduser("~/vosk-model-small-en-us-0.15"),
    ]
    
    model_path = None
    for path in possible_paths:
        if os.path.exists(path):
            model_path = path
            break
    
    if not model_path:
        print(f"Error: Vosk model not found in any of these locations:")
        for path in possible_paths:
            print(f"  - {path}")
        print("\nDownload with: vosk-transcriber (it will auto-download)")
        VOSK_MODEL_LOADED = True
        return None
    
    # Suppress Vosk logging during initial load
    import sys
    original_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    
    try:
        print("Loading speech recognition model... (this happens once)")
        VOSK_MODEL = Model(model_path)
        VOSK_MODEL_LOADED = True
        print("✓ Model loaded")
    finally:
        sys.stderr = original_stderr
    
    return VOSK_MODEL

def get_bluetooth_sink():
    """Get the Bluetooth audio sink name"""
    try:
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                              capture_output=True, text=True, check=True)
        for line in result.stdout.split('\n'):
            if 'bluez' in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]  # Return sink name
    except Exception as e:
        print(f"Warning: Could not detect Bluetooth sink: {e}")
    return None

def speak_text(text):
    """Text-to-speech using espeak with automatic Bluetooth speaker detection"""
    # Clean text to avoid encoding issues
    clean_text = text.encode('ascii', 'ignore').decode('ascii')
    print(f"Assistant: {clean_text}")
    
    # Get Bluetooth sink
    bt_sink = get_bluetooth_sink()
    
    if bt_sink:
        # Use espeak with paplay to route to Bluetooth
        try:
            # Generate speech to stdout, pipe to paplay with Bluetooth sink
            espeak_process = subprocess.Popen(
                ['espeak', '--stdout', clean_text],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            subprocess.run(
                ['paplay', '--device', bt_sink],
                stdin=espeak_process.stdout,
                stderr=subprocess.DEVNULL,
                check=False
            )
            espeak_process.wait()
        except Exception as e:
            print(f"Bluetooth audio error: {e}, falling back to default")
            subprocess.run(['espeak', clean_text], check=False)
    else:
        # Fallback to default audio output
        subprocess.run(['espeak', clean_text], check=False)

def listen_microphone(duration=5):
    """Listen to microphone and convert speech to text using Vosk"""
    if not VOSK_AVAILABLE:
        print("Error: Vosk speech recognition not available")
        print("Install with: pip install vosk pyaudio")
        return None
    
    try:
        # Load model (cached after first call)
        model = load_vosk_model()
        if model is None:
            return None
        
        recognizer = KaldiRecognizer(model, 16000)
        recognizer.SetWords(True)
        
        # Show message FIRST
        print(f"🎤 Listening for {duration} seconds... Speak now!")
        
        # Suppress stderr for all PyAudio operations (Jack/ALSA errors)
        import sys
        original_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        
        # Setup audio - use webcam microphone
        p = pyaudio.PyAudio()
        
        # Find the webcam device
        webcam_index = None
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if 'C270' in info['name'] or 'USB' in info['name']:
                if info['maxInputChannels'] > 0:
                    webcam_index = i
                    break
        
        if webcam_index is None:
            webcam_index = 0  # Default to first device
        
        stream = p.open(format=pyaudio.paInt16,
                       channels=1,
                       rate=16000,
                       input=True,
                       input_device_index=webcam_index,
                       frames_per_buffer=4096)
        
        stream.start_stream()
        
        # Restore stderr for user feedback
        sys.stderr = original_stderr
        
        # Record for specified duration
        all_text = []
        frames_to_read = int(16000 * duration / 4096)
        for i in range(frames_to_read):
            try:
                data = stream.read(4096, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    partial_text = result.get('text', '')
                    if partial_text:
                        all_text.append(partial_text)
                        print(f"   Heard: {partial_text}")
            except Exception as e:
                print(f"Read error: {e}")
                break
        
        # Get final result
        final = json.loads(recognizer.FinalResult())
        final_text = final.get('text', '')
        if final_text:
            all_text.append(final_text)
        
        # Combine all recognized text
        text = ' '.join(all_text).strip()
        
        # Suppress stderr again for cleanup
        sys.stderr = open(os.devnull, 'w')
        
        # Cleanup
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Restore stderr
        sys.stderr = original_stderr
        
        return text if text else None
        
    except Exception as e:
        # Make sure stderr is restored
        import sys
        sys.stderr = original_stderr
        print(f"Error during voice input: {e}")
        import traceback
        traceback.print_exc()
        return None

def query_ollama(prompt, model="qwen2.5:0.5b-instruct"):
    """Send a text prompt to Ollama and stream response"""
    try:
        with requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True
            },
            stream=True,
            timeout=300
        ) as r:
            response_text = ""
            for line in r.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    token = data.get("response", "")
                    response_text += token
                    print(token, end="", flush=True)
            print()
            return response_text
    except Exception as e:
        return f"Error: {e}"

def text_chat_demo():
    """Simple text-based chat with Ollama"""
    print("\n=== TEXT CHAT DEMO ===")
    print("Type 'quit' to exit")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit']:
            break
            
        print("Thinking...")
        response = query_ollama(user_input)
        print(f"Ollama: {response}")

def voice_response_demo():
    """Demo: Text input, voice output"""
    print("\n=== VOICE RESPONSE DEMO ===")
    print("Type your message, Ollama will respond with voice")
    print("Type 'quit' to exit")
    
    while True:
        user_input = input("\nYour message: ")
        if user_input.lower() in ['quit', 'exit']:
            break
            
        print("Thinking...")
        response = query_ollama(user_input)
        speak_text(response)

def voice_conversation_demo():
    """Demo: Voice input, voice output (full voice conversation)"""
    if not VOSK_AVAILABLE:
        print("\n⚠ Voice input not available. Vosk or PyAudio not installed.")
        print("Install with: pip install vosk pyaudio")
        return
    
    print("\n=== VOICE CONVERSATION DEMO ===")
    print("Speak to Ollama and it will respond with voice")
    print("Press Enter to start recording, type 'quit' to exit")
    
    while True:
        user_input = input("\nPress Enter to speak (or type 'quit'): ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        # Listen to microphone
        text = listen_microphone(duration=5)
        
        if text:
            print(f"You said: {text}")
            print("Thinking...")
            response = query_ollama(text)
            speak_text(response)
        else:
            print("Sorry, I didn't hear anything. Try again.")

def test_microphone():
    """Test microphone input"""
    if not VOSK_AVAILABLE:
        print("\n⚠ Vosk or PyAudio not available")
        print("Install with: pip install vosk pyaudio")
        return
    
    print("\n=== MICROPHONE TEST ===")
    
    # List audio devices
    try:
        p = pyaudio.PyAudio()
        print("\nAvailable audio input devices:")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  [{i}] {info['name']} (channels: {info['maxInputChannels']})")
        p.terminate()
        print()
    except Exception as e:
        print(f"Could not list devices: {e}\n")
    
    print("This will record 3 seconds of audio and transcribe it")
    print("Make sure your microphone (webcam) is connected and speak clearly")
    input("Press Enter to start recording...")
    
    text = listen_microphone(duration=3)
    
    if text:
        print(f"\n✓ Transcribed: '{text}'")
        print("Microphone is working!")
    else:
        print("\n✗ No speech detected or microphone issue")
        print("\nTroubleshooting:")
        print("1. Check if your webcam microphone is connected")
        print("2. Test with: arecord -d 3 test.wav && aplay test.wav")
        print("3. List devices with: arecord -l")
        print("4. Try speaking louder and more clearly")

def test_audio():
    """Test audio output and Bluetooth speaker"""
    print("\n=== AUDIO TEST ===")
    bt_sink = get_bluetooth_sink()
    if bt_sink:
        print(f"✓ Bluetooth speaker detected: {bt_sink}")
        print("Testing audio output...")
        speak_text("Audio test. If you hear this, your Bluetooth speaker is working.")
        return True
    else:
        print("⚠ No Bluetooth speaker detected. Using default audio output.")
        print("Testing audio output...")
        speak_text("Audio test. Using default speaker.")
        return True

def check_ollama():
    """Check if Ollama is running and model is available"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            print(f"✓ Ollama is running. Available models: {model_names}")
            return True
        else:
            print("✗ Ollama is not responding")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to Ollama: {e}")
        print("Make sure Ollama is running with: ollama serve")
        return False

def main():
    """Main demo menu"""
    print("Ollama Lab 3 Demo")
    print("=" * 30)
    
    # Check Ollama connection
    if not check_ollama():
        return
    
    while True:
        print("\nChoose a demo:")
        print("1. Text Chat (type to Ollama)")
        print("2. Voice Response (type message, Ollama speaks)")
        print("3. Voice Conversation (speak to Ollama, it speaks back)" + 
              (" ⚠ Vosk needed" if not VOSK_AVAILABLE else ""))
        print("4. Test Ollama (simple query)")
        print("5. Test Audio (speaker)")
        print("6. Test Microphone" + (" ⚠ Vosk needed" if not VOSK_AVAILABLE else ""))
        print("7. Exit")
        
        choice = input("\nEnter choice (1-7): ")
        
        if choice == "1":
            text_chat_demo()
        elif choice == "2":
            voice_response_demo()
        elif choice == "3":
            voice_conversation_demo()
        elif choice == "4":
            response = query_ollama("Say hello and introduce yourself briefly")
            print(f"Ollama: {response}")
        elif choice == "5":
            test_audio()
        elif choice == "6":
            test_microphone()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()