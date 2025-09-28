#!/usr/bin/env python3
"""
ideaBox - AI-Powered Party Game Creative Assistant
Provides creative suggestions for ongoing party games using AI.
"""

import subprocess
import time
import os
import sys
import random
import re
from pathlib import Path

class IdeaBoxAssistant:
    def __init__(self):
        self.piper_model = "en_US-lessac-medium"
        self.whisper_model = "tiny"
        self.current_game = None
        self.audio_dir = "audio"
        
        # Create audio directory if it doesn't exist
        os.makedirs(self.audio_dir, exist_ok=True)
        
    def text_to_speech(self, text, filename="output.wav"):
        """Convert text to speech using Piper"""
        try:
            print("ASSISTANT:", text)
            
            # Store audio file in audio directory
            audio_path = os.path.join(self.audio_dir, filename)
            
            # Use Piper for text-to-speech
            process = subprocess.run(
                ['piper', '--model', self.piper_model, '--output_file', audio_path],
                input=text,
                text=True,
                capture_output=True
            )
            
            if process.returncode == 0:
                # Play the audio
                subprocess.run(['aplay', audio_path], capture_output=True)
                return True
            else:
                print("TTS ERROR:", process.stderr)
                return False
                
        except Exception as e:
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
            print("Converting speech to text...")
            
            # Audio file is already in audio directory
            audio_path = os.path.join(self.audio_dir, audio_file)
            
            result = subprocess.run([
                'whisper', audio_path,
                '--model', self.whisper_model,
                '--output_format', 'txt',
                '--output_dir', self.audio_dir,
                '--verbose', 'False'
            ], capture_output=True, text=True)
            
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
            
            print("Getting AI creative suggestions...")
            
            # Create more open-ended prompts for variety
            if request_type == "punishments":
                prompt = f"""You're helping friends playing {game_type} who need creative consequences for losing. 

Give me 3-4 fun, lighthearted punishment ideas. Be creative and think outside the box! They should be:
- Quick and entertaining
- Safe and appropriate for everyone
- Something that makes people laugh

Context: {additional_context}

IMPORTANT: Your response will be read aloud by text-to-speech. Do not use emojis, asterisks, bullet points, or special characters. Write in natural spoken language only. Keep it conversational and under 120 words."""
            
            elif request_type == "themes":
                prompt = f"""Players are enjoying {game_type} and want fresh theme ideas to keep it interesting.

Suggest 4-5 creative themes or categories. Think of unexpected, fun angles that would make the game more exciting. 

Context: {additional_context}

IMPORTANT: Your response will be read aloud by text-to-speech. Do not use emojis, asterisks, bullet points, or special characters. Write in natural spoken language only. Be enthusiastic and keep it under 120 words."""
            
            elif request_type == "variations":
                prompt = f"""Friends playing {game_type} want to shake things up with some rule variations.

Give me 3-4 creative ways to modify the game. Think of fun twists that change the dynamic while keeping it enjoyable.

Context: {additional_context}

IMPORTANT: Your response will be read aloud by text-to-speech. Do not use emojis, asterisks, bullet points, or special characters. Write in natural spoken language only. Keep it energetic and under 120 words."""
            
            else:  # General creative help
                prompt = f"""Players of {game_type} are asking: "{additional_context}"

Help them make their game more fun and memorable. Be creative and think of practical suggestions they can use right now.

IMPORTANT: Your response will be read aloud by text-to-speech. Do not use emojis, asterisks, bullet points, or special characters. Write in natural spoken language only. Keep it enthusiastic and under 120 words."""
            
            # Call Ollama with longer timeout and better error handling
            result = subprocess.run([
                'ollama', 'run', 'llama3.2',
                prompt
            ], capture_output=True, text=True, timeout=60)  # Increased from 30 to 60 seconds
            
            if result.returncode == 0:
                response = result.stdout.strip()
                print("AI generated creative suggestions successfully")
                return response
            else:
                print("Ollama error:", result.stderr)
                return self.get_fallback_suggestion(request_type, game_type)
                
        except subprocess.TimeoutExpired:
            print("Ollama timeout - using fallback")
            return self.get_fallback_suggestion(request_type, game_type)
        except Exception as e:
            print("Ollama error:", e)
            return self.get_fallback_suggestion(request_type, game_type)

    def get_fallback_suggestion(self, request_type, game_type):
        """Fallback suggestions if AI isn't available"""
        fallbacks = {
            "punishments": f"""Here are some fun punishment ideas for your {game_type} losers:
            
• Do a 30-second victory dance for the winning team
• Tell a joke or funny story to make everyone laugh
• Give genuine compliments to each other player
• Act out their favorite animal for 1 minute
• Share an embarrassing (but harmless) childhood memory""",
            
            "themes": f"""Here are some amazing theme ideas for your {game_type}:
            
• 90s nostalgia (movies, music, trends)
• Childhood favorites (cartoons, games, snacks)
• Around the world (countries, landmarks, foods)
• Superheroes and villains
• Time travel (past decades or future predictions)""",
            
            "variations": f"""Here are some exciting variations to spice up your {game_type}:
            
• Speed rounds: Cut time limits in half
• Silent mode: No talking except for answers
• Team swap: Switch teams halfway through
• Prop challenge: Use random objects as hints
• Reverse rules: Play with opposite rules for one round"""
        }
        
        return fallbacks.get(request_type, f"I'd love to help with your {game_type}! Try asking me about punishments, themes, or variations.")

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

    def run_ideabox_assistant(self, use_microphone=False):
        """Run the ideaBox AI-powered creative assistant"""
        print("Welcome to ideaBox - Your AI Creative Game Assistant!")
        print("====================================================")
        
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
            self.text_to_speech(punishment_suggestions, "punishments.wav")
            time.sleep(2)
        
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