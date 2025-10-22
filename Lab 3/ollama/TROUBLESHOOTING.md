# Ollama Troubleshooting Guide

## Audio Issues

### Bluetooth Speaker Not Working

If you're not hearing audio through your Bluetooth speaker, try these steps:

#### 1. Check Bluetooth Connection
```bash
bluetoothctl
# In bluetoothctl:
# devices (to list paired devices)
# connect <MAC_ADDRESS>
# exit
```

#### 2. Set Bluetooth as Default Audio Output
```bash
# List audio outputs
pactl list short sinks

# Set Bluetooth speaker as default (replace with your sink number/name)
pactl set-default-sink <sink_name_or_number>

# Test audio
speaker-test -t wav -c 2
```

#### 3. Route espeak to Bluetooth
```bash
# Test with espeak
espeak "Testing Bluetooth speaker"

# If that doesn't work, try with explicit ALSA device
espeak --stdout "Testing" | aplay -D bluealsa
```

#### 4. Check Volume Levels
```bash
alsamixer
# Use arrow keys to navigate and adjust volume
# Press 'M' to unmute if needed
```

### Microphone Not Working

```bash
# Test microphone
arecord -d 5 test.wav
aplay test.wav

# List recording devices
arecord -l
```

## Ollama Issues

### Script Won't Start

- Make sure you activated the virtual environment: `source ollama_venv/bin/activate`
- Check that Ollama is running: `curl http://localhost:11434/api/tags`
- Verify the model is downloaded: `ollama list`

### Timeout Errors

If you get timeout errors with Ollama:

1. **Use a smaller/faster model:**
```bash
ollama pull qwen2.5:0.5b-instruct
# or even lighter:
ollama pull qwen2.5:0.5b-instruct-q4_0
```

2. **Make sure streaming is enabled** in your code (see the updated `ollama_demo.py` for examples)

3. **Increase timeout values** in the code if needed (already set to 300 seconds in updated scripts)

### Model Not Found

```bash
# Check available models
ollama list

# Pull the recommended model
ollama pull qwen2.5:0.5b-instruct
```

### Ollama Not Running

```bash
# Start Ollama service
ollama serve

# Or check if it's already running
curl http://localhost:11434/api/tags
```

## Python Environment Issues

### Module Not Found Errors

Make sure you're in the correct virtual environment:

```bash
cd ~/Interactive-Lab-Hub-upstream/Lab\ 3/ollama
source ollama_venv/bin/activate
pip install -r ollama_requirements.txt
```

### PyAudio Installation Issues

If PyAudio fails to install:

```bash
# Install system dependencies first
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-dev

# Then retry pip install
pip install pyaudio
```

## Performance Tips

1. **Use the lightest model** for faster responses: `qwen2.5:0.5b-instruct-q4_0`
2. **Enable streaming** to see responses as they're generated
3. **Keep prompts concise** for faster processing
4. **Close other applications** to free up RAM/CPU
