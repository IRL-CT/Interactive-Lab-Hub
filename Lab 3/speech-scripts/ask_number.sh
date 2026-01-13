#!/bin/bash

# Configurable variables
QUESTION="Please answer the question: How many boroughs in New York City?"
OUTPUT_AUDIO="response.wav"
TRANSCRIPT="response.txt"
MODEL="tiny"


# 1. Text-to-speech function

say() { 
    local IFS=+
    /usr/bin/mplayer -ao alsa -really-quiet -noconsolecontrols \
    "http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q=$*&tl=en"
}

# Speak the question
say "$QUESTION"
sleep 0.2



# 2. Record audio
echo "Recording... Please speak now."
arecord -f cd -d 3 -t wav -r 16000 -c 1 "$OUTPUT_AUDIO"
echo "Recording finished."


# 3. Transcribe with Whisper
if ! command -v whisper >/dev/null 2>&1; then
    echo "Error: whisper CLI not found. Install with 'pip install git+https://github.com/openai/whisper.git'"
    exit 1
fi

# Run Whisper
whisper "$OUTPUT_AUDIO" --model "$MODEL" --output_format txt --output_dir .


# 4. Read transcription result
# Whisper automatically creates a TXT file with the same basename as the audio
if [[ -f "${OUTPUT_AUDIO%.wav}.txt" ]]; then
    RESPONSE=$(cat "${OUTPUT_AUDIO%.wav}.txt")
    echo "You said: $RESPONSE"
    # Optional: speak back the answer
    say "You said: $RESPONSE"
else
    echo "Error: transcription file not found."
    exit 1
fi


# 5. Save to file
echo "$RESPONSE" > "$TRANSCRIPT"
echo "Answer saved to $TRANSCRIPT"
