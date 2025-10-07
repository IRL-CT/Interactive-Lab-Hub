#!/usr/bin/env python3
"""
ideaBox - AI-Powered Party Game Creative Assistant
Provides creative suggestions for ongoing party games using AI.
Enhanced with intro sound and punishment display with countdown.
"""

import subprocess
import time
import os
import sys
import random
import re
from pathlib import Path
import threading


class IdeaBoxAssistant:
    def __init__(self):
        self.piper_model = "en_US-lessac-medium"
        self.whisper_model = "tiny"
        self.current_game = None
        self.audio_dir = "audio"
        self.intro_sound = "intro.mp3"
        self.spinner_active = False
        self.spinner_thread = None
        
        # Create audio directory if it doesn't exist
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Detect available Piper voices
        self.detect_piper_voice()
    
    def __del__(self):
        """Cleanup on exit"""
        self.stop_spinner()
    
    def detect_piper_voice(self):
        """Detect available Piper voices and use the first available one"""
        try:
            # Try to list available voices
            result = subprocess.run(['piper', '--list-voices'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                # Parse available voices
                voices = []
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('Available'):
                        voice_name = line.strip().split()[0]
                        voices.append(voice_name)
                
                if voices:
                    # Prefer lessac-medium, but fall back to first available
                    if self.piper_model in voices:
                        print(f"Using Piper voice: {self.piper_model}")
                    else:
                        self.piper_model = voices[0]
                        print(f"Voice en_US-lessac-medium not found. Using: {self.piper_model}")
                else:
                    print("No Piper voices found. You may need to download voices.")
                    self.print_piper_install_instructions()
            else:
                print("Could not detect Piper voices.")
                self.print_piper_install_instructions()
                
        except Exception as e:
            print(f"Error detecting Piper voices: {e}")
            self.print_piper_install_instructions()
    
    def print_piper_install_instructions(self):
        """Print instructions for installing Piper voices"""
        print("\n" + "="*60)
        print("PIPER VOICE INSTALLATION REQUIRED")
        print("="*60)
        print("\nTo download Piper voices, run one of these commands:\n")
        print("Option 1 - Download en_US-lessac-medium (recommended):")
        print("  wget https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-lessac-medium.tar.gz")
        print("  tar -xzf voice-en-us-lessac-medium.tar.gz")
        print("  # Move .onnx and .json files to piper's voices directory\n")
        print("Option 2 - Use piper to download:")
        print("  piper --download-dir ./voices --voice en_US-lessac-medium")
        print("\nOption 3 - List all available voices:")
        print("  piper --list-voices\n")
        print("="*60 + "\n")
    
    def play_intro_sound(self):
        """Play the intro sound using mpg123 or aplay"""
        try:
            intro_path = os.path.join(self.audio_dir, self.intro_sound)
            
            if not os.path.exists(intro_path):
                print(f"Warning: Intro sound not found at {intro_path}")
                return False
            
            print("Playing intro sound...")
            
            # Try mpg123 first for mp3 files
            try:
                subprocess.run(['mpg123', intro_path], capture_output=True)
                return True
            except FileNotFoundError:
                # Fall back to ffplay if mpg123 not available
                try:
                    subprocess.run(['ffplay', '-nodisp', '-autoexit', intro_path], 
                                 capture_output=True)
                    return True
                except FileNotFoundError:
                    print("No suitable audio player found for MP3. Install mpg123 or ffmpeg.")
                    return False
                    
        except Exception as e:
            print("Intro sound error:", e)
            return False
    
    def spinner_animation(self, message="Processing"):
        """Display spinning wheel animation"""
        # Use ASCII characters instead of Unicode for compatibility
        spinner_chars = ['|', '/', '-', '\\']
        idx = 0
        
        while self.spinner_active:
            sys.stdout.write(f'\r{message}... {spinner_chars[idx % len(spinner_chars)]} ')
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)
        
        # Clear the spinner line
        sys.stdout.write('\r' + ' ' * (len(message) + 10) + '\r')
        sys.stdout.flush()
    
    def start_spinner(self, message="Processing"):
        """Start the spinner animation in a separate thread"""
        if self.spinner_thread and self.spinner_thread.is_alive():
            self.stop_spinner()
        
        self.spinner_active = True
        self.spinner_thread = threading.Thread(target=self.spinner_animation, args=(message,))
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
    
    def stop_spinner(self):
        """Stop the spinner animation"""
        self.spinner_active = False
        if self.spinner_thread:
            self.spinner_thread.join(timeout=0.5)
    
    def display_punishment_name(self, player_name, countdown_seconds=10, punishment=""):
        """Display player name during punishment countdown with synced audio"""
        try:
            # Countdown loop
            for i in range(countdown_seconds, 0, -1):
                # Clear screen and display countdown
                os.system('clear')
                
                print("\n" * 3)
                print("=" * 60)
                print(f"{'PUNISHMENT TIME!':^60}")
                print("=" * 60)
                print()
                print(f"{player_name:^60}")
                print()
                if punishment:
                    # Word wrap the punishment text
                    import textwrap
                    wrapped = textwrap.fill(punishment, width=58)
                    for line in wrapped.split('\n'):
                        print(f"{line:^60}")
                    print()
                
                # Display countdown number with emphasis
                if i <= 5:
                    print(f"{f'>>> {i} <<<':^60}")
                else:
                    print(f"{str(i):^60}")
                
                print()
                print("=" * 60)
                
                # Audio countdown for last 5 seconds (synced with display)
                if i <= 5:
                    countdown_text = str(i)
                    self.text_to_speech(countdown_text, f"countdown_{i}.wav")
                else:
                    # For non-audio seconds, just wait 1 second
                    time.sleep(1)
            
            # Display "TIME UP!" message
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
    
    def text_to_speech(self, text, filename="output.wav"):
        """Convert text to speech using Piper or espeak as fallback"""
        try:
            print("ASSISTANT:", text)
            
            # Start spinner for TTS generation
            self.start_spinner("Generating speech")
            
            # Store audio file in audio directory
            audio_path = os.path.join(self.audio_dir, filename)
            
            # Try Piper first
            try:
                process = subprocess.run(
                    ['piper', '--model', self.piper_model, '--output_file', audio_path],
                    input=text,
                    text=True,
                    capture_output=True,
                    timeout=10
                )
                
                self.stop_spinner()
                
                if process.returncode == 0:
                    # Play the audio with increased buffer size to prevent cutoff
                    subprocess.run([
                        'aplay', 
                        '--buffer-size=8192',  # Larger buffer
                        audio_path
                    ], capture_output=True)
                    return True
                else:
                    raise Exception("Piper failed, trying fallback")
                    
            except Exception as piper_error:
                # Fallback to espeak
                print("Piper unavailable, using espeak fallback...")
                try:
                    # espeak can generate wav file directly
                    subprocess.run([
                        'espeak',
                        '-w', audio_path,
                        '-s', '150',  # Speed
                        '-a', '200',  # Amplitude
                        text
                    ], check=True, capture_output=True)
                    
                    self.stop_spinner()
                    
                    # Play the audio with increased buffer size to prevent cutoff
                    subprocess.run([
                        'aplay',
                        '--buffer-size=8192',  # Larger buffer
                        audio_path
                    ], capture_output=True)
                    return True
                    
                except FileNotFoundError:
                    self.stop_spinner()
                    # If espeak also not available, just print
                    print("No TTS available - printing only")
                    return True
                
        except Exception as e:
            self.stop_spinner()
            print("TTS ERROR:", e)
            return False
    
    def record_audio(self, duration=5, filename="user_input.wav"):
        """Record audio from microphone"""
        try:
            print(f"RECORDING for {duration} seconds...")
            
            # Store audio file in audio directory
            audio_path = os.path.join(self.audio_dir, filename)
            
            result = subprocess.run([
                'arecord', 
                '-d', str(duration),
                '-f', 'cd',
                '-t', 'wav',
                audio_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Recording completed successfully")
                return True
            else:
                print("Recording failed:", result.stderr)
                return False
                
        except Exception as e:
            print("Recording error:", e)
            return False
    
    def speech_to_text(self, audio_file):
        """Convert speech to text using Whisper"""
        try:
            # Start spinner for speech-to-text conversion
            self.start_spinner("Converting speech to text")
            
            # Audio file is already in audio directory
            audio_path = os.path.join(self.audio_dir, audio_file)
            
            result = subprocess.run([
                'whisper', audio_path,
                '--model', self.whisper_model,
                '--output_format', 'txt',
                '--output_dir', self.audio_dir,
                '--verbose', 'False'
            ], capture_output=True, text=True)
            
            self.stop_spinner()
            
            if result.returncode == 0:
                # Text file will be generated in audio directory
                text_file = os.path.join(self.audio_dir, audio_file.replace('.wav', '.txt'))
                if os.path.exists(text_file):
                    with open(text_file, 'r') as f:
                        text = f.read().strip()
                    print("You said:", text)
                    return text
                else:
                    print("Text file not generated")
                    return None
            else:
                print("Speech-to-text failed:", result.stderr)
                return None
                
        except Exception as e:
            self.stop_spinner()
            print("Speech-to-text error:", e)
            return None

    def get_ai_creative_suggestions(self, game_type, request_type, additional_context=""):
        """Get AI-powered creative suggestions using Ollama"""
        try:
            # Acknowledge that we're working on it
            ack_messages = [
                "Let me think of some creative ideas for you...",
                "Give me a moment to come up with something fun...",
                "I'm brewing up some creative suggestions...",
                "Working on some fresh ideas for your game...",
                "Let me put on my creative thinking cap..."
            ]
            ack_message = random.choice(ack_messages)
            self.text_to_speech(ack_message, "thinking.wav")
            
            # Start spinner for AI thinking
            self.start_spinner("AI is thinking")
            
            # Create more open-ended prompts for variety
            if request_type == "punishments":
                prompt = f"""You're helping friends playing {game_type} who need creative consequences for losing. 

Give me exactly 5 fun, lighthearted punishment ideas. Be creative and think outside the box! They should be:
- Quick and entertaining
- Safe and appropriate for everyone
- Something that makes people laugh

Context: {additional_context}

IMPORTANT: Format your response as a numbered list with each punishment on a separate line. Start each line with the number and a period. Do not use emojis, asterisks, or special characters. Keep each punishment to one short sentence."""
            
            elif request_type == "themes":
                prompt = f"""Players are enjoying {game_type} and want fresh theme ideas to keep it interesting.

Suggest exactly 5 creative themes or categories. Think of unexpected, fun angles that would make the game more exciting. 

Context: {additional_context}

IMPORTANT: Format your response as a numbered list with each theme on a separate line. Start each line with the number and a period. Do not use emojis, asterisks, or special characters. Keep each theme to one short phrase."""
            
            elif request_type == "variations":
                prompt = f"""Friends playing {game_type} want to shake things up with some rule variations.

Give me exactly 5 creative ways to modify the game. Think of fun twists that change the dynamic while keeping it enjoyable.

Context: {additional_context}

IMPORTANT: Format your response as a numbered list with each variation on a separate line. Start each line with the number and a period. Do not use emojis, asterisks, or special characters. Keep each variation to one short sentence."""
            
            else:  # General creative help
                prompt = f"""Players of {game_type} are asking: "{additional_context}"

Help them make their game more fun and memorable. Give exactly 5 creative and practical suggestions they can use right now.

IMPORTANT: Format your response as a numbered list with each suggestion on a separate line. Start each line with the number and a period. Do not use emojis, asterisks, or special characters. Keep each suggestion to one short sentence."""
            
            # Call Ollama with longer timeout and better error handling
            result = subprocess.run([
                'ollama', 'run', 'llama3.2',
                prompt
            ], capture_output=True, text=True, timeout=60)
            
            self.stop_spinner()
            
            if result.returncode == 0:
                response = result.stdout.strip()
                print("AI generated creative suggestions successfully")
                
                # Parse the numbered list
                suggestions = self.parse_numbered_list(response)
                return suggestions
            else:
                print("Ollama error:", result.stderr)
                return self.get_fallback_suggestion(request_type, game_type)
                
        except subprocess.TimeoutExpired:
            self.stop_spinner()
            print("Ollama timeout - using fallback")
            return self.get_fallback_suggestion(request_type, game_type)
        except Exception as e:
            self.stop_spinner()
            print("Ollama error:", e)
            return self.get_fallback_suggestion(request_type, game_type)
    
    def parse_numbered_list(self, text):
        """Parse AI response into a list of suggestions"""
        suggestions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Match lines that start with a number and period
            if re.match(r'^\d+\.', line):
                # Remove the number and period
                suggestion = re.sub(r'^\d+\.\s*', '', line)
                if suggestion:
                    suggestions.append(suggestion)
        
        # If no numbered items found, try to split by newlines
        if not suggestions:
            suggestions = [line.strip() for line in lines if line.strip()]
        
        return suggestions[:5]  # Return max 5 suggestions

    def get_fallback_suggestion(self, request_type, game_type):
        """Fallback suggestions if AI isn't available"""
        fallbacks = {
            "punishments": [
                "Do a 30 second victory dance for the winning team",
                "Tell a joke or funny story to make everyone laugh",
                "Give genuine compliments to each other player",
                "Act out their favorite animal for 1 minute",
                "Share an embarrassing but harmless childhood memory"
            ],
            
            "themes": [
                "90s nostalgia with movies music and trends",
                "Childhood favorites like cartoons games and snacks",
                "Around the world featuring countries landmarks and foods",
                "Superheroes and villains",
                "Time travel to past decades or future predictions"
            ],
            
            "variations": [
                "Speed rounds where you cut time limits in half",
                "Silent mode with no talking except for answers",
                "Team swap where you switch teams halfway through",
                "Prop challenge using random objects as hints",
                "Reverse rules where you play with opposite rules for one round"
            ]
        }
        
        return fallbacks.get(request_type, [])

    def simulate_user_input(self, prompt_type="general"):
        """Simulate user input for testing without microphone"""
        if prompt_type == "game":
            test_games = [
                "charades",
                "pictionary", 
                "trivia",
                "cards against humanity",
                "two truths and a lie",
                "never have I ever"
            ]
            
            print("\nSIMULATION MODE - Choose a game:")
            for i, game in enumerate(test_games, 1):
                print(f"{i}. {game}")
            
            try:
                choice = int(input("Enter number (1-6): ")) - 1
                if 0 <= choice < len(test_games):
                    return test_games[choice]
                else:
                    return test_games[0]
            except:
                return test_games[0]
        
        elif prompt_type == "confirmation":
            options = ["yes please", "sure", "no thanks", "yes"]
            print("\nConfirmation options:")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
            
            try:
                choice = int(input("Enter number (1-4): ")) - 1
                if 0 <= choice < len(options):
                    return options[choice]
                else:
                    return options[0]
            except:
                return options[0]
        
        elif prompt_type == "player_name":
            print("\nEnter player name for punishment:")
            player_name = input("Player name: ").strip()
            return player_name if player_name else "Player 1"
        
        elif prompt_type == "countdown_time":
            print("\nEnter countdown duration (5-90 seconds):")
            try:
                duration = int(input("Seconds (default 10): "))
                return str(duration) if 5 <= duration <= 90 else "10"
            except:
                return "10"
        
        elif prompt_type == "punishment_choice":
            print("\nEnter the number of the punishment you want to use:")
            try:
                choice = int(input("Punishment #: "))
                return str(choice)
            except:
                return "1"
        
        else:  # General creative request
            requests = [
                "punishment ideas for losers",
                "new themes to try",
                "fun variations to mix things up", 
                "creative scoring ideas",
                "help make it more interesting"
            ]
            
            print("\nWhat creative help do you want?")
            for i, request in enumerate(requests, 1):
                print(f"{i}. {request}")
            
            try:
                choice = int(input("Enter number (1-5): ")) - 1
                if 0 <= choice < len(requests):
                    return requests[choice]
                else:
                    return requests[0]
            except:
                return requests[0]

    def get_user_input(self, use_microphone, prompt_type="general", duration=6):
        """Get user input either from microphone or simulation"""
        if use_microphone:
            filename = f"{prompt_type}_response.wav"
            if self.record_audio(duration=duration, filename=filename):
                return self.speech_to_text(filename)
            return None
        else:
            user_input = self.simulate_user_input(prompt_type)
            print(f"Simulated input: {user_input}")
            return user_input

    def parse_confirmation(self, response):
        """Check if user wants help"""
        if not response:
            return True
        
        positive = ["yes", "yeah", "sure", "please", "ok", "sounds good"]
        negative = ["no", "nah", "not really", "skip"]
        
        response_lower = response.lower()
        
        for word in positive:
            if word in response_lower:
                return True
        
        for word in negative:
            if word in response_lower:
                return False
        
        return True  # Default to yes

    def determine_request_type(self, user_request):
        """Determine what type of creative help the user wants"""
        if not user_request:
            return "general"
        
        request_lower = user_request.lower()
        
        if any(word in request_lower for word in ["punishment", "penalty", "consequence", "loser", "lose"]):
            return "punishments"
        elif any(word in request_lower for word in ["theme", "topic", "category", "subject"]):
            return "themes"
        elif any(word in request_lower for word in ["variation", "twist", "change", "different", "mix", "spice"]):
            return "variations"
        else:
            return "general"

    def handle_punishment_countdown(self, use_microphone, punishment_suggestions):
        """Handle the punishment confirmation and countdown flow"""
        try:
            # Display punishment options
            print("\n" + "="*60)
            print("PUNISHMENT OPTIONS:")
            print("="*60)
            
            if isinstance(punishment_suggestions, list):
                for i, punishment in enumerate(punishment_suggestions, 1):
                    print(f"{i}. {punishment}")
            else:
                # If it's a string, try to parse it
                punishments = self.parse_numbered_list(str(punishment_suggestions))
                for i, punishment in enumerate(punishments, 1):
                    print(f"{i}. {punishment}")
                punishment_suggestions = punishments
            
            print("="*60 + "\n")
            
            # Read out the punishments
            intro = "Here are your punishment options."
            self.text_to_speech(intro, "punishment_intro.wav")
            
            for i, punishment in enumerate(punishment_suggestions, 1):
                punishment_text = f"Option {i}. {punishment}"
                self.text_to_speech(punishment_text, f"punishment_option_{i}.wav")
                time.sleep(0.5)
            
            # Ask which punishment to use
            choice_question = "Which punishment would you like to use? Say the number."
            self.text_to_speech(choice_question, "ask_punishment_choice.wav")
            
            choice_response = self.get_user_input(use_microphone, "punishment_choice", duration=5)
            
            # Parse the choice
            selected_index = 0
            if choice_response:
                numbers = re.findall(r'\d+', choice_response)
                if numbers:
                    try:
                        selected_index = int(numbers[0]) - 1
                        if selected_index < 0 or selected_index >= len(punishment_suggestions):
                            selected_index = 0
                    except:
                        selected_index = 0
            
            selected_punishment = punishment_suggestions[selected_index]
            
            # Confirm selection
            confirm_msg = f"You selected punishment number {selected_index + 1}. {selected_punishment}"
            self.text_to_speech(confirm_msg, "confirm_selection.wav")
            print(f"\nSELECTED: {selected_punishment}\n")
            
            # Get player name
            name_question = "What is the name of the player who will face this punishment?"
            self.text_to_speech(name_question, "ask_player_name.wav")
            
            player_name = self.get_user_input(use_microphone, "player_name", duration=8)
            if not player_name or len(player_name.strip()) == 0:
                player_name = "Player"
            
            # Get countdown duration
            duration_question = "How many seconds should the punishment countdown last? Say a number between 5 and 90."
            self.text_to_speech(duration_question, "ask_duration.wav")
            
            duration_response = self.get_user_input(use_microphone, "countdown_time", duration=5)
            
            # Parse duration from response
            countdown_seconds = 10  # Default
            if duration_response:
                # Extract numbers from response
                numbers = re.findall(r'\d+', duration_response)
                if numbers:
                    try:
                        countdown_seconds = int(numbers[0])
                        # Clamp between 5 and 90 seconds
                        countdown_seconds = max(5, min(90, countdown_seconds))
                    except:
                        countdown_seconds = 10
            
            # Confirm and start countdown
            confirm_msg = f"Alright! {player_name} will have {countdown_seconds} seconds to complete. {selected_punishment}. Get ready!"
            self.text_to_speech(confirm_msg, "start_countdown.wav")
            
            time.sleep(1)
            
            # Execute the countdown with display
            self.display_punishment_name(player_name, countdown_seconds, selected_punishment)
            
            # Completion message
            done_msg = f"Time up! {player_name} has completed the punishment. Great job everyone!"
            self.text_to_speech(done_msg, "punishment_complete.wav")
            
            return True
            
        except Exception as e:
            print(f"Error in punishment countdown: {e}")
            error_msg = "Sorry, there was an issue with the punishment countdown."
            self.text_to_speech(error_msg, "punishment_error.wav")
            return False

    def run_ideabox_assistant(self, use_microphone=False):
        """Run the ideaBox AI-powered creative assistant"""
        print("Welcome to ideaBox - Your AI Creative Game Assistant!")
        print("====================================================")
        
        # Play intro sound
        self.play_intro_sound()
        time.sleep(1)
        
        # Step 1: Ask what game they're playing
        game_question = "Hi! I'm ideaBox, your AI creative assistant. What party game are you currently playing or about to play?"
        self.text_to_speech(game_question, "game_question.wav")
        
        game_response = self.get_user_input(use_microphone, "game", duration=8)
        
        if not game_response:
            game_response = "party game"
        
        self.current_game = game_response
        print(f"Game: {self.current_game}")
        
        # Step 2: Ask about punishments specifically
        punishment_question = f"Perfect! First, do you need creative punishment ideas for losing players in your {self.current_game}?"
        self.text_to_speech(punishment_question, "punishment_question.wav")
        
        wants_punishments = self.get_user_input(use_microphone, "confirmation", duration=6)
        
        if self.parse_confirmation(wants_punishments):
            # Get AI-powered punishment suggestions
            punishment_suggestions = self.get_ai_creative_suggestions(
                self.current_game, 
                "punishments"
            )
            
            # Offer punishment countdown with the suggestions
            self.handle_punishment_countdown(use_microphone, punishment_suggestions)
        
        # Step 3: Ask for other creative help
        other_help_question = "What other creative ideas would you like? I can suggest themes, game variations, or anything else to make your game more fun!"
        self.text_to_speech(other_help_question, "other_help.wav")
        
        help_request = self.get_user_input(use_microphone, "general", duration=10)
        
        if help_request:
            # Determine what type of help they want and get AI suggestions
            request_type = self.determine_request_type(help_request)
            
            ai_suggestions = self.get_ai_creative_suggestions(
                self.current_game, 
                request_type, 
                help_request
            )
            self.text_to_speech(ai_suggestions, "ai_suggestions.wav")
            time.sleep(2)
        
        # Step 4: Offer continued help
        continue_question = "Would you like any more creative ideas for your game?"
        self.text_to_speech(continue_question, "continue.wav")
        
        continue_response = self.get_user_input(use_microphone, "confirmation", duration=6)
        
        if self.parse_confirmation(continue_response):
            bonus_question = "What specific aspect of your game would you like to enhance?"
            self.text_to_speech(bonus_question, "bonus_question.wav")
            
            bonus_request = self.get_user_input(use_microphone, "general", duration=10)
            
            if bonus_request:
                bonus_suggestions = self.get_ai_creative_suggestions(
                    self.current_game,
                    "general", 
                    bonus_request
                )
                self.text_to_speech(bonus_suggestions, "bonus_suggestions.wav")
        
        # Step 5: Farewell
        farewell = f"Have an amazing time with your {self.current_game}! This is ideaBox signing off - remember, creativity and laughter are the most important ingredients for any great party game!"
        self.text_to_speech(farewell, "farewell.wav")
        
        print("\nideaBox session complete!")
        return {
            "game": self.current_game,
            "ai_powered": True,
            "session_complete": True
        }


def main():
    ideabox = IdeaBoxAssistant()
    
    # Check microphone availability
    mic_available = False
    try:
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        mic_available = len(result.stdout.strip()) > 0
    except:
        pass
    
    if mic_available:
        print("Microphone detected!")
        use_mic = input("Use microphone? (y/n): ").lower().startswith('y')
    else:
        print("No microphone detected - using simulation mode")
        use_mic = False
    
    # Run ideaBox
    result = ideabox.run_ideabox_assistant(use_microphone=use_mic)
    
    # Log results
    print("\nideaBox SESSION LOG:")
    print("====================")
    print("Game:", result.get("game", "Unknown"))
    print("AI-powered suggestions:", "Yes" if result.get("ai_powered") else "No")
    print("Session completed:", "Yes" if result.get("session_complete") else "No")


if __name__ == "__main__":
    main()