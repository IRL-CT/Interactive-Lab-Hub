# Ollama Integration Examples

This folder contains example scripts demonstrating how to integrate Ollama AI models with your Raspberry Pi projects.

## Available Scripts

### 1. ollama_demo.py ✅ (Recommended)

**Status:** Working and tested

Basic demo that shows how to interact with Ollama:
- Text chat interface
- Voice output option (text-to-speech)
- Simple query testing

**Usage:**
```bash
source ollama_venv/bin/activate
python3 ollama_demo.py
```

### 2. ollama_voice_assistant.py 🚧 (Experimental)

**Status:** Updated but requires additional testing

Full voice assistant with:
- Speech recognition (microphone input)
- Ollama AI processing
- Text-to-speech output

**Requirements:**
- Working microphone
- Internet connection (for Google Speech Recognition)
- espeak for audio output

**Usage:**
```bash
source ollama_venv/bin/activate
python3 ollama_voice_assistant.py
```

**Known Issues:**
- May require additional audio configuration
- Microphone permissions needed

### 3. ollama_web_app.py 🚧 (Experimental)

**Status:** Updated but requires additional testing

Web-based chat interface with:
- Browser-based UI
- WebSocket support for real-time chat
- Optional voice features

**Usage:**
```bash
source ollama_venv/bin/activate
python3 ollama_web_app.py
# Open browser to http://localhost:5000
```

**Known Issues:**
- May require Flask-SocketIO configuration
- Audio features depend on browser support

## Integration Example

Here's how to add Ollama to your own projects:

```python
import requests
import json

def ask_ai(question, model="qwen2.5:0.5b-instruct"):
    """Ask AI with streaming response for better performance"""
    try:
        with requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": question, "stream": True},
            stream=True,
            timeout=300
        ) as r:
            response_text = ""
            for line in r.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    response_text += data.get("response", "")
            return response_text
    except Exception as e:
        return f"Error: {e}"

# Use it in your project
answer = ask_ai("How should I greet users?")
print(answer)
```

## Recommended Models

For Raspberry Pi 5, these models offer the best performance:

1. **qwen2.5:0.5b-instruct** (Recommended)
   - Fast responses
   - Good accuracy
   - ~400MB size

2. **qwen2.5:0.5b-instruct-q4_0** (Lightest)
   - Fastest responses
   - Minimal RAM usage
   - Quantized for speed

3. **phi3:mini** (More capable)
   - Better for complex tasks
   - Larger model (~2GB)
   - Slower on Pi

## Setup

See the main Lab 3 README.md for complete setup instructions.

Quick setup:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended model
ollama pull qwen2.5:0.5b-instruct

# Test it
ollama run qwen2.5:0.5b-instruct

# Setup Python environment
python3 -m venv ollama_venv
source ollama_venv/bin/activate
pip install -r ollama_requirements.txt
```

## Troubleshooting

For audio issues, model problems, or other errors, see:
- `TROUBLESHOOTING.md` in this folder
- `OLLAMA_SETUP.md` for detailed setup guide

## Tips for Success

1. **Always use streaming** for better performance (see updated scripts)
2. **Start with the basic demo** to verify your setup works
3. **Use smaller models** for faster responses on Pi
4. **Keep prompts concise** to reduce processing time
5. **Activate the virtual environment** before running scripts

## Contributing

If you improve these scripts or fix issues, please share your updates!
