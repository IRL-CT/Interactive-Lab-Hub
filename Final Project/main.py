import time
import board
import digitalio
import subprocess
import numpy as np
import sounddevice as sd
import pygame
from touch_input import TouchInput
from audio_player import AudioPlayer
from display import Display
from vintage_mic import VintageMicRecorder
from config import OBJECTS

def load_text(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except:
        return ""

def main():
    # --- HARDWARE SETUP ---
    touch = TouchInput()
    audio = AudioPlayer()
    screen = Display()
    vintage_mic = VintageMicRecorder()

    # Button A (Top) -> Show Photo
    button_a = digitalio.DigitalInOut(board.D23)
    button_a.switch_to_input(pull=digitalio.Pull.UP)
    
    # Button B (Bottom) -> Show Text
    button_b = digitalio.DigitalInOut(board.D24)
    button_b.switch_to_input(pull=digitalio.Pull.UP)

    # --- STATE VARIABLES ---
    is_idle_mode = True
    current_active_pad = None
    is_recording = False
    audio_end_time = None  # Track when audio finished

    # Configuration
    LOCK_DURATION = 10
    POST_AUDIO_WAIT = 5  # Seconds to wait after audio before going to idle
    
    unlock_time = 0
    last_interaction_time = time.time()

    print("=" * 50)
    print("   Museum of Lost Sounds")
    print("   LIFT detection mode")
    print("=" * 50)
    screen.show_idle()

    while True:
        current_time = time.time()

        # Skip everything while recording microphone
        if is_recording:
            time.sleep(0.1)
            continue

        # ----------------------------------------
        # 1. CHECK IF AUDIO FINISHED -> START WAIT TIMER
        # ----------------------------------------
        if not is_idle_mode and current_active_pad is not None:
            obj = OBJECTS[current_active_pad]
            if obj.get("type") != "microphone":
                # Check if audio just finished
                if not audio.is_busy() and audio_end_time is None:
                    print("Audio finished. Starting 5 second wait...")
                    audio_end_time = current_time
                
                # Check if 5 seconds passed -> go to idle
                if audio_end_time is not None and (current_time - audio_end_time >= POST_AUDIO_WAIT):
                    print("Going to idle...")
                    screen.show_idle()
                    is_idle_mode = True
                    current_active_pad = None
                    audio_end_time = None

        # ----------------------------------------
        # 2. BUTTON A: SHOW PHOTO (not for microphone)
        # ----------------------------------------
        if not button_a.value and current_active_pad is not None:
            obj = OBJECTS[current_active_pad]
            # Skip buttons for microphone
            if obj.get("type") != "microphone":
                print("Button A: Showing Action Photo")
                last_interaction_time = current_time
                audio_end_time = current_time  # Reset 5 second timer
                screen.show_photo(obj["action_image"], obj["year_text"])
                time.sleep(0.2)

        # ----------------------------------------
        # 3. BUTTON B: SHOW TEXT (not for microphone)
        # ----------------------------------------
        if not button_b.value and current_active_pad is not None:
            obj = OBJECTS[current_active_pad]
            # Skip buttons for microphone
            if obj.get("type") != "microphone":
                print("Button B: Switching back to Text")
                last_interaction_time = current_time
                audio_end_time = current_time  # Reset 5 second timer
                text = load_text(obj["info"])
                screen.show_info(obj["name"], text)
                time.sleep(0.2)

        # ----------------------------------------
        # 4. CHECK FOR OBJECT LIFT
        # ----------------------------------------
        if current_time >= unlock_time:
            lifted_pad = touch.get_lifted()
            
            if lifted_pad is not None and lifted_pad in OBJECTS:
                last_interaction_time = current_time
                is_idle_mode = False
                current_active_pad = lifted_pad
                
                obj = OBJECTS[lifted_pad]
                
                # ============================================
                # SPECIAL: VINTAGE MICROPHONE
                # ============================================
                if obj.get("type") == "microphone":
                    print("=" * 40)
                    print("[MIC] MICROPHONE ACTIVATED!")
                    print("=" * 40)
                    
                    is_recording = True
                    unlock_time = current_time + 30
                    
                    record_duration = obj.get("record_duration", 3)
                    
                    # Step 1: Show "Get Ready" (centered, big)
                    screen.show_mic_message("Vintage Mic", "Speak into the microphone!")
                    
                    # Use Piper TTS to speak the ready message
                    try:
                        message = "Speak into the microphone after the beep!"
                        piper_cmd = f'echo "{message}" | /home/pi/piper/piper/piper --model /home/pi/piper/en_US-lessac-medium.onnx --output-raw | aplay -r 22050 -f S16_LE -t raw -q'
                        subprocess.run(piper_cmd, shell=True, timeout=10)
                        print("[PIPER] Spoke ready message")
                    except Exception as e:
                        print(f"[PIPER] Error: {e}")
                        time.sleep(2)
                    
                    time.sleep(1)
                    
                    # Step 2: Countdown (3, 2, 1, GO!)
                    def play_countdown_beep(frequency=800, duration_ms=200):
                        """Generate a beep sound using pygame."""
                        try:
                            sample_rate = 22050
                            n_samples = int(sample_rate * duration_ms / 1000)
                            t = np.linspace(0, duration_ms / 1000, n_samples, False)
                            wave = np.sin(2 * np.pi * frequency * t) * 0.5
                            fade = np.linspace(1, 0, n_samples)
                            wave = wave * fade
                            wave_int = (wave * 32767).astype(np.int16)
                            stereo = np.column_stack((wave_int, wave_int))
                            sound = pygame.sndarray.make_sound(stereo)
                            sound.play()
                            time.sleep(duration_ms / 1000 + 0.1)
                        except Exception as e:
                            print(f"[BEEP] Error: {e}")
                    
                    # Initialize pygame mixer if needed
                    if not pygame.mixer.get_init():
                        pygame.mixer.init(frequency=22050, size=-16, channels=2)
                    
                    # Big countdown display: 3, 2, 1
                    for i, freq in [(3, 600), (2, 700), (1, 800)]:
                        screen.show_mic_countdown(i)
                        play_countdown_beep(frequency=freq, duration_ms=300)
                        time.sleep(0.7)
                    
                    # GO!
                    screen.show_mic_countdown("GO!")
                    play_countdown_beep(frequency=1000, duration_ms=400)
                    time.sleep(0.5)
                    
                    # Step 3: Recording with countdown
                    print(f"[MIC] Recording for {record_duration} seconds...")
                    
                    all_audio = []
                    chunk_duration = 1
                    
                    for remaining in range(record_duration, 0, -1):
                        # Big centered recording display
                        screen.show_mic_recording(remaining)
                        
                        # Record 1 second chunk
                        chunk = sd.rec(
                            int(chunk_duration * vintage_mic.sample_rate),
                            samplerate=vintage_mic.sample_rate,
                            channels=1,
                            dtype='float32',
                            device=vintage_mic.device
                        )
                        sd.wait()
                        all_audio.append(chunk.flatten())
                    
                    # Combine all chunks
                    vintage_mic.recording = np.concatenate(all_audio)
                    print(f"[OK] Recording complete: {len(vintage_mic.recording)} samples")
                    
                    # Step 4: Processing
                    screen.show_mic_message("Processing...", "Adding vintage magic!")
                    vintage_audio = vintage_mic.apply_vintage_effect()
                    time.sleep(1)
                    
                    # Step 5: Playback
                    screen.show_mic_message("Listen!", "Your voice from 1940s")
                    time.sleep(0.5)
                    vintage_mic.play(vintage_audio)
                    
                    # Step 6: Done
                    screen.show_mic_message("Done!", "Pick up the mic!")
                    time.sleep(3)
                    
                    # Go back to idle immediately
                    screen.show_idle()
                    is_idle_mode = True
                    current_active_pad = None
                    
                    is_recording = False
                    last_interaction_time = time.time()
                    print("[MIC] Microphone interaction complete")
                
                # ============================================
                # STANDARD: PLAY PRE-RECORDED SOUND
                # ============================================
                else:
                    print(f"Object lifted from pad {lifted_pad}: {obj['name']}")
                    
                    unlock_time = current_time + LOCK_DURATION
                    
                    # Play audio
                    audio.play(obj["audio"], duration_sec=LOCK_DURATION)

                    # Show text info
                    text = load_text(obj["info"])
                    screen.show_info(obj["name"], text)
                    
                    # Note: Idle mode will trigger automatically when audio finishes
                    # (handled in section 1 above)
                
                time.sleep(0.3)

        time.sleep(0.05)

if __name__ == "__main__":
    main()