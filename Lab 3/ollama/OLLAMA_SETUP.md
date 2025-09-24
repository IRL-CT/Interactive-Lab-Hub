# Ollama Setup Instructions for Lab 3
*Interactive Device Design - Voice and Speech Prototypes*

## What is Ollama?

Ollama is a tool that lets you run large language models (like ChatGPT, but smaller) locally on your Raspberry Pi. This means your voice assistant can have intelligent conversations without needing internet connectivity for AI processing!

## 🚀 Quick Setup

### Step 1: Install Ollama

Run this command in your terminal:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Download a Model

We recommend **phi3:mini** for Raspberry Pi 5 - it's fast, lightweight, and smart enough for prototyping:

```bash
ollama pull phi3:mini
```

*This will download about 2.2GB, so make sure you have good internet and some patience!*

### Step 3: Test Your Installation

```bash
ollama run phi3:mini "Hello, introduce yourself!"
```

You should see a response from the AI model.

### Step 4: Install Python Dependencies

```bash
pip install requests speechrecognition pyaudio flask flask-socketio
```

## 🎯 Ready-to-Use Scripts

We've created several scripts for different use cases:

### 1. Simple Demo (`ollama_demo.py`)
```bash
python3 ollama_demo.py
```
- Basic text chat with Ollama
- Text-to-speech responses
- Perfect for understanding how Ollama works

### 2. Voice Assistant (`ollama_voice_assistant.py`)
```bash
python3 ollama_voice_assistant.py
```
- Full voice interaction (speech-to-text + Ollama + text-to-speech)
- Natural conversation flow
- Say "hello" to start, "goodbye" to exit

### 3. Web Interface (`ollama_web_app.py`)
```bash
python3 ollama_web_app.py
```
- Beautiful web interface at `http://localhost:5000`
- Chat interface with voice options
- Great for prototyping web-based voice interactions

## 🔧 Troubleshooting

### "Ollama not responding"
Make sure Ollama is running:
```bash
ollama serve
```
Then try your script again.

### "Model not found"
List available models:
```bash
ollama list
```
If phi3:mini isn't there, pull it again:
```bash
ollama pull phi3:mini
```

### Speech Recognition Issues
Make sure your microphone is working:
```bash
python3 speech-scripts/test_microphone.py
```

### Audio Output Issues
Test with espeak:
```bash
espeak "Hello from your Pi"
```

## 📚 For Your Projects

### Quick Integration Template

```python
import requests

def ask_ollama(question):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3:mini",
            "prompt": question,
            "stream": False
        }
    )
    return response.json().get('response', 'Sorry, no response')

# Use it in your project
answer = ask_ollama("What's the weather like?")
print(answer)
```

### Make Your Assistant Specialized

Add a system prompt to make your assistant behave differently:

```python
def ask_specialized_ollama(question, personality):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3:mini",
            "prompt": question,
            "system": personality,  # This changes behavior!
            "stream": False
        }
    )
    return response.json().get('response', 'Sorry, no response')

# Examples:
chef_response = ask_specialized_ollama(
    "What should I cook?", 
    "You are a helpful chef. Give short, practical cooking advice."
)

therapist_response = ask_specialized_ollama(
    "I'm feeling stressed", 
    "You are a supportive counselor. Be empathetic and encouraging."
)
```

## 🎨 Creative Ideas for Your Project

1. **Smart Home Assistant**: "Turn on the lights" → Ollama processes → controls GPIO
2. **Language Tutor**: Practice conversations in different languages
3. **Storytelling Device**: Interactive storytelling with AI-generated plots
4. **Cooking Assistant**: Voice-controlled recipe helper
5. **Study Buddy**: AI tutor that adapts to your learning style
6. **Emotion Support**: An empathetic companion for daily check-ins
7. **Game Master**: AI-powered text adventure games
8. **Creative Writing Partner**: Collaborative story creation

## 📖 Additional Resources

- [Ollama Documentation](https://docs.ollama.com)
- [Available Models](https://ollama.com/library) (try different ones!)
- [Ollama API Reference](https://docs.ollama.com/api)

## 🆘 Getting Help

1. Check the troubleshooting section above
2. Ask in the class Slack channel
3. Use WendyTA (mention "@Ollama" in your question)
4. Office hours with TAs

## 🏆 Pro Tips

1. **Model Size vs Speed**: Smaller models (like phi3:mini) are faster but less capable
2. **Internet Independence**: Once downloaded, models work offline!
3. **Experiment**: Try different system prompts to change personality
4. **Combine with Sensors**: Use Pi sensors + Ollama for context-aware responses
5. **Memory**: Each conversation is independent - add conversation history if needed

---

*Happy prototyping! Remember: the goal is to rapidly iterate and test ideas with real users.*