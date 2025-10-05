#!/usr/bin/env python3
# -*- coding: utf-8 -*-
### Interactive Cooking Assistant with Ollama Integration
### This script implements a step-by-step cooking guide with voice interaction and button control.


import requests
import json
import subprocess
import sys
import time
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import datetime
import threading
import re
import select
import logging
from enum import Enum

# Try to import digitalio button support
try:
    import digitalio
    import board
    DIGITALIO_BUTTON_AVAILABLE = True
    print("DigitalIO button support available")
except ImportError:
    DIGITALIO_BUTTON_AVAILABLE = False
    print("DigitalIO button support not available")

class CookingState(Enum):
    WAITING_FOR_INGREDIENTS = 1
    WAITING_FOR_DISH_SELECTION = 2
    WAITING_FOR_STEPS_CONFIRMATION = 3
    WAITING_FOR_BUTTON_PRESS = 4
    EXECUTING_STEPS = 5
    WAITING_FOR_FINAL_BUTTON = 6
    COMPLETED = 7

class CookingAssistant:
    def __init__(self):
        self.current_state = CookingState.WAITING_FOR_INGREDIENTS
        self.ingredients = ""
        self.available_dishes = []
        self.selected_dish = ""
        self.cooking_steps = []
        self.current_step = 0
        self.audio_queue = queue.Queue()
        
        # Setup logging to .log file first
        self.setup_logging()
        
        # Button setup (keyboard input only)
        self.button_available = False
        self.button_pressed = False  # Track button press state
        self.last_button_time = 0  
        self.listen_to_speech = True  # Control speech listening
        self.setup_buttons()
        
        # Audio setup
        self.setup_audio()
        
        # Tinyllama setup
        self.model = "tinyllama"  
        
        # Conversation log
        self.conversation_log = "cooking_conversation_log.txt"
        self.init_log()
        


    ### Logging Functions ###
    def setup_logging(self):
        # Setup logging to .log file
        # Create logger
        self.logger = logging.getLogger('CookingAssistant')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        log_filename = "cooking_assistant.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        
        # Set the format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler) # Add handler to logger
        
        # Start Logging
        self.logger.info("Cooking Assistant started")
        print(f"[LOG] Logging to file: {log_filename}")
        
    def log_info(self, message):
        # Log info message to both console and file
        print(f"[INFO] {message}")
        self.logger.info(message)
        
    def log_error(self, message):
        # Log error message to both console and file
        print(f"[ERROR] {message}")
        self.logger.error(message)
        
    def log_debug(self, message):
        # Log debug message to both console and file
        print(f"[DEBUG] {message}")
        self.logger.debug(message)
        
    ### Core Functions ###
    def setup_buttons(self):
        # Setup digitalio button detection
        if DIGITALIO_BUTTON_AVAILABLE:
            try:
                # DigitalIO button setup (GPIO23)
                self.buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
                self.buttonA.switch_to_input(pull=digitalio.Pull.UP)
                
                self.button_available = True
                self.log_info("DigitalIO button setup successful (GPIO23)")
                self.log_info("Button is configured with pull-up resistor")
                self.log_info("Button pressed = LOW (False), Button released = HIGH (True)")
                
                # Test initial button state
                initial_state = self.buttonA.value
                self.log_info(f"Initial button state: {initial_state} ({'RELEASED' if initial_state else 'PRESSED'})")
                
            except Exception as e:
                self.log_error(f"DigitalIO button setup failed: {e}")
                self.button_available = False
        else:
            self.log_info("DigitalIO button support not available, using keyboard input instead")
            self.log_info("Press 'b' key to simulate button press")
            self.button_available = False
        
    def setup_audio(self):
        # Setup audio for speech recognition
        try:
            self.vosk_model = Model(lang="en-us")
            self.log_info("Vosk model loaded successfully")
        except Exception as e:
            self.log_error(f"Error loading Vosk model: {e}")
            sys.exit(1)
            
        try:
            device_info = sd.query_devices(None, "input")
            self.samplerate = int(device_info["default_samplerate"])
            self.log_info(f"Audio device configured - Sample rate: {self.samplerate}")
            self.log_info("Microphone is ready for speech input")
        except Exception as e:
            self.log_error(f"Error setting up audio device: {e}")
            sys.exit(1)
        
    def init_log(self):
        # Initialize conversation log
        with open(self.conversation_log, "w", encoding="utf-8") as f:
            f.write(f"Cooking Assistant Conversation Log - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60+"\n")
            
    def log_conversation(self, user_text, ai_response):
        # Log conversation to file
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.conversation_log, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] User: {user_text}\n")
            f.write(f"[{timestamp}] Assistant: {ai_response}\n")
            f.write("-"*50+"\n")
            
    def speak_text(self, text):
        # Convert text to speech using espeak
        # Clean the text first to remove duplicates
        cleaned_text = self.clean_ollama_response(text)
        clean_text = cleaned_text.encode('ascii', 'ignore').decode('ascii')
        print(f"Assistant: {clean_text}")
        
        # Temporarily pause speech listening while speaking
        original_listen_state = self.listen_to_speech
        self.listen_to_speech = False
        self.log_info("Paused speech listening while assistant is speaking")
        
        # Clear audio queue to prevent echo
        try:
            while not self.audio_queue.empty():
                self.audio_queue.get_nowait()
            self.log_info("Cleared audio queue to prevent echo")
        except queue.Empty:
            pass
        
        try:
            subprocess.run(['espeak', clean_text], shell=False, check=False)
            # Wait 2 seconds after speech
            time.sleep(2.0)
            
        except Exception as e:
            print(f"Speech error: {e}")
            time.sleep(2.0)  # Wait even if speech failed
        finally:
            # Resume speech listening after speaking
            self.listen_to_speech = original_listen_state
            self.log_info("Resumed speech listening after assistant finished speaking")
            
    def query_ollama(self, prompt, system_prompt=None):
        # Send prompt to Ollama with optional system prompt
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
                
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json().get('response', 'No response')
            else:
                return f"Error: {response.status_code}"
                
        except Exception as e:
            return f"Error: {e}"
            
    def check_ollama(self):
        # Check if Ollama is running
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=30)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                self.log_info(f"Ollama is running. Available models: {model_names}")
                return True
            else:
                self.log_error("Ollama is not responding")
                return False
        except Exception as e:
            self.log_error(f"Cannot connect to Ollama: {e}")
            self.log_error("Make sure Ollama is running with: ollama serve")
            return False
            
    def handle_button_press_detection(self):
        # Handle button press detection - using same logic as mood clock
        current_time = time.time()
        
        # Debouncing: ignore rapid button presses
        if current_time - self.last_button_time < 0.3:  # 300ms debounce
            return False
            
        if self.button_available and DIGITALIO_BUTTON_AVAILABLE:
            try:
                # Button A Detection (same as mood clock)
                press_A = (self.buttonA.value == False)  # Button pressed when LOW
                release_A = self.button_pressed and not press_A
                self.button_pressed = press_A
                
                if release_A:
                    self.log_info("DigitalIO button released! (GPIO23)")
                    self.handle_button_action()
                    self.last_button_time = current_time
                    return True
                    
            except Exception as e:
                self.log_error(f"DigitalIO button read error: {e}")
                self.button_available = False
                
        else:
            # Fallback to keyboard input
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key.lower() == 'b':
                    self.log_info("Button press detected (keyboard button)!")
                    self.handle_button_action()
                    self.last_button_time = current_time
                    return True
        return False

    def handle_button_action(self):
        # Process button action based on current state
        self.log_info("Button action triggered!")
        
        # If we're in button control mode (after step4), button always advances steps
        if self.current_state in [CookingState.WAITING_FOR_BUTTON_PRESS, CookingState.EXECUTING_STEPS, CookingState.WAITING_FOR_FINAL_BUTTON]:
            if self.current_state == CookingState.WAITING_FOR_FINAL_BUTTON:
                self.completion()
            else:
                self.next_step()
        else:
            # For earlier states, handle normally
            if self.current_state == CookingState.WAITING_FOR_BUTTON_PRESS:
                self.next_step()
            elif self.current_state == CookingState.EXECUTING_STEPS:
                self.next_step()
            elif self.current_state == CookingState.WAITING_FOR_FINAL_BUTTON:
                self.completion()
            
    def audio_callback(self, indata, frames, time, status):
        # Audio callback for speech recognition
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))
        

    def handle_user_speech(self, text):
        # Handle user speech input based on current state
        if "exit" in text.lower() or "quit" in text.lower():
            print("User wants to exit...")
            self.speak_text("Goodbye! Have a great day!")
            sys.exit(0)
            
        if self.current_state == CookingState.WAITING_FOR_INGREDIENTS:
            self.process_ingredients_input(text)
        elif self.current_state == CookingState.WAITING_FOR_DISH_SELECTION:
            self.process_dish_selection_input(text)
        elif self.current_state == CookingState.WAITING_FOR_STEPS_CONFIRMATION:
            self.process_steps_confirmation_input(text)
        elif self.current_state in [CookingState.EXECUTING_STEPS, CookingState.WAITING_FOR_FINAL_BUTTON]:
            self.handle_voice_during_cooking(text)
        elif self.current_state == CookingState.WAITING_FOR_BUTTON_PRESS:
            # During cooking preparation, allow questions
            self.handle_voice_during_cooking(text)
            
    def process_ingredients_input(self, text):
        # Process ingredients input from user
        print("Processing ingredients input...")
        validation_prompt = f"User said: '{text}'. Did they provide ingredients and mention what they want to cook? Answer only 'YES' if they provided both ingredients and dish preference, 'NO' if not."
        validation = self.query_ollama(validation_prompt)
        
        if "YES" in validation.upper():
            self.ingredients = text
            self.log_conversation(text, "Ingredients received")
            # Move to next step
            self.suggest_dishes()
        else:
            self.speak_text("I didn't quite catch that. Could you tell me what ingredients you have and what you'd like to cook?")
            # Stay in current state - the continuous listening loop will handle the next input
            
    def process_dish_selection_input(self, text):
        # Process dish selection input from user
        print("Processing dish selection...")
        selected_dish = self.map_selection_to_dish(text, self.available_dishes)
        
        if selected_dish:
            self.selected_dish = selected_dish
            self.log_conversation(text, "Dish selected")
            # Move to next step
            self.provide_steps()
            self.speak_text("say yes when you are ready to start cooking")
        else:
            self.speak_text("Could you please select one of the dishes I suggested? Just say the name or number.")
            # Stay in current state - the continuous listening loop will handle the next input
            
    def process_steps_confirmation_input(self, text):
        # Process steps confirmation input from user
        print("Processing steps confirmation...")
        validation_prompt = f"User said: '{text}'. Did they confirm they understand the steps and are ready to proceed? Look for words like 'ok', 'yes', 'good', 'ready', 'let's do it'. Answer only 'YES' if they confirmed, 'NO' if not."
        validation = self.query_ollama(validation_prompt)
        
        if "YES" in validation.upper():
            self.log_conversation(text, "Steps confirmed")
            # Move to next step
            self.ready_to_cook()
        else:
            self.speak_text("Please let me know when you're ready to start cooking. Say something like 'ok' or 'yes' when you're ready.")
            # Stay in current state - the continuous listening loop will handle the next input
        
    def clean_ollama_response(self, response):
        # Clean Ollama response to remove duplicates, labels, and fix formatting
        if not response:
            return response
            
        # Split into lines and remove empty lines
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        
        # Remove User: and System: labels and duplicate consecutive lines
        cleaned_lines = []
        prev_line = ""
        for line in lines:
            # Remove User: and System: labels
            if line.startswith('User:') or line.startswith('System:'):
                line = line.split(':', 1)[1].strip()
                if not line:
                    continue
            
            # Skip if same as previous line
            if line != prev_line:
                cleaned_lines.append(line)
                prev_line = line
        
        # Join back together
        cleaned_response = " ".join(cleaned_lines)
        
        # Remove any obvious duplicates in the middle of text
        words = cleaned_response.split()
        if len(words) > 10:  # Only check longer responses
            # Look for repeated phrases
            for i in range(len(words) - 5):
                phrase = " ".join(words[i:i+5])
                for j in range(i+5, len(words) - 4):
                    if phrase == " ".join(words[j:j+5]):
                        # Found duplicate, remove the second occurrence
                        words = words[:j] + words[j+5:]
                        break
        
        return " ".join(words)
            
    ### Recipe Functions ###
    def parse_dish_suggestion(self, response):
        """Parse dish suggestions and create mapping"""
        lines = response.split('\n')
        dishes = []
        for line in lines:
            line = line.strip()
            # Match patterns like "1. Dish Name", "1) Dish Name", "Number 1: Dish Name"
            match = re.match(r'^(?:\d+[.)]\s*|Number\s+\d+[:.]\s*)(.+)$', line, re.IGNORECASE)
            if match:
                dish_name = match.group(1).strip()
                dishes.append(dish_name)
        return dishes
        
    def map_selection_to_dish(self, user_input, dishes):
        # Map user selection (number or name) to actual dish
        user_input_lower = user_input.lower().strip()
        
        # Check for number selection
        number_match = re.search(r'\b(\d+)\b', user_input)
        if number_match:
            try:
                selection_num = int(number_match.group(1))
                if 1 <= selection_num <= len(dishes):
                    return dishes[selection_num - 1]
            except (ValueError, IndexError):
                pass
                
        # Check for word-based number selection
        word_to_num = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4,
            'one': 1, 'two': 2, 'three': 3, 'four': 4
        }
        for word, num in word_to_num.items():
            if word in user_input_lower and num <= len(dishes):
                return dishes[num - 1]
                
        # Check for direct dish name match
        for dish in dishes:
            if any(word in user_input_lower for word in dish.lower().split()):
                return dish
                
        return None
        
    def suggest_dishes(self):
        # Step 2: Suggest dishes based on ingredients
        system_prompt = """You are a cooking expert. Strictly only based on the ingredients provided, suggest 3-4 specific dish. Name only, no details or explanations. Just list the dish names with numbers like "1. Dish Name" format. Keep it simple and concise. Do NOT include any "User:" or "System:" labels in your response - just give a direct response as the cooking expert."""
        
        prompt = f"The user has these ingredients: {self.ingredients}. Suggest 3-4 specific dishes they can make."
        response = self.query_ollama(prompt, system_prompt)
        self.speak_text(response)
        
        # Parse dishes from response
        self.available_dishes = self.parse_dish_suggestion(response)
        
        # Set state - continuous listening loop will handle user input
        self.current_state = CookingState.WAITING_FOR_DISH_SELECTION

    def parse_cooking_steps(self, response):
        """Parse cooking steps using regex for better accuracy"""
        lines = response.split('\n')
        steps = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Match various step patterns
            patterns = [
                r'^(?:\d+[.)]\s*|Step\s+\d+[:.]\s*)(.+)$',  # "1. Step" or "Step 1: Step"
                r'^(?:\d+)\s*[\-:]\s*(.+)$',  # "1 - Step" or "1: Step"
                r'^Step\s+(?:\d+)\s*[:.]\s*(.+)$',  # "Step 1. Step" or "Step 1: Step"
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    step_text = match.group(1).strip()
                    if step_text:
                        steps.append(step_text)
                    break
                    
        return steps
        
    def provide_steps(self):
        # Step 3: Provide detailed cooking steps
        system_prompt = """You are a detailed cooking instructor. Only provide step-by-step cooking instructions for the selected dish. Make each step clear and actionable. Number each step clearly like "1. Step description" or "Step 1: Step description". Keep your response organized. Do NOT include any "User:" or "System:" labels in your response - just give a direct response as the cooking instructor."""
        
        prompt = f"The user wants to cook: {self.selected_dish}. Using these ingredients: {self.ingredients}. Provide detailed step-by-step cooking instructions."
        response = self.query_ollama(prompt, system_prompt)
        self.speak_text(response)
        
        # Parse steps from response using regex
        self.cooking_steps = self.parse_cooking_steps(response)
        
        # Set state - continuous listening loop will handle user input
        self.current_state = CookingState.WAITING_FOR_STEPS_CONFIRMATION
            
    def ready_to_cook(self):
        # Step 4: Tell user they can press button to start
        if self.button_available:
            message = "Great! Now you can press the button (GPIO23) to start cooking. I'll guide you through each step."
        else:
            message = "Great! Now you can press the button to start cooking. I'll guide you through each step."
        self.speak_text(message)
        self.current_state = CookingState.WAITING_FOR_BUTTON_PRESS
        
        # Keep speech listening enabled for questions during cooking
        self.listen_to_speech = True
        self.log_info("Speech listening enabled for cooking questions")
        
    def execute_steps(self):
        # Step 5: Execute cooking steps with button control
        if self.current_step < len(self.cooking_steps):
            step_text = self.cooking_steps[self.current_step]
            self.speak_text(f"Step {self.current_step + 1}: {step_text}")
            self.current_step += 1
            
            # Re-enable speech listening after step is spoken
            self.listen_to_speech = True
            self.log_info("Re-enabled speech listening after step completion")
            
            # Check if this was the last step
            if self.current_step >= len(self.cooking_steps):
                self.current_state = CookingState.WAITING_FOR_FINAL_BUTTON
                if self.button_available:
                    self.speak_text("That was the last step! Press the button one more time to complete cooking.")
                else:
                    self.speak_text("That was the last step! Press the button one more time to complete cooking.")
            else:
                self.current_state = CookingState.EXECUTING_STEPS
                # Tell user they can ask questions
                self.speak_text("You can ask me questions about this step, or press the button to continue to the next step.")
            
    def completion(self):
        # Step 6: Congratulate user on completion
        message = "Congratulations! You've completed all the cooking steps. Your dish should be ready now. Enjoy your meal!"
        self.speak_text(message)
        self.current_state = CookingState.COMPLETED
        
    def next_step(self):
        # Handle next step in cooking process
        if self.current_state == CookingState.WAITING_FOR_BUTTON_PRESS:
            self.current_state = CookingState.EXECUTING_STEPS
            self.execute_steps()
        elif self.current_state == CookingState.EXECUTING_STEPS:
            self.execute_steps()
            
    def handle_voice_during_cooking(self, user_input):
        # Handle voice input during cooking steps
        # Handle questions during any cooking-related state
        if self.current_state in [CookingState.WAITING_FOR_BUTTON_PRESS, CookingState.EXECUTING_STEPS, CookingState.WAITING_FOR_FINAL_BUTTON]:
            # Determine current step context
            if self.current_step <= len(self.cooking_steps) and self.current_step > 0:
                current_step_text = self.cooking_steps[self.current_step - 1]
            elif self.current_step > len(self.cooking_steps):
                current_step_text = "final step"
            else:
                current_step_text = "preparation phase"
            
            system_prompt = f"You are a cooking assistant helping with: {self.selected_dish}. The user is currently on this step: {current_step_text}. Answer their question or concern helpfully and briefly. Keep your response concise and avoid repeating yourself."
            
            prompt = f"User question: {user_input}"
            response = self.query_ollama(prompt, system_prompt)
            self.speak_text(response)
            self.log_conversation(user_input, response)
            
            # After answering, remind user they can press button to continue
            if self.current_state == CookingState.WAITING_FOR_BUTTON_PRESS:
                self.speak_text("You can press the button to start cooking, or ask me more questions.")
            elif self.current_state == CookingState.EXECUTING_STEPS:
                self.speak_text("You can press the button to continue to the next step, or ask me more questions.")
            elif self.current_state == CookingState.WAITING_FOR_FINAL_BUTTON:
                self.speak_text("You can press the button to complete cooking, or ask me more questions.")
            
            
    def run(self):
        # Main execution loop - continuous listening like voice_ai_assistant
        self.log_info("Cooking Assistant Starting...")
        self.log_info("=" * 50)
        
        if not self.check_ollama():
            return
        
        self.speak_text("Hi!")
        self.speak_text("Welcome to your cooking assistant! I'll help you cook step by step.")
        
        # Ask directly for ingredients
        self.speak_text("What ingredients do you have today? And what kind of dish would you like to make?")
        
        # Set initial state
        self.current_state = CookingState.WAITING_FOR_INGREDIENTS
        
        try:
            
            # Continuous listening loop (like voice_ai_assistant)
            with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, device=None,
                    dtype="int16", channels=1, callback=self.audio_callback):
                
                print("#" * 80)
                print("Listening for speech... Say 'exit' to quit")
                print("#" * 80)
                
                rec = KaldiRecognizer(self.vosk_model, self.samplerate)
                
                while True:
                    # Check for button press
                    if self.handle_button_press_detection():
                        print("Button pressed - continuing...")
                        continue
                    
                    # Debug: Monitor button state every 5 seconds
                    if hasattr(self, 'debug_counter'):
                        self.debug_counter += 1
                    else:
                        self.debug_counter = 0
                        
                    if self.debug_counter % 500 == 0:  # Every 5 seconds (500 * 0.01s)
                        if self.button_available and DIGITALIO_BUTTON_AVAILABLE:
                            current_state = self.buttonA.value
                            self.log_debug(f"Button state: {current_state} ({'RELEASED' if current_state else 'PRESSED'})")
                    
                    # Check for audio data - only if listening is enabled
                    if self.listen_to_speech and not self.audio_queue.empty():
                        data = self.audio_queue.get()
                        if rec.AcceptWaveform(data):
                            result = rec.Result()
                            result_json = json.loads(result)
                            text = result_json.get("text", "").strip()
                            
                            if text:
                                self.log_info(f"You said: {text}")
                                
                                # Handle speech input based on current state
                                if self.listen_to_speech:
                                    self.handle_user_speech(text)
                                elif not self.listen_to_speech and ("listen" in text.lower() or "help" in text.lower() or "question" in text.lower()):
                                    self.listen_to_speech = True
                                    self.speak_text("I'm listening. What's your question? You can also press the button to continue to the next step anytime.")
                                    self.log_info("Re-enabled speech listening for user question")
                        else:
                            # Only show partial results if we're listening to speech
                            if self.listen_to_speech:
                                partial = rec.PartialResult()
                                partial_json = json.loads(partial)
                                partial_text = partial_json.get("partial", "").strip()
                                if partial_text:
                                    print(f"Listening: {partial_text}", end='\r')
                    elif not self.listen_to_speech and not self.audio_queue.empty():
                        # If not listening, discard audio data to prevent accumulation
                        try:
                            self.audio_queue.get_nowait()
                        except queue.Empty:
                            pass
                    else:
                        time.sleep(0.01)  # Small delay to prevent busy waiting
                        
        except KeyboardInterrupt:
            self.log_info("Cooking session interrupted by user")
            self.speak_text("Goodbye! Have a great day!")
        except Exception as e:
            self.log_error(f"Error: {e}")
            self.speak_text("Sorry, I encountered an error.")
        finally:
            self.log_info("Cooking Assistant session ended")
            pass  # No GPIO cleanup needed

if __name__ == "__main__":
    assistant = CookingAssistant()
    assistant.run()
