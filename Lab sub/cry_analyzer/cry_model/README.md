# Baby Cry Analyzer Model

## Files Included
- model_weights.weights.h5 - Model weights only ⭐ MOST COMPATIBLE
- cry_model.keras - Native Keras format (TF 2.16+)
- cry_model.h5 - Legacy Keras format
- saved_model/ - TensorFlow SavedModel export
- model_architecture.json - Model structure
- config.json - Configuration
- label_mapping.json - Class labels

## Raspberry Pi Usage

### Method 1: Using Weights (Recommended)
The emergency script will:
1. Rebuild model architecture on Pi
2. Load model_weights.weights.h5 (or model_weights.h5)
3. Works with ANY TensorFlow version!

```bash
python3 cry_emergency.py test_audio.wav
python3 cry_emergency.py --realtime
```

### Method 2: Direct Model Loading (if compatible)
```bash
python3 cry_analyzer.py test_audio.wav
```

## Format Compatibility

| File | Compatibility | Use Case |
|------|--------------|----------|
| model_weights.weights.h5 | ✅✅✅ Best | Use with cry_emergency.py |
| cry_model.keras | ✅✅ TF 2.16+ | Direct loading |
| cry_model.h5 | ⚠️ May fail | Legacy systems |
| saved_model/ | ✅ Good | TFLite conversion |

## If You Get Errors

Use cry_emergency.py - it rebuilds the model and loads weights only,
avoiding ALL format compatibility issues!
