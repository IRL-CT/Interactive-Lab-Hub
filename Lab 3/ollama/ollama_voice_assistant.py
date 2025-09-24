#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Voice Assistant for Lab 3
Interactive voice assistant using speech recognition, Ollama AI, and text-to-speech

Dependencies:
- ollama (API client)
- speech_recognition
- pyaudio
- pyttsx3 or espeak
"""

import speech_recognition as sr
import subprocess
import requests
import json
import time
import sys
import threading
from queue import Queue

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'UTF-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'UTF-8':
    import codecs
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    import pyttsx3
    TTS_ENGINE = 'pyttsx3'
except ImportError:
    TTS_ENGINE = 'espeak'
    print("pyttsx3 not available, using espeak for TTS")

class OllamaVoiceAssistant:
    def __init__(self, model_name="phi3:mini", ollama_url="http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize TTS
        if TTS_ENGINE == 'pyttsx3':
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)  # Speed of speech
        
        # Test Ollama connection
        self.test_ollama_connection()
        
        # Adjust for ambient noise
        print("Adjusting for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Ready for conversation!")

    def test_ollama_connection(self):
        """Test if Ollama is running and the model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                if self.model_name in model_names:
                    print(f"Ollama is running with {self.model_name} model")
                else:
                    print(f"Model {self.model_name} not found. Available models: {model_names}")
                    if model_names:
                        self.model_name = model_names[0]
                        print(f"Using {self.model_name} instead")
            else:
                raise Exception("Ollama API not responding")
        except Exception as e:
            print(f"Error connecting to Ollama: {e}")
            print("Make sure Ollama is running: 'ollama serve'")
            sys.exit(1)

    def speak(self, text):
        """Convert text to speech"""
        # Clean text to avoid encoding issues
        clean_text = text.encode('ascii', 'ignore').decode('ascii')
        print(f"Assistant: {clean_text}")
        
        if TTS_ENGINE == 'pyttsx3':
            self.tts_engine.say(clean_text)
            self.tts_engine.runAndWait()
        else:
            # Use espeak as fallback
            subprocess.run(['espeak', clean_text], check=False)

    def listen(self):
        """Listen for speech and convert to text"""
        try:
            print("Listening...")
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("Recognizing...")
            # Use Google Speech Recognition (free)
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            print("No speech detected, timing out...")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
            return None

    def query_ollama(self, prompt, system_prompt=None):
        """Send a query to Ollama and get response"""
        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Sorry, I could not generate a response.')
            else:
                return f"Error: Ollama API returned status {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Sorry, the response took too long. Please try again."
        except Exception as e:
            return f"Error communicating with Ollama: {e}"

    def run_conversation(self):
        """Main conversation loop"""
        print("\nOllama Voice Assistant Started!")
        print("Say 'hello' to start, 'exit' or 'quit' to stop")
        print("=" * 50)
        
        # System prompt to make the assistant more conversational
        system_prompt = """You are a helpful voice assistant. Keep your responses concise and conversational, 
        typically 1-2 sentences. Be friendly and engaging. You are running on a Raspberry Pi as part of an 
        interactive device design lab."""
        
        self.speak("Hello! I'm your Ollama voice assistant. How can I help you today?")
        
        while True:
            try:
                # Listen for user input
                user_input = self.listen()
                
                if user_input is None:
                    continue
                    
                # Check for exit commands
                if any(word in user_input for word in ['exit', 'quit', 'bye', 'goodbye']):
                    self.speak("Goodbye! Have a great day!")
                    break
                
                # Check for greeting
                if any(word in user_input for word in ['hello', 'hi', 'hey']):
                    self.speak("Hello! What would you like to talk about?")
                    continue
                
                # Send to Ollama for processing
                print("Thinking...")
                response = self.query_ollama(user_input, system_prompt)
                
                # Speak the response
                self.speak(response)
                
            except KeyboardInterrupt:
                print("\nConversation interrupted by user")
                self.speak("Goodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                self.speak("Sorry, I encountered an error. Let's try again.")

def main():
    """Main function to run the voice assistant"""
    print("Starting Ollama Voice Assistant...")
    
    # Check if required dependencies are available
    try:
        import speech_recognition
        import requests
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install with: pip install speechrecognition requests pyaudio")
        return
    
    # Create and run the assistant
    try:
        assistant = OllamaVoiceAssistant()
        assistant.run_conversation()
    except Exception as e:
        print(f"Failed to start assistant: {e}")

if __name__ == "__main__":
    main()