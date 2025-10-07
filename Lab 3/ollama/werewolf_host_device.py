#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Werewolf Host Device
Hardware: Button N, MiniPiTFT, APDS9960 sensor, speaker
Features:
- Narration with espeak
- Gesture input with APDS9960
- Countdown timer display (console / TFT placeholder)
- Beep before listening
- Waits for player voice input at setup
"""

import time
import subprocess
import board
import busio
import digitalio
from adafruit_apds9960.apds9960 import APDS9960
import sounddevice as sd
import vosk
import json
import numpy as np

# -----------------------------
# Configuration
TTS_ENGINE = 'espeak'
MODEL_NAME = "phi3:mini"
num_players = 3  # 調整玩家人數

# -----------------------------
# Setup Vosk
try:
    vosk_model = vosk.Model("vosk-model-small-en-us-0.15")
except Exception as e:
    print(f"Error loading Vosk model: {e}")
    exit(1)

# -----------------------------
# Speaker / TTS
def speak(text):
    """Text-to-speech using espeak"""
    safe_text = text.encode('ascii', 'ignore').decode('ascii')
    print(f"Assistant: {safe_text}")
    subprocess.run(f'espeak "{text}"', shell=True, check=False)

def play_beep():
    """Play beep before listening"""
    subprocess.run(['mpg123', 'beep.mp3'], check=False)

# -----------------------------
# APDS9960 Gesture (Optional - with fallback)
gesture_sensor = None
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    gesture_sensor = APDS9960(i2c)
    gesture_sensor.enable_proximity = True
    gesture_sensor.enable_gesture = True
    print("APDS9960 gesture sensor initialized successfully")
except Exception as e:
    print(f"APDS9960 sensor not available: {e}")
    print("Gesture functionality will use button fallback")

def wait_for_gesture_blocking():
    """Wait indefinitely until gesture is detected (or button press as fallback)"""
    if gesture_sensor:
        while True:
            gesture = gesture_sensor.gesture()
            if gesture:
                print(f"Gesture detected: {gesture}")
                return gesture
            time.sleep(0.1)
    else:
        print("Gesture sensor not available, using button press instead")
        wait_for_button_blocking()
        return "button_press"

# -----------------------------
# Button N (Optional - with fallback)
button_pin = None
try:
    button_pin = digitalio.DigitalInOut(board.D5)
    button_pin.direction = digitalio.Direction.INPUT
    button_pin.pull = digitalio.Pull.UP
    print("Button initialized successfully")
except Exception as e:
    print(f"Button not available: {e}")
    print("Button functionality will use keyboard input fallback")

def wait_for_button_blocking():
    """Wait indefinitely until button is pressed (or Enter key as fallback)"""
    if button_pin:
        while True:
            if not button_pin.value:
                print("Button pressed")
                return True
            time.sleep(0.05)
    else:
        print("Button not available, press Enter key instead")
        input("Press Enter to continue...")
        return True

# -----------------------------
# Voice input with Vosk
def listen(duration=5, fs=16000):
    """Blocking voice recording"""
    try:
        play_beep()
        print("Listening...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        audio_bytes = audio.tobytes()
        rec = vosk.KaldiRecognizer(vosk_model, fs)
        if rec.AcceptWaveform(audio_bytes):
            result = json.loads(rec.Result())
        else:
            result = json.loads(rec.FinalResult())
        recognized_text = result.get("text", "").strip()
        print(f"You said: {recognized_text}")
        return recognized_text.lower() if recognized_text else None
    except Exception as e:
        print(f"Error recording audio: {e}")
        return None

# -----------------------------
# Countdown (TFT placeholder)
def display_countdown(seconds):
    """Countdown timer placeholder"""
    for i in range(seconds, 0, -1):
        print(f"Countdown: {i}")
        time.sleep(1)

# -----------------------------
# Setup Phase
def setup_phase():
    speak("Welcome to Werewolf Village! Please announce your seat.")
    players = []
    for i in range(num_players):
        user_input = listen(duration=5)
        while not user_input:
            speak("I didn't catch that. Please say your seat and name again.")
            user_input = listen(duration=5)
        players.append(user_input)
        speak(f"Seat recorded: {user_input}")
    speak("Roles have been assigned. Remember your role.")
    return players

# -----------------------------
# Night Phase
def night_phase():
    speak("Night falls... Everyone close your eyes.")

    # Werewolves
    speak("Werewolves, wake up. Choose your victim with a swipe.")
    gesture = wait_for_gesture_blocking()
    speak(f"Target confirmed: {gesture}")
    speak("Werewolves, close your eyes.")

    # Seer
    speak("Seer, wake up. Swipe to inspect a seat.")
    gesture = wait_for_gesture_blocking()
    speak(f"Inspection result: {gesture}")
    speak("Seer, close your eyes.")

    # Witch
    speak("Witch, wake up. Swipe UP to save, DOWN to poison.")
    gesture = wait_for_gesture_blocking()
    speak(f"Witch action: {gesture}")
    speak("Witch, close your eyes.")

# -----------------------------
# Day Phase
def day_phase():
    speak("The sun rises... Everyone open your eyes.")
    speak("No one died last night.")
    speak("You have 90 seconds to discuss.")
    display_countdown(90)

# -----------------------------
# Voting Phase
def voting_phase():
    speak("Time's up! Everyone vote now.")
    speak("Use voice or NEAR gesture to vote.")
    gesture = wait_for_gesture_blocking()
    speak(f"Vote recorded: {gesture}")
    display_countdown(5)

# -----------------------------
# Win Check Phase
def win_check_phase():
    villagers_alive = 3
    werewolves_alive = 1
    if werewolves_alive == 0:
        speak("Villagers win! The village is safe again.")
        return True
    elif werewolves_alive >= villagers_alive:
        speak("Werewolves win! Darkness takes over the village.")
        return True
    else:
        speak("The game continues. Night falls again.")
        return False

# -----------------------------
# Main Game Loop
def main():
    players = setup_phase()
    game_over = False
    while not game_over:
        night_phase()
        day_phase()
        voting_phase()
        game_over = win_check_phase()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        speak("Game interrupted. Goodbye!")
