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

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'UTF-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'UTF-8':
    import codecs
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

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
        print("2. Voice Response (Ollama speaks responses)")
        print("3. Test Ollama (simple query)")
        print("4. Test Audio")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ")
        
        if choice == "1":
            text_chat_demo()
        elif choice == "2":
            voice_response_demo()
        elif choice == "3":
            response = query_ollama("Say hello and introduce yourself briefly")
            print(f"Ollama: {response}")
        elif choice == "4":
            test_audio()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()