import pygame

class AudioPlayer:
    def __init__(self):
        # Initialize the mixer
        pygame.mixer.init()
        self.sound = None
        print("AudioPlayer initialized.")

    # ---------------------------------------------------------
    # FIX: Added 'duration_sec=10' here to accept the argument
    # ---------------------------------------------------------
    def play(self, audio_file, duration_sec=10):
        """
        Plays the sound file.
        - duration_sec: limit playback to this many seconds.
        """
        try:
            # 1. Stop any currently playing sound
            if self.sound:
                self.sound.stop()
            
            # 2. Load the new sound
            self.sound = pygame.mixer.Sound(audio_file)
            
            # 3. Play with a time limit (maxtime)
            # We convert seconds to milliseconds (x 1000)
            ms_limit = int(duration_sec * 1000)
            self.sound.play(maxtime=ms_limit) 
            
            print(f"Playing {audio_file} (Limit: {duration_sec}s)")

        except Exception as e:
            print(f"Error playing sound: {e}")

    def is_busy(self):
        """
        Returns True if sound is playing, False if silence.
        """
        return pygame.mixer.get_busy()

    def stop(self):
        if self.sound:
            self.sound.stop()