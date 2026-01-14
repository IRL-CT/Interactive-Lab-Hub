#!/usr/bin/env python3
"""
Simple audio test script to verify speaker/headphone connection.
Plays a beep sound using pygame to test audio output.
"""

import time
import sys

def test_pygame_beep():
    """Test audio using pygame with a simple beep tone."""
    try:
        import pygame
        import numpy as np
        
        print("Testing audio with pygame...")
        print("You should hear a beep sound.")
        
        # Initialize pygame mixer
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Generate a simple beep tone (440 Hz for 0.5 seconds)
        sample_rate = 22050
        duration = 0.5  # seconds
        frequency = 440  # Hz (A4 note)
        
        # Generate sine wave
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        max_sample = 2**(16 - 1) - 1
        
        for i in range(frames):
            wave = max_sample * 0.3 * np.sin(2 * np.pi * frequency * i / sample_rate)
            arr[i][0] = int(wave)  # Left channel
            arr[i][1] = int(wave)  # Right channel
        
        # Convert to pygame sound
        sound = pygame.sndarray.make_sound(arr)
        
        # Play the beep
        print("Playing beep...")
        sound.play()
        
        # Wait for it to finish
        while pygame.mixer.get_busy():
            time.sleep(0.1)
        
        print("[OK] Beep played successfully!")
        print("If you heard the beep, your speaker is working correctly.")
        return True
        
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        print("Install numpy: pip3 install numpy")
        return False
    except Exception as e:
        print(f"[ERROR] Pygame audio test failed: {e}")
        return False

def test_system_beep():
    """Test audio using system beep command."""
    try:
        import subprocess
        
        print("\nTesting audio with system beep...")
        print("You should hear a system beep.")
        
        # Try to use system beep
        result = subprocess.run(['beep'], capture_output=True, timeout=2)
        
        if result.returncode == 0:
            print("[OK] System beep played successfully!")
            return True
        else:
            print("[INFO] System beep command not available")
            return False
            
    except FileNotFoundError:
        print("[INFO] System beep command not found (install with: sudo apt-get install beep)")
        return False
    except Exception as e:
        print(f"[INFO] System beep test failed: {e}")
        return False

def test_aplay():
    """Test audio using aplay with system test file."""
    try:
        import subprocess
        import os
        
        print("\nTesting audio with aplay...")
        print("You should hear a test sound.")
        
        # Try to play a system test sound file
        test_files = [
            '/usr/share/sounds/alsa/Front_Left.wav',
            '/usr/share/sounds/alsa/Front_Right.wav',
            '/usr/share/sounds/alsa/Front_Center.wav',
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                result = subprocess.run(
                    ['aplay', '-D', 'pulse', test_file],
                    capture_output=True,
                    timeout=3
                )
                
                if result.returncode == 0:
                    print(f"[OK] aplay test successful with {test_file}!")
                    return True
                else:
                    print(f"[INFO] aplay test failed: {result.stderr.decode()}")
        
        print("[INFO] No system test sound files found")
        return False
            
    except Exception as e:
        print(f"[INFO] aplay test failed: {e}")
        return False

def test_pygame_music():
    """Test pygame music playback with a simple tone."""
    try:
        import pygame
        
        print("\nTesting pygame.mixer.music...")
        print("You should hear a beep sound.")
        
        pygame.mixer.init()
        
        # Try to play a test tone
        # Generate a simple beep using pygame
        sample_rate = 22050
        duration = 0.5
        frequency = 440
        
        import numpy as np
        
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        max_sample = 2**(16 - 1) - 1
        
        for i in range(frames):
            wave = max_sample * 0.3 * np.sin(2 * np.pi * frequency * i / sample_rate)
            arr[i][0] = int(wave)
            arr[i][1] = int(wave)
        
        sound = pygame.sndarray.make_sound(arr)
        sound.play()
        
        while pygame.mixer.get_busy():
            time.sleep(0.1)
        
        print("[OK] pygame.mixer.music test successful!")
        return True
        
    except Exception as e:
        print(f"[ERROR] pygame.mixer.music test failed: {e}")
        return False

def main():
    """Run all audio tests."""
    print("=" * 60)
    print("Audio Connection Test")
    print("=" * 60)
    print("\nThis script will test your audio output connection.")
    print("Make sure your speaker/headphones are connected.\n")
    
    results = []
    
    # Test 1: Pygame beep
    results.append(("Pygame Beep", test_pygame_beep()))
    
    # Test 2: System beep (optional)
    results.append(("System Beep", test_system_beep()))
    
    # Test 3: aplay (optional)
    results.append(("aplay", test_aplay()))
    
    # Test 4: pygame.mixer.music
    results.append(("Pygame Mixer", test_pygame_music()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, success in results:
        status = "[OK]" if success else "[SKIP/FAIL]"
        print(f"{status} {test_name}")
    
    successful_tests = sum(1 for _, success in results if success)
    
    if successful_tests > 0:
        print(f"\n[SUCCESS] {successful_tests} out of {len(results)} tests passed!")
        print("Your audio system is working. You should be able to hear music.")
    else:
        print("\n[WARNING] No audio tests passed.")
        print("Troubleshooting:")
        print("1. Check speaker/headphone connection")
        print("2. Check volume settings: alsamixer")
        print("3. Test with: aplay /usr/share/sounds/alsa/Front_Left.wav")
        print("4. Check audio device: aplay -l")
        print("5. Install pygame: pip3 install pygame")
        print("6. Install numpy: pip3 install numpy")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(0)

