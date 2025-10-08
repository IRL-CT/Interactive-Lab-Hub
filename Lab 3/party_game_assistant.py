#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Voice Assistant for Lab 3 with Touch Sensor + Punishment Feature
Zoe's working Monopoly assistant + Your punishment suggestions & countdown

Dependencies:
- ollama (API client)
- speech_recognition
- pyaudio
- espeak
- adafruit-circuitpython-mpr121
"""

import speech_recognition as sr
import subprocess
import requests
import json
import time
import sys
import re
import os
import board
import busio
import adafruit_mpr121

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'UTF-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'UTF-8':
    import codecs
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

TTS_ENGINE = 'espeak'

# Initialize I2C and MPR121
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)


class OllamaVoiceAssistant:
    def __init__(self, model_name="phi3:mini", ollama_url="http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # --- Score Tracking State ---
        self.player_scores = {}
        self.score_initialized = False
        self.waiting_for_score_update = False
        
        # --- Touch sensor mappings ---
        # Pads 0-4: Select punishment option (1-5)
        # Pads 5-11: Select duration in seconds
        self.touch_duration_map = {
            5: 5,   # Pad 5 = 5 seconds
            6: 10,  # Pad 6 = 10 seconds
            7: 15,  # Pad 7 = 15 seconds
            8: 20,  # Pad 8 = 20 seconds
            9: 30,  # Pad 9 = 30 seconds
            10: 45, # Pad 10 = 45 seconds
            11: 60  # Pad 11 = 60 seconds
        }

        # Test Ollama connection
        self.test_ollama_connection()

        # Adjust for ambient noise
        print("Calibrating mic... Please stay quiet for 3 seconds.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=3)
        self.recognizer.pause_threshold = 0.6
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
        clean_text = text.encode('ascii', 'ignore').decode('ascii')
        print(f"Assistant: {clean_text}")
        subprocess.run(['espeak', clean_text], check=False)

    def listen(self):
        """Listen for speech and convert to text"""
        try:
            timeout = 5
            print("Listening...")
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)

            print("Recognizing...")
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()

        except sr.WaitTimeoutError:
            print("No speech detected, timing out...")
            if self.waiting_for_score_update:
                self.waiting_for_score_update = False
                self.speak("Timeout. Please say 'update score' again when you're ready.")
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
            data = {"model": self.model_name, "prompt": prompt, "stream": False}
            if system_prompt:
                data["system"] = system_prompt

            response = requests.post(f"{self.ollama_url}/api/generate", json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Sorry, I could not generate a response.')
            else:
                return f"Error: Ollama API returned status {response.status_code}"

        except requests.exceptions.Timeout:
            return "Sorry, the response took too long. Please try again."
        except Exception as e:
            return f"Error communicating with Ollama: {e}"

    # --- Touch Sensor for Player Count ---
    def get_num_players_via_touch(self, max_players=12, timeout=10):
        """Detect number of players via single pad touch."""
        self.speak(f"Please touch a pad to indicate the number of players (1-{max_players}).")

        start_time = time.time()
        while True:
            for i in range(max_players):
                if mpr121[i].value:
                    num_players = i 
                    self.speak(f"{num_players} players detected")
                    time.sleep(0.3)  # Debounce
                    return num_players

            if time.time() - start_time > timeout:
                self.speak("Timeout. Defaulting to 3 players.")
                return 3

    # --- Score Tracking Methods ---
    def initialize_scores(self, initial_amount=10000):
        """Ask user for number of players via touch sensor and initialize scores."""
        num_players = self.get_num_players_via_touch()
        players = [f"user{i+1}" for i in range(num_players)]
        self.player_scores = {player.lower(): initial_amount for player in players}
        self.score_initialized = True
        player_list = ", ".join(players)
        return f"Game started! {player_list} all begin with ${initial_amount}. Let the game begin!"

    def update_score(self, player_name, amount, operation):
        """Updates a player's score and returns the new balance."""
        player_name = player_name.lower()
        if player_name not in self.player_scores:
            return f"Sorry, I don't see a player named {player_name}."

        try:
            amount = int(amount)
            if amount < 0:
                return "Please state a positive amount."

            if operation == 'subtract':
                self.player_scores[player_name] -= amount
                action_word = "paid"
            elif operation == 'add':
                self.player_scores[player_name] += amount
                action_word = "received"
            else:
                return "Internal error: Invalid operation."

            new_balance = self.player_scores[player_name]
            self.waiting_for_score_update = False

            return f"Understood. {player_name.capitalize()} {action_word} ${amount}. Their new balance is ${new_balance}. Scores are updated!"
        except ValueError:
            return "I couldn't understand the amount. Please state it clearly."

    def parse_score_command(self, user_input):
        """Parse commands like 'user1 plus 300', 'user 2 - 500', etc."""
        player_names_pattern = r"user\s*1|user\s*2|user\s*3|user\s*4|user\s*5|user\s*6|user\s*7|user\s*8|user\s*9|user\s*10|user\s*11|user\s*12"

        patterns = [
            rf"(?P<player>{player_names_pattern})\s+(?P<op>plus|add|received|got|gained)\s+(?P<amount>\d+)",
            rf"(?P<player>{player_names_pattern})\s+(?P<op>minus|subtract|paid|lost|owes)\s+(?P<amount>\d+)",
            rf"(?P<player>{player_names_pattern})\s*(?P<op>\+|\-)\s*(?P<amount>\d+)",
            rf"(?P<op>plus|add|received|got|gained)\s+(?P<amount>\d+)\s+(?:to|for)\s+(?P<player>{player_names_pattern})",
            rf"(?P<op>minus|subtract|paid|lost|owes)\s+(?P<amount>\d+)\s+(?:from)\s+(?P<player>{player_names_pattern})",
        ]

        for pat in patterns:
            match = re.search(pat, user_input, re.IGNORECASE)
            if match:
                player = match.group("player").replace(" ", "")
                amount = match.group("amount")
                op = match.group("op").lower()
                if op in ["minus", "subtract", "paid", "lost", "owes", "-"]:
                    operation = "subtract"
                else:
                    operation = "add"
                return player, amount, operation

        return None

    def display_scores(self):
        """Returns a string listing all current player scores."""
        if not self.player_scores:
            return "No game in progress. Say 'start game' to begin."
        score_lines = [f"{name.capitalize()}: ${score:,.0f}" for name, score in self.player_scores.items()]
        return "Current scores are: " + " | ".join(score_lines)

    # ========== NEW: PUNISHMENT FEATURES ==========
    
    def get_punishment_suggestions(self):
        """Get AI-powered punishment suggestions using Ollama"""
        try:
            self.speak("Let me think of some creative punishment ideas...")
            
            prompt = """You're helping friends playing Monopoly who need creative consequences for losing players.

Give me exactly 5 fun, lighthearted punishment ideas. Be creative! They should be:
- Quick and entertaining
- Safe and appropriate for everyone
- Something that makes people laugh

IMPORTANT: Format your response as a numbered list with each punishment on a separate line. Start each line with the number and a period. Do not use emojis, asterisks, or special characters. Keep each punishment to one short sentence."""

            result = subprocess.run([
                'ollama', 'run', 'llama3.2',
                prompt
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                response = result.stdout.strip()
                suggestions = self.parse_numbered_list(response)
                return suggestions
            else:
                return self.get_fallback_punishments()

        except Exception as e:
            print(f"Ollama error: {e}")
            return self.get_fallback_punishments()

    def parse_numbered_list(self, text):
        """Parse AI response into a list of suggestions"""
        suggestions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line):
                suggestion = re.sub(r'^\d+\.\s*', '', line)
                if suggestion:
                    suggestions.append(suggestion)
        
        if not suggestions:
            suggestions = [line.strip() for line in lines if line.strip()]
        
        return suggestions[:5]

    def get_fallback_punishments(self):
        """Fallback punishments if AI isn't available"""
        return [
            "Do a 30 second victory dance for the winning team",
            "Tell a joke or funny story to make everyone laugh",
            "Give genuine compliments to each other player",
            "Act out their favorite animal for 1 minute",
            "Share an embarrassing but harmless childhood memory"
        ]

    def wait_for_touch_punishment(self, max_options=5, timeout=30):
        """Wait for user to touch pad 0-4 to select punishment"""
        print("\n" + "="*60)
        print("TOUCH A PAD TO SELECT PUNISHMENT:")
        print("="*60)
        for pad in range(min(max_options, 5)):
            print(f"Pad {pad} → Option {pad + 1}")
        print("="*60)
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            for pad in range(min(max_options, 5)):
                if mpr121[pad].value:
                    option = pad + 1
                    print(f"\n✓ Pad {pad} touched! Selected punishment option: {option}")
                    time.sleep(0.3)  # Debounce
                    return option
            
            time.sleep(0.1)
        
        print("\nTimeout - using default option 1")
        return 1

    def wait_for_touch_duration(self, timeout=30):
        """Wait for user to touch pad 5-11 to select duration"""
        print("\n" + "="*60)
        print("TOUCH A PAD TO SELECT PUNISHMENT DURATION:")
        print("="*60)
        for pad, duration in self.touch_duration_map.items():
            print(f"Pad {pad:2d} → {duration:2d} seconds")
        print("="*60)
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            for pad in self.touch_duration_map.keys():
                if mpr121[pad].value:
                    duration = self.touch_duration_map[pad]
                    print(f"\n✓ Pad {pad} touched! Selected duration: {duration} seconds")
                    time.sleep(0.3)  # Debounce
                    return duration
            
            time.sleep(0.1)
        
        print("\nTimeout - using default 10 seconds")
        return 10

    def display_punishment_countdown(self, player_name, countdown_seconds, punishment):
        """Display player name during punishment countdown with audio"""
        try:
            for i in range(countdown_seconds, 0, -1):
                os.system('clear')
                
                print("\n" * 3)
                print("=" * 60)
                print(f"{'PUNISHMENT TIME!':^60}")
                print("=" * 60)
                print()
                print(f"{player_name:^60}")
                print()
                
                # Word wrap the punishment text
                import textwrap
                wrapped = textwrap.fill(punishment, width=58)
                for line in wrapped.split('\n'):
                    print(f"{line:^60}")
                print()
                
                # Display countdown number
                if i <= 5:
                    print(f"{f'>>> {i} <<<':^60}")
                else:
                    print(f"{str(i):^60}")
                
                print()
                print("=" * 60)
                
                # Audio countdown for last 5 seconds
                if i <= 5:
                    subprocess.run(['espeak', str(i)], check=False)
                else:
                    time.sleep(1)
            
            # Display "TIME UP!"
            os.system('clear')
            print("\n" * 8)
            print("=" * 60)
            print(f"{'TIME UP!':^60}")
            print("=" * 60)
            print()
            
            time.sleep(2)
            return True
            
        except Exception as e:
            print("Display error:", e)
            return False

    def handle_punishment_mode(self):
        """Handle the complete punishment flow"""
        try:
            # Get AI suggestions
            punishments = self.get_punishment_suggestions()
            
            # Display and read out punishments
            print("\n" + "="*60)
            print("PUNISHMENT OPTIONS:")
            print("="*60)
            for i, punishment in enumerate(punishments, 1):
                print(f"{i}. {punishment}")
                self.speak(f"Option {i}. {punishment}")
                time.sleep(0.5)
            print("="*60 + "\n")
            
            # Select punishment via touch
            self.speak("Touch pad 0 through 4 to select which punishment to use.")
            selected_option = self.wait_for_touch_punishment(max_options=len(punishments))
            selected_punishment = punishments[selected_option - 1]
            
            self.speak(f"You selected option {selected_option}. {selected_punishment}")
            
            # Get player name
            self.speak("What is the name of the player who will face this punishment?")
            player_name = self.listen()
            if not player_name or len(player_name.strip()) == 0:
                player_name = "Player"
            
            # Select duration via touch
            self.speak("Touch pad 5 through 11 to select the punishment duration.")
            duration = self.wait_for_touch_duration()
            
            # Confirm and start
            self.speak(f"Alright! {player_name} will have {duration} seconds. Get ready!")
            time.sleep(1)
            
            # Run countdown
            self.display_punishment_countdown(player_name, duration, selected_punishment)
            
            self.speak(f"Time up! Great job {player_name}!")
            return True
            
        except Exception as e:
            print(f"Error in punishment mode: {e}")
            self.speak("Sorry, there was an issue with punishment mode.")
            return False

    # ========== END PUNISHMENT FEATURES ==========

    def run_conversation(self):
        """Main conversation loop"""
        print("\nOllama Voice Assistant Started!")
        print("Say 'hello' to start, 'exit' to quit.")
        print("Say 'start game' to begin tracking scores.")
        print("Say 'punishment' to get creative punishment ideas.")
        print("Say 'update score' for score changes.")
        print("Say 'show scores' to check balances.")
        print("=" * 50)

        system_prompt = "You are a helpful voice assistant. Keep your responses concise and conversational."

        self.speak("Hello! I'm your Monopoly game assistant. How can I help you today?")

        while True:
            try:
                user_input = self.listen()
                if user_input is None:
                    continue

                # Exit
                if any(word in user_input for word in ['exit', 'quit', 'bye']):
                    self.speak("Goodbye! Have a great day!")
                    break

                # NEW: Punishment mode
                if 'punishment' in user_input:
                    self.handle_punishment_mode()
                    continue

                # Waiting for score update
                if self.waiting_for_score_update and self.score_initialized:
                    score_command = self.parse_score_command(user_input)
                    if score_command:
                        player, amount, operation = score_command
                        response = self.update_score(player, amount, operation)
                        self.speak(response)
                        continue
                    else:
                        self.speak("Sorry, I didn't catch that. Say 'user one plus 300' or 'user two minus 500'.")
                        continue

                # Start game
                if 'start game' in user_input and not self.score_initialized:
                    response = self.initialize_scores()
                    self.speak(response)
                    continue

                # Show scores
                if 'show score' in user_input or 'current balance' in user_input:
                    response = self.display_scores()
                    self.speak(response)
                    continue

                # Trigger score update
                if ('update score' in user_input or 'change score' in user_input) and self.score_initialized:
                    self.waiting_for_score_update = True
                    self.speak("Ready to update. Please say which user and how much.")
                    continue

                # Greetings
                if any(word in user_input for word in ['hello', 'hi', 'hey']):
                    self.speak("Hello! What would you like to do?")
                    continue

                # General queries → Ollama
                print("Thinking...")
                response = self.query_ollama(user_input, system_prompt)
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
    print("Starting Ollama Voice Assistant with Punishment Feature...")

    try:
        assistant = OllamaVoiceAssistant()
        assistant.run_conversation()
    except Exception as e:
        print(f"Failed to start assistant: {e}")


if __name__ == "__main__":
    main()