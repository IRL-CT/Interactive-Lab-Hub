"""
Baby Cry Analyzer - Mini PiTFT Display (ST7789)
Shows cry type and confidence on 240x135 pixel color display
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
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization
except ImportError:
    raise ImportError("Install: pip3 install tensorflow==2.15.0")

# ============================================
# DISPLAY CONFIGURATION
# ============================================

# SPI + Display Setup
cs_pin = digitalio.DigitalInOut(board.D5)      # GPIO5  (PIN 29)
dc_pin = digitalio.DigitalInOut(board.D25)     # GPIO25 (PIN 22)
reset_pin = None
BAUDRATE = 64000000

spi = board.SPI()

# Mini PiTFT 1.14" (240x135) ST7789
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

# Backlight
backlight = digitalio.DigitalInOut(board.D22)  # GPIO22 (PIN 15)
backlight.switch_to_output(value=True)

# Buttons
buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# Display dimensions (240 width x 135 height in landscape)
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 135

rotation = 90

# ============================================
# COLOR DEFINITIONS
# ============================================

# RGB colors for each cry type
CRY_COLORS_RGB = {
    'belly_pain': (255, 0, 0),      # RED
    'hungry': (255, 200, 0),        # YELLOW
    'tired': (0, 150, 255),         # BLUE
    'burping': (255, 140, 0),       # ORANGE
    'discomfort': (200, 0, 255),    # PURPLE
}

# Status colors
COLOR_LISTENING = (0, 255, 0)       # GREEN
COLOR_ANALYZING = (255, 255, 0)     # YELLOW
COLOR_ERROR = (255, 0, 0)           # RED
COLOR_WHITE = (255, 255, 255)       # WHITE
COLOR_BLACK = (0, 0, 0)             # BLACK

# Emoji for each cry type
CRY_EMOJI = {
    'belly_pain': '!',
    'hungry': 'H',
    'tired': 'Z',
    'burping': 'B',
    'discomfort': 'D',
}


# ============================================
# DISPLAY FUNCTIONS
# ============================================

def create_blank_image():
    """Create blank image for drawing"""
    return Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), COLOR_BLACK)


def draw_centered_text(draw, text, y_position, font, color=COLOR_WHITE):
    """Draw centered text"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (DISPLAY_WIDTH - text_width) // 2
    draw.text((x, y_position), text, font=font, fill=color)


def draw_progress_bar(draw, x, y, width, height, percentage, color):
    """Draw a progress bar"""
    # Background
    draw.rectangle([x, y, x + width, y + height], outline=COLOR_WHITE, fill=COLOR_BLACK)
    
    # Fill
    fill_width = int(width * (percentage / 100))
    if fill_width > 0:
        draw.rectangle([x, y, x + fill_width, y + height], fill=color)
    
    # Percentage text
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
    """Show 'Listening...' screen"""
    image = create_blank_image()
    draw = ImageDraw.Draw(image)
    
    # Background color
    draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=COLOR_LISTENING)
    
    # Text
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw_centered_text(draw, "LISTENING", 40, font_large, COLOR_BLACK)
    draw_centered_text(draw, "for baby cries...", 75, font_small, COLOR_BLACK)
    
    display.image(image, rotation)


def display_analyzing():
    """Show 'Analyzing...' screen"""
    image = create_blank_image()
    draw = ImageDraw.Draw(image)
    
    # Background
    draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=COLOR_ANALYZING)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw_centered_text(draw, "ANALYZING...", 55, font, COLOR_BLACK)
    
    display.image(image, rotation)


def display_cry_result(cry_type, confidence, all_probs=None, labels=None):
    """Display cry detection result"""
    image = create_blank_image()
    draw = ImageDraw.Draw(image)
    
    # Get color for this cry type
    bg_color = CRY_COLORS_RGB.get(cry_type, COLOR_WHITE)
    emoji = CRY_EMOJI.get(cry_type, '?')
    
    # Background (fill with cry type color)
    draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=bg_color)
    
    # Fonts
    try:
        font_emoji = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        font_type = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_conf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except:
        font_emoji = ImageFont.load_default()
        font_type = ImageFont.load_default()
        font_conf = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Emoji/Icon at top
    draw_centered_text(draw, emoji, 5, font_emoji, COLOR_WHITE)
    
    # Cry type name
    cry_name = cry_type.replace('_', ' ').upper()
    draw_centered_text(draw, cry_name, 50, font_type, COLOR_WHITE)
    
    # Confidence percentage
    conf_text = f"{confidence:.1f}%"
    draw_centered_text(draw, conf_text, 78, font_conf, COLOR_WHITE)
    
    # Progress bar
    draw_progress_bar(draw, 20, 100, 200, 15, confidence, COLOR_WHITE)
    
    # Show top 2 other probabilities (small text at bottom)
    if all_probs is not None and labels is not None:
        sorted_indices = np.argsort(all_probs)[::-1]
        y_pos = 120
        for i, idx in enumerate(sorted_indices[1:3]):  # Show 2nd and 3rd
            label = labels[idx].replace('_', ' ')[:8]  # Truncate
            prob = all_probs[idx] * 100
            text = f"{label}: {prob:.0f}%"
            draw.text((5, y_pos), text, font=font_small, fill=COLOR_WHITE)
            y_pos += 10
    
    display.image(image, rotation)


def display_error(message):
    """Display error message"""
    image = create_blank_image()
    draw = ImageDraw.Draw(image)
    
    draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=COLOR_ERROR)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    draw_centered_text(draw, "ERROR", 50, font, COLOR_WHITE)
    draw_centered_text(draw, message[:20], 75, font, COLOR_WHITE)
    
    display.image(image, rotation)


# ============================================
# CRY ANALYZER (from your existing code)
# ============================================

class SimpleCryAnalyzer:
    def __init__(self, model_path='cry_model'):
        """Initialize analyzer"""
        self.model_path = Path(model_path)
        
        # Load configuration
        print("Loading configuration...")
        with open(self.model_path / 'config.json', 'r') as f:
            self.config = json.load(f)
        
        self.sample_rate = self.config.get('sample_rate', 16000)
        self.n_mfcc = self.config.get('n_mfcc', 40)
        
        # Load labels
        with open(self.model_path / 'label_mapping.json', 'r') as f:
            label_map = json.load(f)
            self.labels = [label_map[str(i)] for i in range(len(label_map))]
        
        print(f"Classes: {self.labels}")
        
        # Build model
        print("Building model...")
        self.model = self._build_model_architecture()
        
        # Load weights
        print("Loading weights...")
        self._load_weights()
        
        print("Model Ready!")
    
    def _build_model_architecture(self):
        """Build model architecture"""
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
        """Load weights from file"""
        weights_loaded = False
        
        # Try new format
        weights_path_new = self.model_path / 'model_weights.weights.h5'
        if weights_path_new.exists():
            try:
                self.model.load_weights(str(weights_path_new), skip_mismatch=True)
                print("Loaded weights successfully!")
                weights_loaded = True
            except Exception as e:
                print(f"Failed: {e}")
        
        # Try old format
        if not weights_loaded:
            weights_path = self.model_path / 'model_weights.h5'
            if weights_path.exists():
                try:
                    self.model.load_weights(str(weights_path), skip_mismatch=True)
                    print("Loaded weights successfully!")
                    weights_loaded = True
                except Exception as e:
                    print(f"Failed: {e}")
        
        if not weights_loaded:
            raise ValueError("Could not load model weights!")
    
    def extract_features(self, audio):
        """Extract MFCC features"""
        try:
            mfcc = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=self.n_mfcc)
            mfcc_scaled = np.mean(mfcc.T, axis=0)
            return mfcc_scaled
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None
    
    def predict(self, audio):
        """Predict cry type"""
        features = self.extract_features(audio)
        if features is None:
            return None, 0, None
        
        features = features / np.max(np.abs(features))
        features = features.reshape(1, 40, 1).astype(np.float32)
        
        output = self.model.predict(features, verbose=0)
        probabilities = output[0]
        print(f"Probabilities: {probabilities}")
        
        predicted_idx = np.argmax(probabilities)
        confidence = probabilities[predicted_idx] * 100
        predicted_label = self.labels[predicted_idx]
        
        return predicted_label, confidence, probabilities


# ============================================
# REALTIME MONITOR WITH DISPLAY
# ============================================

class CryMonitorWithDisplay:
    def __init__(self, model_path='cry_model', threshold=60, recording_duration=3):
        """Initialize monitor with display"""
        import sounddevice as sd
        self.sd = sd
        
        self.analyzer = SimpleCryAnalyzer(model_path)
        self.threshold = threshold
        self.sample_rate = self.analyzer.sample_rate
        self.recording_duration = recording_duration
        
        self.cry_count = 0
        self.last_cry_time = None
        
        # Show initial listening screen
        display_listening()
    
    def detect_cry_level(self, audio):
        """Detect if crying"""
        rms = np.sqrt(np.mean(audio**2))
        return rms > 0.02
    
    def monitor(self):
        """Monitor with display updates"""
        print("\nMonitoring started...")
        print("Button A: Force analyze current audio")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Show listening screen
                display_listening()
                
                # Wait for Button A press
                while buttonA.value == True:  # Button is NOT pressed (pull-up = True when released)
                    time.sleep(0.1)
                
                # Button A pressed! Show analyzing and start recording
                display_analyzing()
                print("Button A pressed - Recording...")
                
                # Record audio
                audio = self.sd.rec(
                    int(self.recording_duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32'
                )
                self.sd.wait()
                audio = audio.flatten()
                
                print("Analyzing...")
                
                # Predict
                label, confidence, probs = self.analyzer.predict(audio)
                
                if label:
                    self.cry_count += 1
                    self.last_cry_time = time.strftime('%H:%M:%S')
                    
                    # Display result
                    display_cry_result(
                        label,
                        confidence,
                        probs,
                        self.analyzer.labels
                    )
                    
                    print(f"[{self.last_cry_time}] Cry #{self.cry_count}: {label.upper()} ({confidence:.1f}%)")
                    
                    # Show result for 3 seconds
                    time.sleep(5)
                else:
                    print(f"Analysis failed")
                    time.sleep(1)
                
                # Wait for button release before next cycle
                while buttonA.value == False:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print(f"\n\nMonitoring stopped.")
            print(f"Total cries detected: {self.cry_count}")
            
            # Show final screen
            image = create_blank_image()
            draw = ImageDraw.Draw(image)
            draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=COLOR_BLACK)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            except:
                font = ImageFont.load_default()
            
            draw_centered_text(draw, "STOPPED", 50, font, COLOR_WHITE)
            draw_centered_text(draw, f"Cries: {self.cry_count}", 75, font, COLOR_WHITE)
            
            display.image(image, rotation)


# ============================================
# MAIN
# ============================================

def main():
    import sys
    
    model_path = './cry_model'
    
    print("="*60)
    print("Baby Cry Analyzer - Mini PiTFT Display")
    print("="*60)
    print(f"\nDisplay: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
    print("Controls:")
    print("  Button A: Toggle backlight")
    print("  Button B: Force analyze current audio")
    print("  Ctrl+C: Stop monitoring")
    print("="*60)
    
    try:
        # Initialize and start monitoring
        monitor = CryMonitorWithDisplay(
            model_path=model_path,
            threshold=60,  # 60% confidence threshold
            recording_duration=7
        )
        
        monitor.monitor()
        
    except Exception as e:
        print(f"\nError: {e}")
        display_error(str(e)[:20])
        raise


if __name__ == '__main__':
    main()