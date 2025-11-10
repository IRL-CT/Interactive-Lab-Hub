"""
Automatic Baby Monitor - All Sounds Detection
1. Continuously listens for sounds
2. YAMNet detects crying, laughing, AND babbling
3. When crying → DeepInfant classifies cry type
4. When laughing/babbling → Shows directly
5. Displays all results on screen
NO BUTTONS - Fully automatic!
"""

import time
import digitalio
import board
import numpy as np
import librosa
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from adafruit_rgb_display.rgb import color565
import adafruit_rgb_display.st7789 as st7789


try:
    import tensorflow as tf
    import tensorflow_hub as hub
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization
except ImportError:
    raise ImportError("Install: pip3 install tensorflow==2.15.0 tensorflow-hub")



import pygame

# Initialize pygame display instead of mini PiTFT
pygame.init()
screen = pygame.display.set_mode((240, 135))
pygame.display.set_caption("Baby Monitor")


# ============================================
# DISPLAY CONFIGURATION
# ============================================

cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None
BAUDRATE = 64000000

spi = board.SPI()

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 135
rotation = 90

# ============================================
# COLORS
# ============================================

# Cry type colors
CRY_COLORS_RGB = {
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
HAPPY_COLORS_RGB = {
    'laughing': (255, 200, 0),      # BRIGHT YELLOW
    'babbling': (0, 255, 200),      # CYAN/TURQUOISE
}

CRY_EMOJI = {
    'belly_pain': '!!!',
    'hungry': 'H',
    'tired': 'Z',
    'burping': 'B',
    'discomfort': 'D',
    'cold_hot': 'C/H',
    'lonely': 'L',
    'scared': 'S',
    'unknown': '?',
}

HAPPY_EMOJI = {
    'laughing': ':-D',
    'babbling': ':-)',
}

COLOR_LISTENING = (0, 255, 0)
COLOR_ANALYZING = (255, 255, 0)
COLOR_ERROR = (255, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# ============================================
# DISPLAY FUNCTIONS
# ============================================

def create_blank_image():
    return Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), COLOR_BLACK)

def draw_centered_text(draw, text, y_position, font, color=COLOR_WHITE):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (DISPLAY_WIDTH - text_width) // 2
    draw.text((x, y_position), text, font=font, fill=color)

def draw_progress_bar(draw, x, y, width, height, percentage, color):
    draw.rectangle([x, y, x + width, y + height], outline=COLOR_WHITE, fill=COLOR_BLACK)
    fill_width = int(width * (percentage / 100))
    if fill_width > 0:
        draw.rectangle([x, y, x + fill_width, y + height], fill=color)
    
    text = f"{percentage:.0f}%"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = x + (width - text_width) // 2
    text_y = y + (height - 12) // 2
    draw.text((text_x, text_y), text, font=font, fill=COLOR_WHITE)

def display_listening():
    image = create_blank_image()
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=COLOR_LISTENING)
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw_centered_text(draw, "LISTENING", 40, font_large, COLOR_BLACK)
    draw_centered_text(draw, "Auto-monitoring...", 75, font_small, COLOR_BLACK)
    
    display.image(image, rotation)

def display_analyzing():
    image = create_blank_image()
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=COLOR_ANALYZING)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw_centered_text(draw, "CRY DETECTED!", 40, font, COLOR_BLACK)
    draw_centered_text(draw, "Classifying...", 70, font_small, COLOR_BLACK)
    
    display.image(image, rotation)

def display_cry_result(cry_type, confidence, all_probs=None, labels=None):
    image = create_blank_image()
    draw = ImageDraw.Draw(image)
    
    bg_color = CRY_COLORS_RGB.get(cry_type, COLOR_WHITE)
    emoji = CRY_EMOJI.get(cry_type, '?')
    
    draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=bg_color)
    
    try:
        font_emoji = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 35)
        font_type = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_conf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except:
        font_emoji = ImageFont.load_default()
        font_type = ImageFont.load_default()
        font_conf = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw_centered_text(draw, emoji, 5, font_emoji, COLOR_WHITE)
    
    cry_name = cry_type.replace('_', ' ').upper()
    draw_centered_text(draw, cry_name, 48, font_type, COLOR_WHITE)
    
    conf_text = f"{confidence:.1f}%"
    draw_centered_text(draw, conf_text, 75, font_conf, COLOR_WHITE)
    
    draw_progress_bar(draw, 20, 95, 200, 12, confidence, COLOR_WHITE)
    
    # Show top 2 other predictions
    if all_probs is not None and labels is not None:
        sorted_indices = np.argsort(all_probs)[::-1]
        y_pos = 113
        for i, idx in enumerate(sorted_indices[1:3]):
            label = labels[idx].replace('_', ' ')[:10]
            prob = all_probs[idx] * 100
            text = f"{label}: {prob:.0f}%"
            draw.text((5, y_pos), text, font=font_small, fill=COLOR_WHITE)
            y_pos += 11
    
    display.image(image, rotation)


def display_happy_sound(sound_type, confidence):
    """Display laughing or babbling detection"""
    image = create_blank_image()
    draw = ImageDraw.Draw(image)
    
    bg_color = HAPPY_COLORS_RGB.get(sound_type, COLOR_WHITE)
    emoji = HAPPY_EMOJI.get(sound_type, ':)')
    
    draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=bg_color)
    
    try:
        font_emoji = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
        font_type = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_conf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_emoji = ImageFont.load_default()
        font_type = ImageFont.load_default()
        font_conf = ImageFont.load_default()
    
    draw_centered_text(draw, emoji, 5, font_emoji, COLOR_BLACK)
    
    sound_name = sound_type.upper()
    draw_centered_text(draw, sound_name, 65, font_type, COLOR_BLACK)
    
    conf_text = f"{confidence:.1f}%"
    draw_centered_text(draw, conf_text, 95, font_conf, COLOR_BLACK)
    
    draw_progress_bar(draw, 20, 115, 200, 12, confidence, COLOR_BLACK)
    
    display.image(image, rotation)

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
        # Note: These are approximate - you may need to adjust based on actual YAMNet class mapping
        self.baby_cry_indices = [20]     # "Baby cry, infant cry"
        self.laughter_indices = [14]  # "Laughter", "Baby laughter" 
        self.babbling_indices = [4]     # "Babbling"
        
        print("YAMNet ready!")
        print(f"  Crying: {[self.class_names[i] for i in self.baby_cry_indices if i < len(self.class_names)]}")
        print(f"  Laughing: {[self.class_names[i] for i in self.laughter_indices if i < len(self.class_names)]}")
        print(f"  Babbling: {[self.class_names[i] for i in self.babbling_indices if i < len(self.class_names)]}")
    
    def detect_baby_sound(self, audio, threshold=0.25):
        """
        Check if audio contains baby sounds (crying, laughing, or babbling)
        Returns: (sound_type, confidence)
        sound_type: 'crying', 'laughing', 'babbling', or None
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
        # if cry_score > threshold:
        #     if laugh_score > 0.5: # Laughing overrides crying
        #         return 'laughing', laugh_score * 100
        #     if babble_score > 0.5: # Babbling overrides crying
        #         return 'babbling', babble_score * 100
        #     return 'crying', cry_score * 100
        # elif laugh_score > 0.5:

        # # Find the highest score
        # max_score = max(cry_score, laugh_score, babble_score)
        
        # # Determine sound type if above threshold
        # if max_score > threshold:
        #     if max_score == cry_score:
        #         return 'crying', cry_score * 100
        #     elif max_score == laugh_score:
        #         return 'laughing', laugh_score * 100
        #     elif max_score == babble_score:
        #         return 'babbling', babble_score * 100
        
        return None, 0

# ============================================
# DEEPINFANT CRY CLASSIFIER (Stage 2)
# ============================================

class CryTypeClassifier:
    """Stage 2: Classify cry type using trained model"""
    def __init__(self, model_path='cry_model'):
        print("Loading cry type classifier...")
        self.model_path = Path(model_path)
        
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
        # Try new format first
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
    """
    Combined automatic baby monitor:
    1. Continuously listens
    2. YAMNet detects baby sounds (crying, laughing, babbling)
    3. If crying → classifier determines cry type
    4. If laughing/babbling → display directly
    5. Displays result
    """
    def __init__(self, 
                 model_path='cry_model',
                 sound_threshold=0.25,    # YAMNet baby sound threshold
                 classify_threshold=50,   # Classifier confidence threshold
                 recording_duration=3,
                 check_interval=1):       # How often to check (seconds)
        
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
        
        display_listening()
    
    def monitor(self):
        """Start automatic monitoring"""
        print("\n" + "="*60)
        print("AUTOMATIC BABY MONITOR - ALL SOUNDS")
        print("="*60)
        print("Detects: Crying, Laughing, Babbling")
        print("\nMonitoring started...")
        print("Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        try:
            while True:
                self.total_checks += 1
                
                # Show listening screen
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
                print(f"[Check #{self.total_checks}] Detected: {sound_type} ({confidence:.1f}%)" if sound_type else f"[Check #{self.total_checks}] No baby sounds detected")
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
                            print(f"  Probabilities:")
                            for i, label in enumerate(self.cry_classifier.labels):
                                if probs[i] * 100 > 5:  # Only show >5%
                                    print(f"     {label}: {probs[i]*100:.1f}%")
                            
                            # Display cry classification
                            display_cry_result(
                                cry_type,
                                type_confidence,
                                probs,
                                self.cry_classifier.labels
                            )
                            
                            time.sleep(5)  # Show result longer for cries
                        else:
                            print(f"  Crying detected but classification confidence low ({type_confidence:.1f}%)")
                            time.sleep(2)
                    
                    elif sound_type == 'laughing':
                        # LAUGHING detected - show directly
                        self.laugh_count += 1
                        
                        print(f"\n[{timestamp}] LAUGHING DETECTED! ({confidence:.1f}%)")
                        
                        # Display laughing
                        display_happy_sound('laughing', confidence)
                        
                        time.sleep(3)  # Show result
                    
                    elif sound_type == 'babbling':
                        # BABBLING detected - show directly
                        self.babble_count += 1
                        
                        print(f"\n[{timestamp}] BABBLING DETECTED! ({confidence:.1f}%)")
                        
                        # Display babbling
                        display_happy_sound('babbling', confidence)
                        
                        time.sleep(3)  # Show result
                
                else:
                    # No baby sounds - quiet check message every 10 checks
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
        
        # Final screen
        image = create_blank_image()
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=COLOR_BLACK)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        draw_centered_text(draw, "STOPPED", 20, font, COLOR_WHITE)
        draw_centered_text(draw, f"Cries: {self.cry_count}", 50, font_small, COLOR_WHITE)
        draw_centered_text(draw, f"Laughs: {self.laugh_count}", 65, font_small, COLOR_WHITE)
        draw_centered_text(draw, f"Babbles: {self.babble_count}", 80, font_small, COLOR_WHITE)
        
        # Show top cry type if any
        if self.cry_count > 0:
            top_cry = max(self.cry_type_counts.items(), key=lambda x: x[1])
            if top_cry[1] > 0:
                text = f"Top: {top_cry[0].replace('_', ' ')}"
                draw_centered_text(draw, text, 100, font_small, COLOR_WHITE)
        
        display.image(image, rotation)

# ============================================
# MAIN
# ============================================

def main():
    print("="*60)
    print("AUTOMATIC BABY MONITOR - ALL SOUNDS")
    print("="*60)
    print("Detects: Crying, Laughing, Babbling")
    print("  Crying: Classifies type (Hungry, Tired, etc.)")
    print("  Laughing/Babbling: Shows directly")
    print(f"\nDisplay: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT} Mini PiTFT")
    print("="*60)
    
    try:
        monitor = AutoBabyMonitor(
            model_path='./cry_model',      # Path to your trained cry classifier
            sound_threshold=0.25,           # YAMNet threshold for baby sounds (0.2-0.4)
            classify_threshold=50,          # Cry classifier threshold (50-70)
            recording_duration=4,           # Recording length per check
            check_interval=0                # Wait time between checks
        )
        
        monitor.monitor()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
        image = create_blank_image()
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=COLOR_ERROR)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        draw_centered_text(draw, "ERROR", 50, font, COLOR_WHITE)
        draw_centered_text(draw, str(e)[:20], 75, font, COLOR_WHITE)
        display.image(image, rotation)
        
        raise

if __name__ == '__main__':
    main()