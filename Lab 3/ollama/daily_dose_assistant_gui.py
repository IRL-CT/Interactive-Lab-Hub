# -*- coding: utf-8 -*-
"""
Daily Dose Voice Assistant for ST7789 (240x135) + 2 buttons via gpiozero.
- Page A: Chat context (ASR user text + Ollama reply), English-only on screen
- Page B: Timer countdown; natural language duration parsing ("5 minutes", "30 sec", "1h 20m", etc.)
- TTS via eSpeak -> paplay (fallback to aplay -D pulse)
- Buttons:
    BTN_A (GPIO23): On Chat page -> start one-shot speech capture; On Timer page -> switch to Chat
    BTN_B (GPIO24): Switch to Timer page

Run:
    MIC_INDEX=0 python3 daily_dose_assistant_st7789_buttons_pulse_tts.py
"""

import os
import re
import time
import math
import queue
import json
import threading
import requests
import subprocess
import shutil

# -----------------------------
# Display (ST7789 240x135)
# -----------------------------
import board, busio, digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

ROTATION = 180
X_OFFSET, Y_OFFSET = 53, 40   # for 240x135 wide layout
BAUDRATE = 64_000_000

spi = board.SPI()
dc_pin = digitalio.DigitalInOut(board.D25)
disp = st7789.ST7789(
    spi,
    cs=None,
    dc=dc_pin,
    rst=None,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=X_OFFSET,
    y_offset=Y_OFFSET,
    rotation=ROTATION
)
W, H = disp.width, disp.height
image = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(image)

def ensure_canvas():
    global image, draw, W, H
    if image.size != (disp.width, disp.height):
        W, H = disp.width, disp.height
        image = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(image)

# Fonts
def load_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()

FONT_SMALL = load_font(12)
FONT_MED   = load_font(14)
FONT_BIG   = load_font(32)

# -----------------------------
# Buttons via gpiozero
# -----------------------------
from gpiozero import Button
BTN_A_PIN = 23
BTN_B_PIN = 24
btn_a = Button(BTN_A_PIN, pull_up=True, bounce_time=0.05)
btn_b = Button(BTN_B_PIN, pull_up=True, bounce_time=0.05)

# -----------------------------
# Global App State
# -----------------------------
PAGE_CHAT  = "chat"
PAGE_TIMER = "timer"

current_page = PAGE_CHAT

chat_history = []   # list of tuples: ("You", text) or ("Assistant", text)
MAX_CHAT_LINES = 8
MAX_HIST = 50

# Timer state
timer_running = False
timer_end_ts = 0.0
timer_last_cmd = ""
timer_remaining_text = "00:00"

# Speech / Ollama control
MIC_INDEX = int(os.environ.get("MIC_INDEX", "0"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini")
ASR_TIMEOUT = 6.0
OLLAMA_TIMEOUT = 60

# Thread comms
asr_request_q = queue.Queue()
tts_q = queue.Queue()
stop_event = threading.Event()

# -----------------------------
# Utils
# -----------------------------
def ascii_only(s: str) -> str:
    return (s or "").encode("ascii", "ignore").decode()

def wrap_text(txt, font, max_width):
    words = txt.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def format_hms(seconds: int) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"

# -----------------------------
# TTS via paplay / aplay -D pulse
# -----------------------------
def speak_text(text: str, rate: int = 175, pitch: int = 50, voice: str = "en-us"):
    if not text:
        return
    clean = ascii_only(text)
    espeak_cmd = [
        "espeak", "-s", str(rate), "-p", str(pitch), "-v", voice, clean, "--stdout"
    ]
    use_paplay = shutil.which("paplay") is not None
    try:
        if use_paplay:
            p1 = subprocess.Popen(espeak_cmd, stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["paplay"], stdin=p1.stdout)
            p1.stdout.close()
            p2.communicate()
            return
        else:
            p1 = subprocess.Popen(espeak_cmd, stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["aplay", "-D", "pulse"], stdin=p1.stdout)
            p1.stdout.close()
            p2.communicate()
    except Exception:
        pass

def tts_worker():
    while not stop_event.is_set():
        try:
            msg = tts_q.get(timeout=0.1)
        except queue.Empty:
            continue
        try:
            speak_text(msg)
        except Exception:
            pass

# -----------------------------
# ASR (SpeechRecognition)
# -----------------------------
def recognize_one_utterance():
    import speech_recognition as sr
    r = sr.Recognizer()
    with sr.Microphone(device_index=MIC_INDEX) as source:
        r.energy_threshold = 300
        r.dynamic_energy_threshold = True
        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
        except Exception:
            pass
        audio = r.listen(source, timeout=ASR_TIMEOUT, phrase_time_limit=ASR_TIMEOUT)

    text = ""
    try:
        text = r.recognize_sphinx(audio)
    except Exception:
        pass

    if not text:
        try:
            text = r.recognize_google(audio, language="en-US")
        except Exception:
            pass

    return ascii_only(text.strip())

def asr_worker():
    while not stop_event.is_set():
        try:
            req = asr_request_q.get(timeout=0.1)
        except queue.Empty:
            continue
        if req != "listen":
            continue

        user_text = ""
        try:
            user_text = recognize_one_utterance()
        except Exception:
            user_text = ""

        if not user_text:
            add_chat("You", "(could not understand)")
            continue

        add_chat("You", user_text)
        dur = parse_duration_seconds(user_text)
        if dur > 0:
            start_timer(dur)
            global timer_last_cmd
            timer_last_cmd = user_text

        reply = ollama_respond(user_text)
        if not reply:
            reply = "I had trouble generating a response. Please try again."
        add_chat("Assistant", reply)
        tts_q.put(reply)

# -----------------------------
# Ollama
# -----------------------------
def ollama_respond(user_text: str) -> str:
    prompt = (
        "You are a brief, helpful assistant. "
        "If the user asks for a timer, acknowledge it succinctly. "
        "Keep answers short.\n\n"
        f"User: {user_text}\nAssistant:"
    )
    data = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        resp = requests.post(OLLAMA_URL, json=data, timeout=OLLAMA_TIMEOUT)
        if resp.ok:
            js = resp.json()
            out = js.get("response", "")
            return ascii_only(out.strip())
    except Exception:
        pass
    return ""

# -----------------------------
# Duration Parsing
# -----------------------------
DUR_PATTERN = re.compile(
    r"(?:(\d+)\s*(?:hours?|hrs?|h))?\s*"
    r"(?:(\d+)\s*(?:minutes?|mins?|m))?\s*"
    r"(?:(\d+)\s*(?:seconds?|secs?|s))?",
    re.IGNORECASE
)

def parse_duration_seconds(text: str) -> int:
    txt = ascii_only(text.lower())
    m = DUR_PATTERN.search(txt)
    if m:
        h = int(m.group(1) or 0)
        m_ = int(m.group(2) or 0)
        s = int(m.group(3) or 0)
        total = h*3600 + m_*60 + s
        if total > 0:
            return total

    alt = 0
    m2 = re.findall(r"(\d+)\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes|s|sec|secs|second|seconds)\b", txt)
    for val, unit in m2:
        v = int(val)
        if unit.startswith("h"):
            alt += v*3600
        elif unit.startswith("m"):
            alt += v*60
        else:
            alt += v
    return alt

def start_timer(seconds: int):
    global timer_running, timer_end_ts
    timer_running = True
    timer_end_ts = time.time() + seconds

# -----------------------------
# Chat helpers
# -----------------------------
def add_chat(who: str, text: str):
    t = ascii_only(text or "")
    chat_history.append((who, t))
    if len(chat_history) > MAX_HIST:
        del chat_history[:len(chat_history)-MAX_HIST]

# -----------------------------
# UI Rendering
# -----------------------------
BG = (0, 0, 0)
FG = (235, 235, 245)
FG_DIM = (180, 180, 200)
ACCENT = (90, 170, 255)

def draw_header(title: str, sub: str = ""):
    draw.rectangle((0, 0, W, 20), fill=(20, 20, 30))
    draw.text((4, 3), ascii_only(title), font=FONT_MED, fill=FG)
    if sub:
        sw = draw.textlength(ascii_only(sub), font=FONT_SMALL)
        draw.text((W - 4 - sw, 4), ascii_only(sub), font=FONT_SMALL, fill=FG_DIM)

def render_chat_page():
    ensure_canvas()
    draw.rectangle((0, 0, W, H), fill=BG)
    draw_header("Daily Dose • Chat", "BTN_A=Speak  BTN_B=Timer")
    y = 24
    maxw = W - 8
    combined = []
    for who, text in chat_history[-12:]:
        who_tag = "You: " if who == "You" else "AI: "
        for line in wrap_text(who_tag + text, FONT_SMALL, maxw):
            combined.append(line)
    for line in combined[-MAX_CHAT_LINES:]:
        draw.text((4, y), line, font=FONT_SMALL, fill=FG)
        y += 14
    disp.image(image)

def render_timer_page():
    ensure_canvas()
    draw.rectangle((0, 0, W, H), fill=BG)
    draw_header("Daily Dose • Timer", "BTN_A=Chat  BTN_B=Timer")
    remain = 0
    if timer_running:
        remain = max(0, int(timer_end_ts - time.time()))
    ttxt = format_hms(remain)
    tw = draw.textlength(ttxt, font=FONT_BIG)
    draw.text(((W - tw)//2, 40), ttxt, font=FONT_BIG, fill=ACCENT)
    if timer_running and remain > 0:
        draw.text((4, 90), "Running...", font=FONT_MED, fill=FG)
    elif timer_running and remain <= 0:
        draw.text((4, 90), "Done!", font=FONT_MED, fill=(255, 220, 120))
    else:
        draw.text((4, 90), "No active timer", font=FONT_MED, fill=FG_DIM)
    if timer_last_cmd:
        for i, line in enumerate(wrap_text("Last: " + timer_last_cmd, FONT_SMALL, W-8)):
            draw.text((4, 110 + i*14), line, font=FONT_SMALL, fill=FG_DIM)
    disp.image(image)

# -----------------------------
# UI / Logic Loop
# -----------------------------
def ui_loop():
    global current_page, timer_running
    while not stop_event.is_set():
        # Timer update
        if timer_running and time.time() >= timer_end_ts:
            timer_running = False
            tts_q.put("Timer finished.")
        # Buttons
        if btn_a.is_pressed:
            # 小延时做去抖
            time.sleep(0.02)
            if btn_a.is_pressed:
                if current_page == PAGE_CHAT:
                    asr_request_q.put("listen")
                else:
                    current_page = PAGE_CHAT
                # 等松手，避免长按多次触发
                btn_a.wait_for_release(timeout=0.6)

        if btn_b.is_pressed:
            time.sleep(0.02)
            if btn_b.is_pressed:
                current_page = PAGE_TIMER
                btn_b.wait_for_release(timeout=0.6)

        # Render
        if current_page == PAGE_CHAT:
            render_chat_page()
        else:
            render_timer_page()

        time.sleep(0.03)

# -----------------------------
# Main
# -----------------------------
def main():
    add_chat("Assistant", "Hello! Press BTN_A to speak. BTN_B to show timer.")
    th_tts = threading.Thread(target=tts_worker, daemon=True)
    th_asr = threading.Thread(target=asr_worker, daemon=True)
    th_ui  = threading.Thread(target=ui_loop, daemon=True)
    th_tts.start(); th_asr.start(); th_ui.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        try:
            draw.rectangle((0,0,W,H), fill=(0,0,0))
            disp.image(image)
        except Exception:
            pass

if __name__ == "__main__":
    main()
