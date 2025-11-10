"""
Baby Sound Monitor - YAMNet Version
Uses Google's pre-trained YAMNet model (AudioSet)
Detects: Crying, Laughing, Babbling, Ambient

This version is easier to set up - no model training needed!
"""

import time
import digitalio
import board
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from adafruit_rgb_display.rgb import color565
import adafruit_rgb_display.st7789 as st7789

try:
    import tensorflow as tf
    import tensorflow_hub as hub
except ImportError:
    raise ImportError("Install: pip3 install tensorflow==2.15.0 tensorflow-hub")

# ============================================
# DISPLAY CONFIGURATION
# ============================================

# SPI + Display Setup
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

buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input(pull=digitalio.Pull.UP)
buttonB.switch_to_input(pull=digitalio.Pull.UP)

DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 135
rotation = 90

# ============================================
# COLORS
# ============================================

COLOR_CRYING = (255, 0, 0)
COLOR_LAUGHING = (255, 200, 0)
COLOR_BABBLING = (0, 200, 255)
COLOR_AMBIENT = (100, 100, 100)
COLOR_LISTENING = (0, 255, 0)
COLOR_ANALYZING = (255, 255, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# ============================================
# DISPLAY FUNCTIONS (same as before)
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
    draw_centered_text(draw, "for baby sounds...", 75, font_small, COLOR_BLACK)
    
    display.image(image, rotation)

def display_analyzing():
    image = create_blank_image()
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=COLOR_ANALYZING)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw_centered_text(draw, "ANALYZING...", 55, font, COLOR_BLACK)
    display.image(image, rotation)

def display_detection_result(sound_type, confidence, class_name=None):
    image = create_blank_image()
    draw = ImageDraw.Draw(image)
    
    colors = {
        'crying': COLOR_CRYING,
        'laughing': COLOR_LAUGHING,
        'babbling': COLOR_BABBLING,
        'ambient': COLOR_AMBIENT
    }
    
    emojis = {
        'crying': ':-(',
        'laughing': ':-D',
        'babbling': ':-)',
        'ambient': '...'
    }
    
    bg_color = colors.get(sound_type, COLOR_AMBIENT)
    emoji = emojis.get(sound_type, '?')
    
    draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=bg_color)
    
    try:
        font_emoji = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
        font_type = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_conf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except:
        font_emoji = ImageFont.load_default()
        font_type = ImageFont.load_default()
        font_conf = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw_centered_text(draw, emoji, 5, font_emoji, COLOR_WHITE)
    
    sound_name = sound_type.upper()
    if sound_type == 'ambient':
        sound_name = "QUIET"
    
    draw_centered_text(draw, sound_name, 65, font_type, COLOR_WHITE)
    
    conf_text = f"{confidence:.1f}%"
    draw_centered_text(draw, conf_text, 93, font_conf, COLOR_WHITE)
    
    # Show actual YAMNet class if available
    if class_name and sound_type != 'ambient':
        class_text = f"({class_name[:15]})"
        draw_centered_text(draw, class_text, 108, font_small, COLOR_WHITE)
    
    bar_color = COLOR_WHITE if sound_type != 'ambient' else COLOR_BLACK
    draw_progress_bar(draw, 20, 120, 200, 10, confidence, bar_color)
    
    display.image(image, rotation)

# ============================================
# YAMNET DETECTOR
# ============================================

class YAMNetDetector:
    """
    Baby sound detector using Google's YAMNet
    Pre-trained on AudioSet with 521 sound classes
    """
    def __init__(self):
        """Initialize YAMNet"""
        print("Loading YAMNet model from TensorFlow Hub...")
        print("(This may take a minute on first run)")
        
        # Load YAMNet model
        self.model = hub.load('https://tfhub.dev/google/yamnet/1')
        
        # Load class names
        self.class_names = self._load_class_names()
        
        # Baby-related class indices in AudioSet/YAMNet
        self.baby_cry_indices = [20]    # "Baby cry, infant cry"
        self.babbling_indices = [4]     # "Babbling"
        self.laughter_indices = [14]  # "Laughter", "Baby laughter"
        
        print("YAMNet ready!")
        print(f"Monitoring classes:")
        print(f"  Crying: {[self.class_names[i] for i in self.baby_cry_indices]}")
        print(f"  Laughing: {[self.class_names[i] for i in self.laughter_indices]}")
        print(f"  Babbling: {[self.class_names[i] for i in self.babbling_indices]}")
    
    def _load_class_names(self):
        """Load YAMNet class names"""
        # Download class names CSV
        class_map_path = tf.keras.utils.get_file(
            'yamnet_class_map.csv',
            'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
        )
        
        class_names = []
        with open(class_map_path) as f:
            # Skip header
            next(f)
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    class_names.append(parts[2])  # Display name
        
        return class_names
    
    def detect(self, audio, sample_rate=16000):
        """
        Detect sound type using YAMNet
        Returns: (sound_type, confidence, class_name)
        """
        # YAMNet expects float32 audio
        audio = audio.astype(np.float32)
        
        # Run inference
        scores, embeddings, spectrogram = self.model(audio)
        
        # Scores is a 2D array [num_frames, num_classes]
        # Average over time frames
        mean_scores = np.mean(scores.numpy(), axis=0)
        
        # Get top class
        top_class_idx = np.argmax(mean_scores)
        confidence = mean_scores[top_class_idx] * 100
        class_name = self.class_names[top_class_idx]
        
        # Map to our categories
        if top_class_idx in self.baby_cry_indices:
            sound_type = 'crying'
        elif top_class_idx in self.laughter_indices:
            sound_type = 'laughing'
        elif top_class_idx in self.babbling_indices:
            sound_type = 'babbling'
        else:
            # Check if any baby-related class has high score
            baby_cry_score = np.max([mean_scores[i] for i in self.baby_cry_indices])
            laughter_score = np.max([mean_scores[i] for i in self.laughter_indices])
            babbling_score = np.max([mean_scores[i] for i in self.babbling_indices])
            
            max_baby_score = max(baby_cry_score, laughter_score, babbling_score)
            
            if baby_cry_score == max_baby_score and baby_cry_score > 0.1:
                sound_type = 'crying'
                confidence = baby_cry_score * 100
                class_name = self.class_names[self.baby_cry_indices[0]]
            elif laughter_score == max_baby_score and laughter_score > 0.1:
                sound_type = 'laughing'
                confidence = laughter_score * 100
                class_name = self.class_names[self.laughter_indices[0]]
            elif babbling_score == max_baby_score and babbling_score > 0.1:
                sound_type = 'babbling'
                confidence = babbling_score * 100
                class_name = self.class_names[self.babbling_indices[0]]
            else:
                sound_type = 'ambient'
        
        return sound_type, confidence, class_name

# ============================================
# BABY MONITOR
# ============================================

class BabyMonitor:
    """Baby monitor using YAMNet"""
    def __init__(self, detection_threshold=30, recording_duration=3):
        """Initialize monitor"""
        import sounddevice as sd
        self.sd = sd
        
        self.detector = YAMNetDetector()
        self.detection_threshold = detection_threshold
        self.sample_rate = 16000  # YAMNet uses 16kHz
        self.recording_duration = recording_duration
        
        self.cry_count = 0
        self.laugh_count = 0
        self.babble_count = 0
        self.total_detections = 0
        
        display_listening()
    
    def monitor(self):
        """Monitor baby sounds"""
        print("\n" + "="*60)
        print("BABY SOUND MONITOR - YAMNet Version")
        print("="*60)
        print("Using Google's pre-trained AudioSet model")
        print("\nDetects: Crying, Laughing, Babbling, Ambient")
        print("\nControls:")
        print("  Button A: Analyze audio")
        print("  Button B: Toggle backlight")
        print("  Ctrl+C: Stop monitoring")
        print("="*60 + "\n")
        
        try:
            while True:
                display_listening()
                
                # Button B for backlight
                if buttonB.value == False:
                    backlight.value = not backlight.value
                    time.sleep(0.3)
                
                # Wait for Button A
                while buttonA.value == True:
                    time.sleep(0.1)
                
                display_analyzing()
                print("\n[Recording audio...]")
                
                # Record audio
                audio = self.sd.rec(
                    int(self.recording_duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32'
                )
                self.sd.wait()
                audio = audio.flatten()
                
                # Detect
                print("[Analyzing with YAMNet...]")
                sound_type, confidence, class_name = self.detector.detect(audio, self.sample_rate)
                
                timestamp = time.strftime('%H:%M:%S')
                
                # Update statistics
                self.total_detections += 1
                if sound_type == 'crying' and confidence >= self.detection_threshold:
                    self.cry_count += 1
                    print(f"[{timestamp}] CRYING! #{self.cry_count} ({confidence:.1f}%)")
                    print(f"  YAMNet class: {class_name}")
                elif sound_type == 'laughing' and confidence >= self.detection_threshold:
                    self.laugh_count += 1
                    print(f"[{timestamp}] LAUGHING! #{self.laugh_count} ({confidence:.1f}%)")
                    print(f"  YAMNet class: {class_name}")
                elif sound_type == 'babbling' and confidence >= self.detection_threshold:
                    self.babble_count += 1
                    print(f"[{timestamp}] BABBLING! #{self.babble_count} ({confidence:.1f}%)")
                    print(f"  YAMNet class: {class_name}")
                else:
                    print(f"[{timestamp}] Ambient ({confidence:.1f}%)")
                    print(f"  Detected: {class_name}")
                
                # Display result
                display_detection_result(sound_type, confidence, class_name)
                
                # Show duration
                if sound_type == 'crying':
                    time.sleep(5)
                elif sound_type in ['laughing', 'babbling']:
                    time.sleep(3)
                else:
                    time.sleep(1.5)
                
                # Wait for button release
                while buttonA.value == False:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n" + "="*60)
            print("MONITORING STOPPED")
            print("="*60)
            print(f"Total detections: {self.total_detections}")
            print(f"  Cries: {self.cry_count}")
            print(f"  Laughs: {self.laugh_count}")
            print(f"  Babbles: {self.babble_count}")
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
            
            draw_centered_text(draw, "STOPPED", 25, font, COLOR_WHITE)
            draw_centered_text(draw, f"Total: {self.total_detections}", 55, font_small, COLOR_WHITE)
            draw_centered_text(draw, f"Cries: {self.cry_count}", 75, font_small, COLOR_WHITE)
            draw_centered_text(draw, f"Laughs: {self.laugh_count}", 90, font_small, COLOR_WHITE)
            draw_centered_text(draw, f"Babbles: {self.babble_count}", 105, font_small, COLOR_WHITE)
            
            display.image(image, rotation)

# ============================================
# MAIN
# ============================================

def main():
    print("="*60)
    print("BABY SOUND MONITOR - YAMNet Version")
    print("="*60)
    print("Uses Google's pre-trained AudioSet model")
    print("No training required!")
    print("="*60)
    
    try:
        monitor = BabyMonitor(
            detection_threshold=30,  # Lower threshold for YAMNet
            recording_duration=3
        )
        
        monitor.monitor()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()