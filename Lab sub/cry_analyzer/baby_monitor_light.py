"""
Automatic Baby Monitor - All Sounds Detection with LED Ring
1. Continuously listens for sounds
2. YAMNet detects crying, laughing, AND babbling
3. When crying → DeepInfant classifies cry type
4. Shows results on LED ring with colors
"""

import time
import board
import numpy as np
import librosa
import json
from pathlib import Path
import neopixel_spi as neopixel

try:
    import tensorflow as tf
    import tensorflow_hub as hub
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization
except ImportError:
    raise ImportError("Install: pip3 install tensorflow==2.15.0 tensorflow-hub")

# ============================================
# LED CONFIGURATION
# ============================================

spi = board.SPI()
NUM_PIXELS = 24
pixels = neopixel.NeoPixel_SPI(
    spi, 
    NUM_PIXELS, 
    brightness=0.3, 
    auto_write=False,
    pixel_order=neopixel.GRB
)

# ============================================
# COLORS (R, G, B format)
# ============================================

# Cry type colors
LED_COLORS = {
    'belly_pain': (255, 0, 0),      # RED
    'hungry': (255, 140, 0),        # ORANGE
    'tired': (0, 100, 255),         # BLUE
    'burping': (255, 165, 0),       # ORANGE
    'discomfort': (139, 69, 19),    # BROWN
    'cold_hot': (100, 150, 255),    # LIGHT BLUE
    'lonely': (150, 150, 255),      # LAVENDER
    'scared': (255, 50, 50),        # BRIGHT RED
    'unknown': (150, 150, 150),     # GRAY
}

# Happy sounds colors
LED_COLORS['laughing'] = (255, 200, 0)   # YELLOW
LED_COLORS['babbling'] = (0, 255, 200)   # CYAN

# Status colors
COLOR_LISTENING = (20, 20, 20)           # DIM WHITE
COLOR_OFF = (0, 0, 0)                    # OFF

# ============================================
# LED FUNCTIONS
# ============================================

def set_all_leds(color):
    """Set all LEDs to one color"""
    for i in range(NUM_PIXELS):
        pixels[i] = color
    pixels.show()

def clear_leds():
    """Turn off all LEDs"""
    set_all_leds(COLOR_OFF)

def led_listening():
    """Dim white for listening state"""
    set_all_leds(COLOR_LISTENING)

def led_analyzing():
    """Circling white animation while analyzing"""
    # Clear first
    clear_leds()
    
    # Create circling effect - repeat 3 times
    for _ in range(3):
        for i in range(NUM_PIXELS):
            # Turn on current LED bright white
            pixels[i] = (255, 255, 255)
            # Fade previous LED
            prev_i = (i - 1) % NUM_PIXELS
            pixels[prev_i] = (50, 50, 50)
            # Turn off LED before that
            prev_prev_i = (i - 2) % NUM_PIXELS
            pixels[prev_prev_i] = (0, 0, 0)
            
            pixels.show()
            time.sleep(0.05)  # Speed of circle
    
    # End with dim white
    set_all_leds(COLOR_LISTENING)

def led_result(result_type, confidence=100):
    """Display result with color and brightness based on confidence"""
    color = LED_COLORS.get(result_type, (150, 150, 150))
    
    # Adjust brightness based on confidence (if needed)
    # For now, just show the color fully
    
    # Pulse effect - fade in
    steps = 10
    for step in range(steps):
        brightness = step / steps
        adjusted_color = tuple(int(c * brightness) for c in color)
        set_all_leds(adjusted_color)
        time.sleep(0.05)
    
    # Show full color
    set_all_leds(color)

def led_pulse(color, duration=3):
    """Pulse effect for a duration"""
    start_time = time.time()
    
    while time.time() - start_time < duration:
        # Fade in
        for brightness in range(0, 100, 5):
            adjusted_color = tuple(int(c * brightness / 100) for c in color)
            set_all_leds(adjusted_color)
            time.sleep(0.03)
        
        # Fade out
        for brightness in range(100, 0, -5):
            adjusted_color = tuple(int(c * brightness / 100) for c in color)
            set_all_leds(adjusted_color)
            time.sleep(0.03)

# ============================================
# YAMNET BABY SOUND DETECTOR (Stage 1)
# ============================================

class YAMNetBabySoundDetector:
    """Stage 1: Detect baby sounds (crying, laughing, babbling) using YAMNet"""
    def __init__(self):
        print("Loading YAMNet baby sound detector...")
        self.model = hub.load('https://tfhub.dev/google/yamnet/1')
        
        # Load class names
        class_map_path = tf.keras.utils.get_file(
            'yamnet_class_map.csv',
            'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
        )
        
        self.class_names = []
        with open(class_map_path) as f:
            next(f)  # Skip header
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    self.class_names.append(parts[2])
        
        self.baby_cry_indices = [20]
        self.laughter_indices = [14]
        self.babbling_indices = [4]
        
        print("YAMNet ready!")
    
    def detect_baby_sound(self, audio, threshold=0.25):
        """Check if audio contains baby sounds"""
        audio = audio.astype(np.float32)
        scores, embeddings, spectrogram = self.model(audio)
        mean_scores = np.mean(scores.numpy(), axis=0)
        
        cry_score = max([mean_scores[i] for i in self.baby_cry_indices if i < len(mean_scores)], default=0)
        laugh_score = max([mean_scores[i] for i in self.laughter_indices if i < len(mean_scores)], default=0)
        babble_score = max([mean_scores[i] for i in self.babbling_indices if i < len(mean_scores)], default=0)
        
        print(f"YAMNet Scores - Cry: {cry_score:.3f}, Laugh: {laugh_score:.3f}, Babble: {babble_score:.3f}")

        if laugh_score > 0.4: 
            return 'laughing', laugh_score * 100
        if cry_score > 0.25: 
            return 'crying', cry_score * 100
        if babble_score > 0.4: 
            return 'babbling', babble_score * 100
        
        return None, 0

# ============================================
# DEEPINFANT CRY CLASSIFIER (Stage 2)
# ============================================

class CryTypeClassifier:
    """Stage 2: Classify cry type using trained model"""
    def __init__(self, model_path='cry_model'):
        print("Loading cry type classifier...")
        self.model_path = Path(model_path)
        
        with open(self.model_path / 'config.json', 'r') as f:
            self.config = json.load(f)
        
        self.sample_rate = self.config.get('sample_rate', 16000)
        self.n_mfcc = self.config.get('n_mfcc', 40)
        
        with open(self.model_path / 'label_mapping.json', 'r') as f:
            label_map = json.load(f)
            self.labels = [label_map[str(i)] for i in range(len(label_map))]
        
        print(f"Cry types: {self.labels}")
        
        self.model = self._build_model()
        self._load_weights()
        
        print("Classifier ready!")
    
    def _build_model(self):
        model = Sequential([
            Conv1D(filters=32, kernel_size=3, activation='relu', input_shape=(40, 1)),
            BatchNormalization(),
            MaxPooling1D(pool_size=2),
            Conv1D(filters=64, kernel_size=3, activation='relu'),
            BatchNormalization(),
            MaxPooling1D(pool_size=2),
            Conv1D(filters=128, kernel_size=3, activation='relu'),
            BatchNormalization(),
            MaxPooling1D(pool_size=2),
            Flatten(),
            Dense(64, activation='relu'),
            Dropout(0.3),
            Dense(len(self.labels), activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        return model
    
    def _load_weights(self):
        weights_path = self.model_path / 'model_weights.weights.h5'
        if not weights_path.exists():
            weights_path = self.model_path / 'model_weights.h5'
        
        if weights_path.exists():
            self.model.load_weights(str(weights_path), skip_mismatch=True)
            print(f"Loaded weights from {weights_path}")
        else:
            raise ValueError(f"Weights not found at {weights_path}")
    
    def extract_features(self, audio):
        try:
            mfcc = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=self.n_mfcc)
            mfcc_scaled = np.mean(mfcc.T, axis=0)
            return mfcc_scaled
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None
    
    def classify(self, audio):
        """Classify cry type"""
        features = self.extract_features(audio)
        if features is None:
            return None, 0, None
        
        features = features / np.max(np.abs(features))
        features = features.reshape(1, 40, 1).astype(np.float32)
        
        output = self.model.predict(features, verbose=0)
        probabilities = output[0]
        
        predicted_idx = np.argmax(probabilities)
        confidence = probabilities[predicted_idx] * 100
        cry_type = self.labels[predicted_idx]
        
        return cry_type, confidence, probabilities

# ============================================
# COMBINED AUTO MONITOR
# ============================================

class AutoBabyMonitor:
    """Combined automatic baby monitor with LED feedback"""
    def __init__(self, 
                 model_path='cry_model',
                 sound_threshold=0.25,
                 classify_threshold=50,
                 recording_duration=3,
                 check_interval=1):
        
        import sounddevice as sd
        self.sd = sd
        
        self.sound_detector = YAMNetBabySoundDetector()
        self.cry_classifier = CryTypeClassifier(model_path)
        
        self.sound_threshold = sound_threshold
        self.classify_threshold = classify_threshold
        self.sample_rate = 16000
        self.recording_duration = recording_duration
        self.check_interval = check_interval
        
        self.total_checks = 0
        self.cry_count = 0
        self.laugh_count = 0
        self.babble_count = 0
        self.cry_type_counts = {label: 0 for label in self.cry_classifier.labels}
        
        # Start with listening state
        led_listening()
    
    def monitor(self):
        """Start automatic monitoring"""
        print("\n" + "="*60)
        print("AUTOMATIC BABY MONITOR - LED RING")
        print("="*60)
        print("Detects: Crying, Laughing, Babbling")
        print("\nLED Colors:")
        print("  Listening: Dim White")
        print("  Analyzing: Circling White")
        print("  Laughing: Yellow")
        print("  Hungry: Orange")
        print("  Belly Pain: Red")
        print("  Tired: Blue")
        print("  Discomfort: Brown")
        print("\nPress Ctrl+C to stop")
        print("="*60 + "\n")
        
        try:
            while True:
                self.total_checks += 1
                
                # Show listening
                led_listening()
                
                # Record audio
                audio = self.sd.rec(
                    int(self.recording_duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32'
                )
                self.sd.wait()
                audio = audio.flatten()
                
                # Check for baby sounds
                sound_type, confidence = self.sound_detector.detect_baby_sound(
                    audio, self.sound_threshold
                )
                
                print(f"[Check #{self.total_checks}] Detected: {sound_type} ({confidence:.1f}%)" if sound_type else f"[Check #{self.total_checks}] No baby sounds detected")
                
                if sound_type:
                    timestamp = time.strftime('%H:%M:%S')
                    
                    if sound_type == 'crying':
                        self.cry_count += 1
                        
                        print(f"\n[{timestamp}] CRYING DETECTED! (YAMNet: {confidence:.1f}%)")
                        
                        # Show analyzing animation
                        led_analyzing()
                        
                        # Classify cry type
                        cry_type, type_confidence, probs = self.cry_classifier.classify(audio)
                        
                        if cry_type and type_confidence >= self.classify_threshold:
                            self.cry_type_counts[cry_type] += 1
                            
                            print(f"  Cry Type: {cry_type.upper()} ({type_confidence:.1f}%)")
                            
                            # Show cry type color
                            led_result(cry_type, type_confidence)
                            
                            time.sleep(5)  # Show result longer
                        else:
                            print(f"  Low confidence ({type_confidence:.1f}%)")
                            time.sleep(2)
                    
                    elif sound_type == 'laughing':
                        self.laugh_count += 1
                        
                        print(f"\n[{timestamp}] LAUGHING DETECTED! ({confidence:.1f}%)")
                        
                        # Show yellow
                        led_result('laughing', confidence)
                        
                        time.sleep(3)
                    
                    elif sound_type == 'babbling':
                        self.babble_count += 1
                        
                        print(f"\n[{timestamp}] BABBLING DETECTED! ({confidence:.1f}%)")
                        
                        # Show cyan
                        led_result('babbling', confidence)
                        
                        time.sleep(3)
                
                else:
                    if self.total_checks % 10 == 0:
                        print(f"[Check #{self.total_checks}] All quiet...")
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self._show_summary()
            clear_leds()
    
    def _show_summary(self):
        """Show monitoring summary"""
        print("\n" + "="*60)
        print("MONITORING STOPPED")
        print("="*60)
        print(f"Total audio checks: {self.total_checks}")
        print(f"Baby sounds detected:")
        print(f"  Cries: {self.cry_count}")
        print(f"  Laughs: {self.laugh_count}")
        print(f"  Babbles: {self.babble_count}")
        
        if self.cry_count > 0:
            print("\nCry type breakdown:")
            for label, count in sorted(self.cry_type_counts.items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    print(f"  {label}: {count}")
        print("="*60)

# ============================================
# MAIN
# ============================================

def main():
    print("="*60)
    print("AUTOMATIC BABY MONITOR - LED RING")
    print("="*60)
    
    try:
        # Test LEDs first
        print("Testing LEDs...")
        led_listening()
        time.sleep(1)
        led_analyzing()
        time.sleep(1)
        led_listening()
        
        monitor = AutoBabyMonitor(
            model_path='./cry_model',
            sound_threshold=0.25,
            classify_threshold=50,
            recording_duration=4,
            check_interval=0
        )
        
        monitor.monitor()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
        # Flash red on error
        for _ in range(5):
            set_all_leds((255, 0, 0))
            time.sleep(0.2)
            clear_leds()
            time.sleep(0.2)
        
        raise
    finally:
        clear_leds()

if __name__ == '__main__':
    main()