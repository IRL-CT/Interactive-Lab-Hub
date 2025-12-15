import time
import board
import neopixel
import numpy as np
import librosa
import json
from pathlib import Path

try:
    import tensorflow as tf
    import tensorflow_hub as hub
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization
except ImportError:
    raise ImportError("Install: pip3 install tensorflow==2.15.0 tensorflow-hub")

# ============================================
# NEOPIXEL CONFIGURATION (SAFE FOR PI POWER)
# ============================================

# NeoPixel setup - SAFE brightness for Pi power
PIXEL_PIN = board.D18          # GPIO 18 (PWM capable)
NUM_PIXELS = 12                # Common ring sizes: 12, 16, 24
BRIGHTNESS = 0.1               # 10% brightness (SAFE for Pi - max 0.2 for 12 LEDs)
PIXEL_ORDER = neopixel.GRB     # Or RGB depending on your ring

# Initialize NeoPixel ring
pixels = neopixel.NeoPixel(
    PIXEL_PIN, 
    NUM_PIXELS, 
    brightness=BRIGHTNESS,
    auto_write=False,
    pixel_order=PIXEL_ORDER
)

# ============================================
# COLORS (RGB values 0-255)
# ============================================

# Cry type colors
CRY_COLORS = {
    'belly_pain': (255, 0, 0),      # RED
    'hungry': (255, 200, 0),        # YELLOW
    'tired': (0, 150, 255),         # BLUE
    'burping': (255, 140, 0),       # ORANGE
    'discomfort': (200, 0, 255),    # PURPLE
    'cold_hot': (100, 150, 255),    # LIGHT BLUE
    'lonely': (150, 150, 255),      # LAVENDER
    'scared': (255, 50, 50),        # BRIGHT RED
    'unknown': (150, 150, 150),     # GRAY
}

# Happy sounds colors
HAPPY_COLORS = {
    'laughing': (255, 200, 0),      # BRIGHT YELLOW
    'babbling': (0, 255, 200),      # CYAN/TURQUOISE
}

COLOR_LISTENING = (0, 255, 0)      # GREEN
COLOR_ANALYZING = (255, 255, 0)    # YELLOW
COLOR_ERROR = (255, 0, 0)          # RED
COLOR_OFF = (0, 0, 0)              # OFF

# ============================================
# NEOPIXEL DISPLAY FUNCTIONS
# ============================================

def clear_pixels():
    """Turn off all pixels"""
    pixels.fill(COLOR_OFF)
    pixels.show()

def set_all_pixels(color):
    """Set all pixels to one color"""
    pixels.fill(color)
    pixels.show()

def breathing_effect(color, duration=2, steps=20):
    """Gentle breathing effect"""
    for _ in range(2):  # Two breaths
        # Fade in
        for i in range(steps):
            brightness = i / steps
            dimmed = tuple(int(c * brightness) for c in color)
            pixels.fill(dimmed)
            pixels.show()
            time.sleep(duration / (2 * steps))
        
        # Fade out
        for i in range(steps, 0, -1):
            brightness = i / steps
            dimmed = tuple(int(c * brightness) for c in color)
            pixels.fill(dimmed)
            pixels.show()
            time.sleep(duration / (2 * steps))

def pulse_effect(color, count=3):
    """Quick pulse effect"""
    for _ in range(count):
        pixels.fill(color)
        pixels.show()
        time.sleep(0.15)
        pixels.fill(COLOR_OFF)
        pixels.show()
        time.sleep(0.15)

def spinning_pixel(color, speed=0.05):
    """Single pixel spinning around ring"""
    for i in range(NUM_PIXELS):
        pixels.fill(COLOR_OFF)
        pixels[i] = color
        pixels.show()
        time.sleep(speed)

def confidence_bar(color, confidence):
    """Display confidence as filled pixels (0-100%)"""
    num_lit = int((confidence / 100) * NUM_PIXELS)
    pixels.fill(COLOR_OFF)
    for i in range(num_lit):
        pixels[i] = color
    pixels.show()

def rainbow_cycle(wait=0.05, cycles=2):
    """Rainbow cycle animation"""
    for j in range(256 * cycles):
        for i in range(NUM_PIXELS):
            pixel_index = (i * 256 // NUM_PIXELS) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions"""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

def display_listening():
    """Show listening state - gentle green breathing"""
    print("Display: LISTENING (green breathing)")
    breathing_effect(COLOR_LISTENING, duration=1.5, steps=15)

def display_analyzing():
    """Show analyzing state - yellow pulse"""
    print("Display: ANALYZING (yellow pulse)")
    pulse_effect(COLOR_ANALYZING, count=5)

def display_cry_result(cry_type, confidence, all_probs=None, labels=None):
    """Display cry detection result"""
    color = CRY_COLORS.get(cry_type, COLOR_OFF)
    print(f"Display: CRY - {cry_type.upper()} ({confidence:.1f}%)")
    
    # Show confidence bar
    confidence_bar(color, confidence)
    time.sleep(2)
    
    # Pulse the color
    pulse_effect(color, count=3)
    
    # Hold solid color
    set_all_pixels(color)

def display_happy_sound(sound_type, confidence):
    """Display happy sound (laughing/babbling)"""
    color = HAPPY_COLORS.get(sound_type, (255, 255, 255))
    print(f"Display: {sound_type.upper()} ({confidence:.1f}%)")
    
    # Rainbow for happiness
    rainbow_cycle(wait=0.02, cycles=1)
    
    # Then show the specific color
    set_all_pixels(color)

def display_error():
    """Display error state"""
    print("Display: ERROR (red blink)")
    pulse_effect(COLOR_ERROR, count=5)
    set_all_pixels(COLOR_ERROR)

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
        
        # Baby sound class indices in AudioSet/YAMNet
        self.baby_cry_indices = [20]     # "Baby cry, infant cry"
        self.laughter_indices = [14]     # "Laughter"
        self.babbling_indices = [4]      # "Babbling"
        
        print("YAMNet ready!")
    
    def detect_baby_sound(self, audio, threshold=0.25):
        """
        Check if audio contains baby sounds (crying, laughing, or babbling)
        Returns: (sound_type, confidence)
        """
        audio = audio.astype(np.float32)
        
        # Run YAMNet
        scores, embeddings, spectrogram = self.model(audio)
        mean_scores = np.mean(scores.numpy(), axis=0)
        
        # Check scores for all baby sounds
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
    def __init__(self, model_path='./cry_analyzer/cry_model'):
        print("Loading cry type classifier...")
        print(f"Model path: {Path(model_path)}")

        self.model_path = Path(model_path)
        print(f"Model path: {self.model_path.resolve()}")
        # Load configuration
        with open(self.model_path / 'config.json', 'r') as f:
            self.config = json.load(f)
        
        self.sample_rate = self.config.get('sample_rate', 16000)
        self.n_mfcc = self.config.get('n_mfcc', 40)
        
        # Load labels
        with open(self.model_path / 'label_mapping.json', 'r') as f:
            label_map = json.load(f)
            self.labels = [label_map[str(i)] for i in range(len(label_map))]
        
        print(f"Cry types: {self.labels}")
        
        # Build and load model
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
    """Combined automatic baby monitor with NeoPixel display"""
    def __init__(self, 
                 model_path='./cry_analyzer/cry_model',
                 sound_threshold=0.25,
                 classify_threshold=50,
                 recording_duration=3,
                 check_interval=1):
        
        import sounddevice as sd
        self.sd = sd
        
        # Initialize both models
        self.sound_detector = YAMNetBabySoundDetector()
        self.cry_classifier = CryTypeClassifier(model_path)
        
        self.sound_threshold = sound_threshold
        self.classify_threshold = classify_threshold
        self.sample_rate = 16000
        self.recording_duration = recording_duration
        self.check_interval = check_interval
        
        # Statistics
        self.total_checks = 0
        self.cry_count = 0
        self.laugh_count = 0
        self.babble_count = 0
        self.cry_type_counts = {label: 0 for label in self.cry_classifier.labels}
        
        # Initial display
        clear_pixels()
        display_listening()
    
    def monitor(self):
        """Start automatic monitoring"""
        print("\n" + "="*60)
        print("AUTOMATIC BABY MONITOR - NEOPIXEL VERSION")
        print("="*60)
        print(f"NeoPixels: {NUM_PIXELS} LEDs at {BRIGHTNESS*100:.0f}% brightness")
        print("Detects: Crying, Laughing, Babbling")
        print("\nMonitoring started...")
        print("Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        try:
            while True:
                self.total_checks += 1
                
                # Show listening state
                display_listening()
                
                # Record audio
                audio = self.sd.rec(
                    int(self.recording_duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32'
                )
                self.sd.wait()
                audio = audio.flatten()
                
                # STAGE 1: Check for baby sounds with YAMNet
                sound_type, confidence = self.sound_detector.detect_baby_sound(
                    audio, self.sound_threshold
                )
                
                if sound_type:
                    timestamp = time.strftime('%H:%M:%S')
                    
                    if sound_type == 'crying':
                        # CRYING detected - classify the type
                        self.cry_count += 1
                        print(f"\n[{timestamp}] CRYING DETECTED! (YAMNet: {confidence:.1f}%)")
                        
                        display_analyzing()
                        
                        # STAGE 2: Classify cry type
                        cry_type, type_confidence, probs = self.cry_classifier.classify(audio)
                        
                        if cry_type and type_confidence >= self.classify_threshold:
                            self.cry_type_counts[cry_type] += 1
                            
                            print(f"  Cry Type: {cry_type.upper()} ({type_confidence:.1f}%)")
                            
                            # Display cry classification
                            display_cry_result(cry_type, type_confidence, probs, self.cry_classifier.labels)
                            
                            time.sleep(5)
                        else:
                            print(f"  Low confidence ({type_confidence:.1f}%)")
                            time.sleep(2)
                    
                    elif sound_type == 'laughing':
                        self.laugh_count += 1
                        print(f"\n[{timestamp}] LAUGHING DETECTED! ({confidence:.1f}%)")
                        display_happy_sound('laughing', confidence)
                        time.sleep(3)
                    
                    elif sound_type == 'babbling':
                        self.babble_count += 1
                        print(f"\n[{timestamp}] BABBLING DETECTED! ({confidence:.1f}%)")
                        display_happy_sound('babbling', confidence)
                        time.sleep(3)
                
                else:
                    if self.total_checks % 10 == 0:
                        print(f"[Check #{self.total_checks}] All quiet...")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self._show_summary()
    
    def _show_summary(self):
        """Show monitoring summary"""
        print("\n" + "="*60)
        print("MONITORING STOPPED")
        print("="*60)
        print(f"Total checks: {self.total_checks}")
        print(f"Cries: {self.cry_count}, Laughs: {self.laugh_count}, Babbles: {self.babble_count}")
        
        if self.cry_count > 0:
            print("\nCry types:")
            for label, count in sorted(self.cry_type_counts.items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    print(f"  {label}: {count}")
        print("="*60)
        
        # Final display - turn off
        clear_pixels()

# ============================================
# MAIN
# ============================================

def main():
    print("="*60)
    print("AUTOMATIC BABY MONITOR - NEOPIXEL VERSION")
    print("="*60)
    print(f"NeoPixel Ring: {NUM_PIXELS} LEDs on GPIO {PIXEL_PIN}")
    print(f"Brightness: {BRIGHTNESS*100:.0f}% (SAFE for Pi power)")
    print("="*60)
    
    try:
        # Test NeoPixels on startup
        print("\nTesting NeoPixels...")
        rainbow_cycle(wait=0.02, cycles=1)
        clear_pixels()
        time.sleep(0.5)
        
        monitor = AutoBabyMonitor(
            model_path='./cry_analyzer/cry_model',
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
        display_error()
        raise
    
    finally:
        # Always turn off LEDs on exit
        clear_pixels()
        print("NeoPixels turned off")

if __name__ == '__main__':
    main()