import subprocess
from flask import Flask, render_template_string, request
from recognize_speech import record_and_recognize
import sys
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

MOODS = {
    "happy": "😺",
    "sad": "😿",
    "sick": "🤒",
    "sleepy": "😴",
    "excited": "😻"
}

def speak(text):
    # Use espeak_demo.sh for TTS
    subprocess.run(["bash", "./espeak.sh", text])

@app.route('/', methods=['GET', 'POST'])
def index():
    pet_name = "Milo"
    mood = None
    emoji = None
    if request.method == 'POST':
        spoken = record_and_recognize(
            model_lang="en-us",
            silence_threshold=600,
            silence_duration=1.2,
            max_duration=10
        )
        for key in MOODS:
            if key in spoken:
                mood = key
                emoji = MOODS[key]
                response = f"{pet_name} is {mood}"
                speak(response)
                break
        if not mood:
            mood = "unknown"
            emoji = "❓"
            speak(f"Sorry, I didn't catch that.")
    return render_template_string('''
        <h2>How is your pet today?</h2>
        <form method="post">
            <button type="submit">Speak Now</button>
        </form>
        {% if mood %}
            <h3>{{pet_name}} is {{mood}} {{emoji}}</h3>
        {% endif %}
    ''', pet_name=pet_name, mood=mood, emoji=emoji)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)