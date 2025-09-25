#!/usr/bin/env -S /home/pi/Interactive-Lab-Hub/Lab\ 3/.venv/bin/python

import subprocess
import requests
import json
import queue
import sys
import time
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import datetime

# audio queue
q=queue.Queue()
conversation_log="conversation_log.txt"

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def log_conversation(user_text, ai_response):
    timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(conversation_log, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] User: {user_text}\n")
        f.write(f"[{timestamp}] Assistant: {ai_response}\n")
        f.write("-"*50+"\n")

def speak_text(text):
    print(f"Assistant: {text}")
    try:
        p = subprocess.Popen(["festival", "--tts"], stdin=subprocess.PIPE, text=True)
        p.communicate(text, timeout=60)
        p.wait()
        
        # Wait for speech to complete
        time.sleep(1)
        
    except subprocess.TimeoutExpired:
        p.kill()

def query_ollama(prompt, model="phi3:mini"):
    try:
        response=requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model":model,
                "prompt":prompt,
                "stream":False
            },
            timeout=60
        )
        
        if response.status_code==200:
            return response.json().get('response', 'No response')
        else:
            return f"Error: {response.status_code}"
    
    except requests.exceptions.ReadTimeout:
        return "I timed out."
    except Exception as e:
        return f"Error: {e}"

def check_ollama():
    try:
        response=requests.get("http://localhost:11434/api/tags")
        if response.status_code==200:
            models=response.json().get('models', [])
            model_names=[m['name'] for m in models]
            print(f"Ollama is running. Available models: {model_names}")
            return True
        else:
            print("Ollama is not responding")
            return False
    except Exception as e:
        print(f"Cannot connect to Ollama: {e}")
        print("Make sure Ollama is running with: ollama serve")
        return False

def main():
    print("Voice AI Assistant for Lab 3")
    print("="*40)
    
    # init log
    with open(conversation_log, "w", encoding="utf-8") as f:
        f.write(f"Voice AI Assistant Conversation Log - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60+"\n")
    
    if not check_ollama():
        return
    
    # load vosk model
    try:
        model=Model(lang="en-us")
        print("Vosk model loaded successfully")
    except Exception as e:
        print(f"Error loading Vosk model: {e}")
        return
    
    device_info=sd.query_devices(None, "input")
    samplerate=int(device_info["default_samplerate"])
    
    speak_text("Hello! I am your voice AI assistant. Say something to me!")
    
    try:
        with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=None,
                dtype="int16", channels=1, callback=callback):
            print("#"*80)
            print("Listening for speech... Say 'exit' to quit")
            print("#"*80)
            
            rec=KaldiRecognizer(model, samplerate)
            
            while True:
                data=q.get()
                if rec.AcceptWaveform(data):
                    result=rec.Result()
                    result_json=json.loads(result)
                    text=result_json.get("text", "").strip()
                    
                    if text:
                        print(f"You said: {text}")
                        
                        if "exit" in text.lower():
                            speak_text("Goodbye! Have a great day!")
                            break
                        
                        print("Thinking...")
                        ai_response=query_ollama(text)
                        
                        log_conversation(text, ai_response)
                        
                        speak_text(ai_response)
                        
                else:
                    partial=rec.PartialResult()
                    partial_json=json.loads(partial)
                    partial_text=partial_json.get("partial", "").strip()
                    if partial_text:
                        print(f"Listening: {partial_text}", end='\r')
    
    except KeyboardInterrupt:
        print("\nConversation interrupted by user")
        speak_text("Goodbye!")
        with open(conversation_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Conversation ended by user interrupt\n")
    except Exception as e:
        print(f"Error: {e}")
        speak_text("Sorry, I encountered an error.")
        with open(conversation_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: {e}\n")

if __name__ == "__main__":
    main()
