"""
Baby Cry Analyzer - Raspberry Pi Inference (SIMPLIFIED VERSION)
Compatible with the averaged MFCC approach
"""

import numpy as np
import librosa
import json
import sounddevice as sd
from pathlib import Path
import time

# Try to import TFLite (handles both runtime and full TensorFlow)
try:
    import tflite_runtime.interpreter as tflite
    print("Using TFLite Runtime")
except ImportError:
    try:
        import tensorflow as tf
        tflite = tf.lite
        print("Using TensorFlow Lite (from full TensorFlow)")
    except ImportError:
        raise ImportError("Please install tensorflow or tflite-runtime")

class SimpleCryAnalyzer:
    def __init__(self, model_path='cry_model'):
        """
        Initialize the cry analyzer with simplified features
        """
        self.model_path = Path(model_path)
        
        # Load configuration
        with open(self.model_path / 'config.json', 'r') as f:
            self.config = json.load(f)
        
        # Get parameters (use defaults if not in config)
        self.sample_rate = self.config.get('sample_rate', 16000)
        self.n_mfcc = self.config.get('n_mfcc', 40)
        
        # Load label mapping
        with open(self.model_path / 'label_mapping.json', 'r') as f:
            label_map = json.load(f)
            self.labels = [label_map[str(i)] for i in range(len(label_map))]
        
        # Load TFLite model (works with both runtime and full TF)
        self.interpreter = tflite.Interpreter(
            model_path=str(self.model_path / 'cry_model.tflite')
        )
        self.interpreter.allocate_tensors()
        
        # Get input and output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        print("Simple Cry Analyzer initialized!")
        print(f"Classes: {self.labels}")
        print(f"Feature extraction: Averaged MFCC ({self.n_mfcc} coefficients)")
    
    def extract_simple_features(self, audio):
        """
        Extract SIMPLE averaged MFCC features (matches training)
        """
        try:
            # Extract MFCCs
            mfcc = librosa.feature.mfcc(
                y=audio, 
                sr=self.sample_rate, 
                n_mfcc=self.n_mfcc
            )
            
            # Average over time dimension → shape (40,)
            mfcc_scaled = np.mean(mfcc.T, axis=0)
            
            return mfcc_scaled
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None
    
    def predict(self, audio):
        """
        Predict cry type from audio
        """
        # Extract simple features
        features = self.extract_simple_features(audio)
        
        if features is None:
            return None, 0, None
        
        # Normalize (max absolute value - matches training)
        features = features / np.max(np.abs(features))
        
        # Reshape for model input: (1, 40, 1)
        features = features.reshape(1, 40, 1).astype(np.float32)
        
        # Run inference
        self.interpreter.set_tensor(self.input_details[0]['index'], features)
        self.interpreter.invoke()
        
        # Get prediction
        output = self.interpreter.get_tensor(self.output_details[0]['index'])
        probabilities = output[0]
        
        # Get predicted class and confidence
        predicted_idx = np.argmax(probabilities)
        confidence = probabilities[predicted_idx]
        predicted_label = self.labels[predicted_idx]
        
        return predicted_label, confidence, probabilities
    
    def predict_from_file(self, audio_file):
        """
        Predict cry type from audio file
        """
        # Load audio
        audio, sr = librosa.load(audio_file, sr=self.sample_rate)
        
        # Predict
        label, confidence, probs = self.predict(audio)
        
        return label, confidence, probs
    
    def analyze_and_display(self, audio_file):
        """
        Analyze audio file and display results
        """
        label, confidence, probs = self.predict_from_file(audio_file)
        
        if label is None:
            print("Error: Could not analyze audio")
            return None, None
        
        print(f"\n{'='*50}")
        print(f"Predicted Cry Type: {label.upper()}")
        print(f"Confidence: {confidence*100:.2f}%")
        print(f"{'='*50}")
        print("\nAll Probabilities:")
        for i, (class_name, prob) in enumerate(zip(self.labels, probs)):
            bar = '█' * int(prob * 50)
            print(f"{class_name:15s} [{prob*100:5.1f}%] {bar}")
        print(f"{'='*50}\n")
        
        return label, confidence


class RealtimeCryDetector:
    def __init__(self, model_path='cry_model', threshold=0.6, recording_duration=3):
        """
        Real-time cry detection using microphone
        """
        self.analyzer = SimpleCryAnalyzer(model_path)
        self.threshold = threshold
        self.sample_rate = self.analyzer.sample_rate
        self.recording_duration = recording_duration
        
    def detect_cry_level(self, audio):
        """
        Simple cry detection based on volume
        """
        rms = np.sqrt(np.mean(audio**2))
        return rms > 0.02  # Adjust threshold as needed
    
    def monitor(self, callback=None):
        """
        Monitor microphone for crying sounds
        """
        print("Starting real-time cry monitoring...")
        print("Listening for baby cries...")
        print(f"Recording duration: {self.recording_duration}s")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Record audio chunk
                audio = sd.rec(
                    int(self.recording_duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32'
                )
                sd.wait()
                audio = audio.flatten()
                
                # Check if crying detected
                if self.detect_cry_level(audio):
                    print("Cry detected! Analyzing...")
                    
                    # Predict cry type
                    label, confidence, probs = self.analyzer.predict(audio)
                    
                    if label and confidence > self.threshold:
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                        print(f"[{timestamp}] Baby is crying: {label.upper()} ({confidence*100:.1f}%)")
                        
                        if callback:
                            callback(label, confidence, timestamp)
                    else:
                        print("Low confidence, continuing to monitor...")
                else:
                    print(".", end="", flush=True)
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")


def main():
    """
    Main function with usage examples
    """
    import sys
    
    model_path = './cry_model'
    
    if len(sys.argv) < 2:
        print("Baby Cry Analyzer - Raspberry Pi (Simplified Version)")
        print("\nUsage:")
        print("  python raspberry_pi_inference_simple.py <audio_file>    - Analyze single file")
        print("  python raspberry_pi_inference_simple.py --realtime      - Real-time monitoring")
        print("  python raspberry_pi_inference_simple.py --test <folder> - Test on folder")
        print("\nExamples:")
        print("  python raspberry_pi_inference_simple.py baby_cry.wav")
        print("  python raspberry_pi_inference_simple.py --realtime")
        return
    
    if sys.argv[1] == '--realtime':
        # Real-time monitoring
        detector = RealtimeCryDetector(model_path=model_path)
        detector.monitor()
        
    elif sys.argv[1] == '--test' and len(sys.argv) > 2:
        # Test on folder
        analyzer = SimpleCryAnalyzer(model_path=model_path)
        test_folder = Path(sys.argv[2])
        
        for audio_file in test_folder.glob('*.wav'):
            print(f"\nAnalyzing: {audio_file.name}")
            analyzer.analyze_and_display(audio_file)
            
    else:
        # Single file analysis
        analyzer = SimpleCryAnalyzer(model_path=model_path)
        audio_file = sys.argv[1]
        analyzer.analyze_and_display(audio_file)


if __name__ == '__main__':
    main()