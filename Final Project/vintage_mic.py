import numpy as np
import sounddevice as sd
from scipy import signal
from scipy.io import wavfile
import time
import os

class VintageMicRecorder:
    """
    Records audio and transforms it to sound like a vintage microphone.
    Perfect for the Museum of Lost Sounds!
    """
    
    def __init__(self, sample_rate=None, device=None):
        # Auto-detect C270 first
        if device is None:
            self.device = self._find_c270()
        else:
            self.device = device
        
        # Find a sample rate that actually works
        if sample_rate is None:
            self.sample_rate = self._find_working_sample_rate()
        else:
            self.sample_rate = sample_rate
        
        self.recording = None
        self.output_dir = "/home/pi/museum_project/recordings"
        
        # Create output directory if needed
        os.makedirs(self.output_dir, exist_ok=True)
        
        print("VintageMicRecorder initialized")
        print(f"Using device: {self.device}, Sample rate: {self.sample_rate} Hz")

    def _find_c270(self):
        """Auto-detect Logitech C270 webcam microphone."""
        devices = sd.query_devices()
        
        for i, dev in enumerate(devices):
            name = dev['name'].lower()
            if 'c270' in name or ('webcam' in name and dev['max_input_channels'] > 0):
                print(f"Found C270/webcam at device #{i}: {dev['name']}")
                return i
        
        print("C270 not found, using default input device")
        return None

    def _find_working_sample_rate(self):
        """Try common sample rates and return one that works."""
        # Common sample rates to try (in order of preference)
        rates_to_try = [16000, 22050, 44100, 48000, 8000, 32000]
        
        for rate in rates_to_try:
            try:
                # Try to open a short test stream
                test_stream = sd.InputStream(
                    device=self.device,
                    samplerate=rate,
                    channels=1,
                    dtype='float32'
                )
                test_stream.close()
                print(f"Working sample rate found: {rate} Hz")
                return rate
            except Exception as e:
                print(f"Sample rate {rate} Hz failed, trying next...")
                continue
        
        # Last resort fallback
        print("Warning: Could not verify sample rate, using 16000 Hz")
        return 16000

    def record(self, duration=5):
        """
        Record audio from microphone.
        
        Args:
            duration: Recording length in seconds
        
        Returns:
            numpy array of recorded audio
        """
        print(f"[MIC] Recording for {duration} seconds...")
        print(f"      Device: {self.device}, Rate: {self.sample_rate} Hz")
        
        # Record mono audio
        self.recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            device=self.device
        )
        
        # Wait for recording to complete
        sd.wait()
        
        # Flatten to 1D array
        self.recording = self.recording.flatten()
        
        print(f"[OK] Recording complete: {len(self.recording)} samples")
        return self.recording

    def apply_vintage_effect(self, audio=None):
        """
        Transform clean audio into vintage microphone sound.
        
        Effects chain:
        1. Bandpass filter (300Hz - 3kHz) - old mic frequency response
        2. Add tape hiss
        3. Add vinyl crackle
        4. Soft clipping (tube warmth)
        """
        if audio is None:
            audio = self.recording
        
        if audio is None:
            print("No audio to process!")
            return None
        
        print("[FX] Applying vintage effects...")
        
        # Normalize input
        audio = audio / (np.max(np.abs(audio)) + 0.001)
        
        # --- 1. BANDPASS FILTER (300Hz - 3kHz) ---
        nyquist = self.sample_rate / 2
        low_cut = min(300, nyquist * 0.8)
        high_cut = min(3000, nyquist * 0.9)
        
        low = low_cut / nyquist
        high = high_cut / nyquist
        
        if low < high and low > 0 and high < 1:
            b, a = signal.butter(4, [low, high], btype='band')
            audio = signal.filtfilt(b, a, audio)
            print(f"     [OK] Bandpass filter ({int(low_cut)}Hz-{int(high_cut)}Hz)")
        else:
            print("     [SKIP] Bandpass (sample rate too low)")
        
        # --- 2. ADD TAPE HISS ---
        hiss_level = 0.02
        hiss = np.random.normal(0, hiss_level, len(audio))
        
        hiss_cutoff = min(4000, nyquist * 0.9) / nyquist
        if hiss_cutoff > 0 and hiss_cutoff < 1:
            b_hiss, a_hiss = signal.butter(2, hiss_cutoff, btype='low')
            hiss = signal.filtfilt(b_hiss, a_hiss, hiss)
        
        audio = audio + hiss
        print("     [OK] Added tape hiss")
        
        # --- 3. ADD VINYL CRACKLE ---
        crackle = self._generate_crackle(len(audio))
        audio = audio + crackle * 0.03
        print("     [OK] Added vinyl crackle")
        
        # --- 4. SOFT CLIPPING (Tube Saturation) ---
        drive = 1.5
        audio = np.tanh(audio * drive) / np.tanh(drive)
        print("     [OK] Applied tube saturation")
        
        # --- 5. FINAL NORMALIZATION ---
        audio = audio / (np.max(np.abs(audio)) + 0.001) * 0.8
        
        print("[FX] Vintage effect complete!")
        return audio.astype(np.float32)

    def _generate_crackle(self, length):
        """Generate random pops and crackles like vinyl."""
        crackle = np.zeros(length)
        
        num_pops = int(length / self.sample_rate * 10)
        pop_positions = np.random.randint(0, length, num_pops)
        pop_amplitudes = np.random.uniform(0.3, 1.0, num_pops)
        
        for pos, amp in zip(pop_positions, pop_amplitudes):
            pop_len = np.random.randint(5, 20)
            end_pos = min(pos + pop_len, length)
            crackle[pos:end_pos] = amp * np.random.randn(end_pos - pos)
        
        return crackle

    def play(self, audio=None):
        """Play audio through speakers."""
        if audio is None:
            audio = self.recording
        
        if audio is None:
            print("No audio to play!")
            return
        
        print("[PLAY] Playing audio...")
        sd.play(audio, self.sample_rate)
        sd.wait()
        print("[OK] Playback complete")

    def record_and_transform(self, duration=8):
        """
        Full pipeline: Record -> Transform -> Play
        """
        # Record
        self.record(duration)
        
        # Small pause
        time.sleep(0.3)
        
        # Apply vintage effect
        vintage_audio = self.apply_vintage_effect()
        
        # Play transformed audio
        self.play(vintage_audio)
        
        return vintage_audio
