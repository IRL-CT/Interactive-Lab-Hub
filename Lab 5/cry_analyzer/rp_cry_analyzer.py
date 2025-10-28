"""
Baby Cry Analyzer - Emergency Workaround
Rebuilds model from scratch, loads weights only (avoids .h5 compatibility issues)
"""

import numpy as np
import librosa
import json
from pathlib import Path
import time
import h5py

try:
    import tensorflow as tf
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout
    print(f"Using TensorFlow {tf.__version__}")
except ImportError:
    raise ImportError("Please install: pip3 install tensorflow==2.15.0")

class SimpleCryAnalyzer:
    def __init__(self, model_path='cry_model'):
        """Initialize by rebuilding model architecture"""
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
        
        # Build model architecture from scratch
        print("Building model architecture...")
        self.model = self._build_model_architecture()
        
        # Load weights (avoids .h5 format compatibility issues)
        print("Loading model weights...")
        weights_loaded = False
        
        # Try 1: Load from model_weights.weights.h5 (new API)
        weights_path_new = self.model_path / 'model_weights.weights.h5'
        if weights_path_new.exists():
            try:
                print(f"Loading weights from {weights_path_new}...")
                self.model.load_weights(str(weights_path_new))
                print("Loaded weights successfully!")
                weights_loaded = True
            except Exception as e:
                print(f"Failed to load model_weights.weights.h5: {e}")
        
        # Try 2: Load from model_weights.h5 (old API)
        if not weights_loaded:
            weights_path = self.model_path / 'model_weights.h5'
            if weights_path.exists():
                try:
                    print(f"Loading weights from {weights_path}...")
                    self.model.load_weights(str(weights_path))
                    print("✓ Loaded weights successfully!")
                    weights_loaded = True
                except Exception as e:
                    print(f"Failed to load model_weights.h5: {e}")
        
        # Try 2: Extract weights from cry_model.h5 manually
        if not weights_loaded:
            h5_path = self.model_path / 'cry_model.h5'
            if h5_path.exists():
                try:
                    print(f"Extracting weights from {h5_path}...")
                    self._extract_and_load_weights(h5_path)
                    print("Extracted weights successfully!")
                    weights_loaded = True
                except Exception as e:
                    print(f"Failed to extract from cry_model.h5: {e}")
        
        if not weights_loaded:
            raise ValueError(
                "Could not load model weights!\n"
                "Please re-save your model in Colab using the updated save script.\n"
                "The model needs either:\n"
                "  - model_weights.weights.h5 (TF 2.16+, preferred)\n"
                "  - model_weights.h5 (TF 2.15 and earlier)\n"
                "  - cry_model.h5 (can extract weights)\n"
                "  - cry_model.keras (TF 2.16+)\n"
            )
        
        print(f"\n{'='*50}")
        print("Model Ready!")
        print(f"Input shape: (40, 1)")
        print(f"Output classes: {len(self.labels)}")
        print(f"{'='*50}\n")
    
    def _build_model_architecture(self):
        """
        Rebuild the exact model architecture used in training
        This must match your Colab training code!
        """
        model = Sequential([
            Conv1D(filters=32, kernel_size=3, activation='relu', input_shape=(40, 1)),
            MaxPooling1D(pool_size=2),
            
            Conv1D(filters=64, kernel_size=3, activation='relu'),
            MaxPooling1D(pool_size=2),
            
            Flatten(),
            Dense(64, activation='relu'),
            Dropout(0.3),
            Dense(len(self.labels), activation='softmax')
        ])
        
        # Compile (needed for some operations)
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _extract_and_load_weights(self, h5_path):
        """
        Manually extract weights from .h5 file
        This bypasses the format compatibility issues
        """
        import h5py
        
        # Open the h5 file
        with h5py.File(h5_path, 'r') as f:
            # Try different weight locations in the file
            weight_keys = []
            
            # Check if weights are in model_weights group
            if 'model_weights' in f.keys():
                weights_group = f['model_weights']
            else:
                weights_group = f
            
            # Extract layer names
            layer_names = []
            def find_layers(name, obj):
                if isinstance(obj, h5py.Group):
                    layer_names.append(name)
            
            weights_group.visititems(find_layers)
            
            # Load weights for each layer
            weights_list = []
            for layer in self.model.layers:
                layer_weights = []
                layer_name = layer.name
                
                # Find matching weights in h5 file
                for h5_layer_name in layer_names:
                    if layer_name in h5_layer_name or h5_layer_name.endswith(layer_name):
                        try:
                            layer_group = weights_group[h5_layer_name]
                            if hasattr(layer_group, 'keys'):
                                for weight_name in layer_group.keys():
                                    weight_data = layer_group[weight_name][()]
                                    layer_weights.append(weight_data)
                        except:
                            pass
                
                if layer_weights:
                    try:
                        layer.set_weights(layer_weights)
                        print(f"  ✓ Loaded {layer_name}")
                    except Exception as e:
                        print(f"  ✗ Failed {layer_name}: {e}")
    
    def extract_simple_features(self, audio):
        """Extract averaged MFCC features"""
        try:
            mfcc = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=self.n_mfcc)
            mfcc_scaled = np.mean(mfcc.T, axis=0)
            return mfcc_scaled
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None
    
    def predict(self, audio):
        """Predict cry type"""
        features = self.extract_simple_features(audio)
        if features is None:
            return None, 0, None
        
        # Normalize
        features = features / np.max(np.abs(features))
        
        # Reshape
        features = features.reshape(1, 40, 1).astype(np.float32)
        
        # Predict
        output = self.model.predict(features, verbose=0)
        probabilities = output[0]
        
        predicted_idx = np.argmax(probabilities)
        confidence = probabilities[predicted_idx]
        predicted_label = self.labels[predicted_idx]
        
        return predicted_label, confidence, probabilities
    
    def predict_from_file(self, audio_file):
        """Predict from file"""
        audio, sr = librosa.load(audio_file, sr=self.sample_rate)
        return self.predict(audio)
    
    def analyze_and_display(self, audio_file):
        """Analyze and display results"""
        label, confidence, probs = self.predict_from_file(audio_file)
        
        if label is None:
            print("Error: Could not analyze audio")
            return None, None
        
        print(f"\n{'='*50}")
        print(f"Predicted Cry Type: {label.upper()}")
        print(f"Confidence: {confidence*100:.2f}%")
        print(f"{'='*50}")
        print("\nAll Probabilities:")
        for class_name, prob in zip(self.labels, probs):
            # bar = '█' * int(prob * 50)
            print(f"{class_name:15s} [{prob*100:5.1f}%]")
        print(f"{'='*50}\n")
        
        return label, confidence


class RealtimeCryDetector:
    def __init__(self, model_path='cry_model', threshold=0.6, recording_duration=3):
        """Real-time detection"""
        import sounddevice as sd
        self.sd = sd
        self.analyzer = SimpleCryAnalyzer(model_path)
        self.threshold = threshold
        self.sample_rate = self.analyzer.sample_rate
        self.recording_duration = recording_duration
    
    def detect_cry_level(self, audio):
        """Detect crying"""
        rms = np.sqrt(np.mean(audio**2))
        return rms > 0.02
    
    def monitor(self, callback=None):
        """Monitor microphone"""
        print("\nStarting real-time monitoring...")
        print("Listening for baby cries...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                audio = self.sd.rec(
                    int(self.recording_duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32'
                )
                self.sd.wait()
                audio = audio.flatten()
                
                if self.detect_cry_level(audio):
                    print("Cry detected! Analyzing...")
                    label, confidence, probs = self.analyzer.predict(audio)
                    
                    if label and confidence > self.threshold:
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                        print(f"[{timestamp}] Baby crying: {label.upper()} ({confidence*100:.1f}%)")
                        
                        if callback:
                            callback(label, confidence, timestamp)
                else:
                    print(".", end="", flush=True)
                
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")


def main():
    import sys
    
    model_path = './cry_model'
    
    if len(sys.argv) < 2:
        print("Baby Cry Analyzer - Emergency Workaround")
        print("\nUsage:")
        print("  python3 cry_emergency.py <audio_file>")
        print("  python3 cry_emergency.py --realtime")
        print("  python3 cry_emergency.py --test <folder>")
        return
    
    if sys.argv[1] == '--realtime':
        detector = RealtimeCryDetector(model_path=model_path)
        detector.monitor()
    elif sys.argv[1] == '--test' and len(sys.argv) > 2:
        analyzer = SimpleCryAnalyzer(model_path=model_path)
        test_folder = Path(sys.argv[2])
        for audio_file in test_folder.glob('*.wav'):
            print(f"\nAnalyzing: {audio_file.name}")
            analyzer.analyze_and_display(audio_file)
    else:
        analyzer = SimpleCryAnalyzer(model_path=model_path)
        analyzer.analyze_and_display(sys.argv[1])


if __name__ == '__main__':
    main()