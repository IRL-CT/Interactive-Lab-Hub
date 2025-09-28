#!/bin/bash

echo "🎉 Party Game Voice Assistant Setup 🎉"
echo "======================================"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if required tools are installed
echo "🔍 Checking dependencies..."

# Check Piper
if ! command -v piper &> /dev/null; then
    echo "❌ Piper not found. Installing..."
    pip install piper-tts
fi

# Check Whisper
if ! command -v whisper &> /dev/null; then
    echo "❌ Whisper not found. Installing..."
    pip install openai-whisper
fi

# Check if Ollama is running
echo "🤖 Checking Ollama..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama not running. Starting Ollama serve..."
    ollama serve &
    sleep 3
fi

# Check if we have a model
echo "📥 Checking Ollama models..."
if ! ollama list | grep -q "llama3.2"; then
    echo "📥 Downloading Ollama model (this may take a while)..."
    ollama pull llama3.2:1b  # Smaller model for Pi
fi

echo "✅ Setup complete!"
echo ""
echo "🎯 Starting Party Game Assistant..."
echo "=================================="

# Run the assistant
python3 party_game_assistant.py

echo ""
echo "🎊 Thanks for using the Party Game Assistant!"