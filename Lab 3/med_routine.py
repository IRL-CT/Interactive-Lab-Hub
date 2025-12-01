import os
import time
import re
import whisper
import subprocess
from datetime import datetime, timedelta

# ================== Google TTS ==================
def say(text, lang="en"):
    text = text.replace(" ", "+")
    url = f"http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q={text}&tl={lang}"
    subprocess.run(["mplayer", "-ao", "alsa", "-really-quiet", "-noconsolecontrols", url])

# ================== Setting the alarm ==================
say("What time would you like to take your medicine? Please use 24-hour format.")
os.system("echo -e '\a'")
time.sleep(0.5)
print("Recording your answer...")
os.system("arecord -f cd -d 5 -t wav -r 16000 -c 1 response.wav")
print("Finished recording.")

model = whisper.load_model("tiny")
result = model.transcribe("response.wav", language="en")
text = result["text"].strip()
print(f"You said: {text}")

# === Extract time (24-hour format, e.g., 14:30 or 1830) ===
text = text.lower()
time_patterns = [
    r"(\d{1,2}):(\d{2})",          # e.g. 14:30
    r"(\d{2})(\d{2})",             # e.g. 1830
    r"(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(\d{2})?"
]

num_map = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "twenty one": 21, "twenty two": 22, "twenty three": 23
}

hour, minute = None, 0

for p in time_patterns:
    match = re.search(p, text)
    if match:
        if p == time_patterns[0] or p == time_patterns[1]:
            hour = int(match.group(1))
            minute = int(match.group(2))
            break
        elif match.group(1) in num_map:
            hour = num_map[match.group(1)]
            minute = int(match.group(2)) if match.group(2) else 0
            break

# === Confirm extracted time ===
if hour is not None:
    say(f"You said {hour:02d}:{minute:02d}. Is that correct?")
    print(f"Detected time: {hour:02d}:{minute:02d}")
else:
    say("Sorry, I could not detect the time. Please try again.")
    exit()

# === Confirmation recording ===
os.system("arecord -f cd -d 3 -t wav -r 16000 -c 1 confirm.wav")
confirm = model.transcribe("confirm.wav", language="en")["text"].lower()
print("Confirmation:", confirm)

if "yes" not in confirm:
    say("Okay, let's try again later.")
    exit()

# === Set alarm ===
from datetime import datetime, timedelta
now = datetime.now()
alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
if alarm_time < now:
    alarm_time += timedelta(days=1)

say(f"Alarm set for {alarm_time.strftime('%H:%M')}.")

# ================== waiting for alarm ==================
alarm_triggered = False
medicine_taken = False

while True:
    now = datetime.now()
    if not alarm_triggered and now >= alarm_time:
        alarm_triggered = True
        say("It's time to take your medicine!")
        
        # Confirmation
        time.sleep(10) # wait 10 seconds before asking
        say("Did you take your medicine?")
        print("Recording your confirmation...")
        os.system("arecord -f cd -d 5 -t wav -r 16000 -c 1 confirm_medicine.wav")
        response = model.transcribe("confirm_medicine.wav", language="en")["text"].lower()
        print("User response:", response)
        
        if "yes" in response:
            medicine_taken = True
            say("Good job! Don't forget it tomorrow!")
        else:
            say("Okay, remember to take it soon!")
    
    time.sleep(5)  # Check every 5 seconds
