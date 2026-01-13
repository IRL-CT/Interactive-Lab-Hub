import os
import time
import re
import whisper
import subprocess

# === Google TTS 函數 ===
def say(text, lang="en"):
    """用 Google Translate TTS 語音播放文字"""
    text = text.replace(" ", "+")
    url = f"http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q={text}&tl={lang}"
    subprocess.run(["mplayer", "-ao", "alsa", "-really-quiet", "-noconsolecontrols", url])

# === Step 1: 語音提問 ===
say("What time would you like to take your medicine? Please specify am or pm.")

# Add a beep sound
os.system("echo -e '\a'")  # System bell beep
time.sleep(0.5)  # Small delay after beep

# === Step 2: 錄音 ===
print("Recording... please say the time now.")
os.system("arecord -f cd -d 5 -t wav -r 16000 -c 1 response.wav")
print("Recording finished.")

# === Step 3: Whisper 辨識 ===
start_time = time.perf_counter()
model = whisper.load_model("tiny")
result = model.transcribe("response.wav", language="en")
text = result["text"].strip()
print(f"You said: {text}")
end_time = time.perf_counter()
print(f"Transcription took {end_time - start_time:.2f} seconds")

# === Step 4: 從文字中找時間 ===
patterns = [
    r"([0-9]{1,2})\s*(?:o'?clock|pm|am)?",
    r"(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
]

time_match = None
for p in patterns:
    m = re.search(p, text.lower())
    if m:
        time_match = m.group(1)
        break

num_map = {
    "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8",
    "nine": "9", "ten": "10", "eleven": "11", "twelve": "12"
}
if time_match in num_map:
    time_match = num_map[time_match]

if time_match:
    say(f"You want to take your medicine at {time_match} o'clock. Is that correct?")
else:
    say("Sorry, I could not detect the time. Please try again.")
