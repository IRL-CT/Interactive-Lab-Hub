import os
import re
import time
import json
import queue
import math
import threading
import datetime as dt
from dataclasses import dataclass, field
from typing import Optional, Tuple

# --- UI ---
import tkinter as tk
from tkinter import ttk, messagebox

# --- Audio / LLM ---
import requests
import subprocess
import speech_recognition as sr

# --------------------------
# Utilities
# --------------------------

def now_ts() -> float:
    return time.time()

def fmt_hms(seconds: int) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"

def fmt_clock(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts).strftime("%H:%M:%S")

# --------------------------
# TTS (espeak -> fallback pyttsx3)
# --------------------------

class Speaker:
    def __init__(self):
        self.lock = threading.Lock()
        self.available_espeak = self._has_espeak()
        self.pyttsx3_engine = None
        if not self.available_espeak:
            try:
                import pyttsx3
                self.pyttsx3_engine = pyttsx3.init()
            except Exception:
                self.pyttsx3_engine = None

    def _has_espeak(self) -> bool:
        try:
            subprocess.run(["espeak", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except Exception:
            return False

    def say(self, text: str):
        if not text:
            return
        with self.lock:
            if self.available_espeak:
                # espeak on Pi is robust and fast
                try:
                    subprocess.run(["espeak", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                except Exception:
                    pass
            elif self.pyttsx3_engine is not None:
                try:
                    self.pyttsx3_engine.say(text)
                    self.pyttsx3_engine.runAndWait()
                except Exception:
                    pass

# --------------------------
# STT
# --------------------------

class Listener:
    def __init__(self, mic_index: Optional[int] = None):
        self.rec = sr.Recognizer()
        self.rec.energy_threshold = 300  # tweakable
        self.rec.dynamic_energy_threshold = True
        self.mic_index = mic_index

    def list_devices(self):
        return sr.Microphone.list_microphone_names() or []

    def listen_once(self, timeout: int = 6, phrase_time_limit: int = 8) -> Optional[str]:
        # Try explicit index -> 'default' -> 'pulse'
        mic_candidates = []
        if self.mic_index is not None:
            mic_candidates.append(self.mic_index)
        # fallbacks use None (default device)
        mic_candidates.append(None)

        for idx in mic_candidates:
            try:
                with sr.Microphone(device_index=idx) as source:
                    # small ambient adjust
                    self.rec.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.rec.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                try:
                    text = self.rec.recognize_google(audio, language="zh-CN")  # CN first
                except Exception:
                    text = self.rec.recognize_google(audio, language="en-US")
                return text
            except Exception:
                continue
        return None

# --------------------------
# Intent parsing
# --------------------------

# Simple Chinese numerals (limited)
CN_NUM = {
    "零":0,"一":1,"两":2,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10
}
def cn_to_int(s: str) -> Optional[int]:
    # very small helper for “五分钟、十分钟、三小时”
    if not s:
        return None
    if s.isdigit():
        return int(s)
    # handle forms like 十五 / 二十
    total = 0
    if "十" in s:
        parts = s.split("十")
        left = CN_NUM.get(parts[0], 1 if parts[0]=="" else None)
        if left is None:
            return None
        right = CN_NUM.get(parts[1], 0 if len(parts)==2 and parts[1]=="" else None) if len(parts)>1 else 0
        if right is None:
            return None
        total = left*10 + right
        return total
    # single char
    if len(s) == 1 and s in CN_NUM:
        return CN_NUM[s]
    return None

duration_patterns = [
    # English patterns
    re.compile(r"(\d+)\s*(hours?|hrs?)", re.I),
    re.compile(r"(\d+)\s*(minutes?|mins?)", re.I),
    re.compile(r"(\d+)\s*(seconds?|secs?)", re.I),
    # Chinese patterns: 3小时/三小时/5分钟/五分钟
    re.compile(r"([零一两二三四五六七八九十\d]+)\s*小时"),
    re.compile(r"([零一两二三四五六七八九十\d]+)\s*分钟"),
    re.compile(r"([零一两二三四五六七八九十\d]+)\s*秒钟?"),
]

def extract_duration_seconds(text: str) -> Optional[int]:
    if not text:
        return None
    text = text.strip()
    # English first
    hrs = re.search(r"(\d+)\s*(hours?|hrs?)", text, re.I)
    mins = re.search(r"(\d+)\s*(minutes?|mins?)", text, re.I)
    secs = re.search(r"(\d+)\s*(seconds?|secs?)", text, re.I)
    total = 0
    if hrs:
        total += int(hrs.group(1)) * 3600
    if mins:
        total += int(mins.group(1)) * 60
    if secs:
        total += int(secs.group(1))
    if total > 0:
        return total

    # Chinese
    def cn_num_find(pat, unit_secs):
        m = re.search(pat, text)
        if m:
            raw = m.group(1)
            val = cn_to_int(raw) if not raw.isdigit() else int(raw)
            if val is not None:
                return val * unit_secs
        return 0

    total += cn_num_find(r"([零一两二三四五六七八九十\d]+)\s*小时", 3600)
    total += cn_num_find(r"([零一两二三四五六七八九十\d]+)\s*分钟", 60)
    total += cn_num_find(r"([零一两二三四五六七八九十\d]+)\s*秒钟?", 1)

    return total if total > 0 else None

def detect_intent(text: str, alerting: bool=False) -> Tuple[str, Optional[int]]:
    """
    Returns (intent, seconds) where seconds may be None.
    Intents: CONFIRM_TAKEN, SNOOZE, SET_TIMER, SMALLTALK
    """
    if not text:
        return ("SMALLTALK", None)

    t = text.lower()

    # confirm taken
    if any(k in t for k in ["i took", "i've taken", "taken", "done", "finished"]) or ("吃" in text and ("了" in text or "完成" in text or "搞定" in text)):
        return ("CONFIRM_TAKEN", None)

    # snooze (only makes sense when alerting)
    if alerting and (("snooze" in t) or ("later" in t) or ("再" in text and "分钟" in text) or ("等" in text)):
        secs = extract_duration_seconds(text)
        if secs is None:
            secs = 300  # default 5 min
        return ("SNOOZE", secs)

    # set timer / reminder
    if any(k in t for k in ["remind", "timer", "after", "in "]) or ("提醒" in text) or ("小时" in text) or ("分钟" in text):
        secs = extract_duration_seconds(text)
        if secs:
            return ("SET_TIMER", secs)

    return ("SMALLTALK", None)

# --------------------------
# LLM (Ollama) with timeout
# --------------------------

def ollama_reply(prompt: str, timeout: int = 5) -> Optional[str]:
    model = os.environ.get("OLLAMA_MODEL", "phi3:mini")
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("response", "").strip()
    except Exception:
        return None
    return None

# --------------------------
# Data classes
# --------------------------

@dataclass
class Schedule:
    next_ts: Optional[float] = None
    label: str = "Next dose"
    active: bool = False

    def set_after(self, seconds: int):
        self.next_ts = now_ts() + seconds
        self.active = True

    def snooze(self, seconds: int):
        if self.next_ts is None:
            self.next_ts = now_ts() + seconds
        else:
            self.next_ts = now_ts() + seconds
        self.active = True

    def clear(self):
        self.next_ts = None
        self.active = False

    def remaining(self) -> int:
        if not self.active or self.next_ts is None:
            return 0
        return int(self.next_ts - now_ts())

# --------------------------
# Main App
# --------------------------

class DoseAssistantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Daily Dose Assistant")
        self.geometry("820x520")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Components
        mic_index_env = os.environ.get("MIC_INDEX")
        self.listener = Listener(mic_index=int(mic_index_env) if mic_index_env and mic_index_env.isdigit() else None)
        self.speaker = Speaker()

        # State
        self.schedule = Schedule()
        self.alerting = False
        self.running = True

        # UI
        self._build_ui()

        # Threads
        self.event_queue = queue.Queue()
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()

        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        # UI updater
        self.after(200, self._ui_tick)

    # ----- UI -----
    def _build_ui(self):
        # Header controls
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        self.btn_start = ttk.Button(top, text="🎙️ Start Listening", command=self.toggle_listen)
        self.btn_start.pack(side="left")

        self.btn_switch_to_chat = ttk.Button(top, text="💬 Conversation", command=lambda: self.nb.select(self.frame_chat))
        self.btn_switch_to_chat.pack(side="left", padx=5)

        self.btn_switch_to_timer = ttk.Button(top, text="⏱️ Countdown", command=lambda: self.nb.select(self.frame_timer))
        self.btn_switch_to_timer.pack(side="left")

        self.btn_quick_5m = ttk.Button(top, text="+5 min", command=lambda: self.create_timer(5*60))
        self.btn_quick_5m.pack(side="right")
        self.btn_quick_3h = ttk.Button(top, text="+3 h", command=lambda: self.create_timer(3*3600))
        self.btn_quick_3h.pack(side="right", padx=5)

        # Notebook
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        # Conversation page
        self.frame_chat = ttk.Frame(self.nb)
        self.nb.add(self.frame_chat, text="💬 Conversation")

        self.txt_chat = tk.Text(self.frame_chat, wrap="word", font=("Helvetica", 12))
        self.txt_chat.pack(fill="both", expand=True)
        self._log("Assistant", "Hello! I’m your Daily Dose Assistant. Say something like “Remind me in 3 hours” or “我吃了 / 等五分钟”.")
        self._log("System", "TIP: You can set MIC_INDEX env to choose microphone.")

        # Timer page
        self.frame_timer = ttk.Frame(self.nb)
        self.nb.add(self.frame_timer, text="⏱️ Countdown")

        self.lbl_next = ttk.Label(self.frame_timer, text="Next dose: --:--:--", font=("Helvetica", 16))
        self.lbl_next.pack(pady=10)

        self.lbl_remaining = ttk.Label(self.frame_timer, text="00:00", font=("Helvetica", 48, "bold"))
        self.lbl_remaining.pack(pady=20)

        self.btn_clear = ttk.Button(self.frame_timer, text="Clear Timer", command=self.clear_timer)
        self.btn_clear.pack()

    def _log(self, who: str, text: str):
        self.txt_chat.insert("end", f"{who}: {text}\n")
        self.txt_chat.see("end")

    # ----- Threads -----

    def toggle_listen(self):
        # The listener thread runs continuous loop; this button just logs a hint
        self._log("System", "Listening loop is running. Speak after the beep if you hear one at alert time.")
        self.speaker.say("Listening")

    def _listen_loop(self):
        while self.running:
            # Passive listen; short sleep between cycles to reduce CPU
            text = self.listener.listen_once(timeout=3, phrase_time_limit=5)
            if not self.running:
                break
            if text:
                self.event_queue.put(("USER_TEXT", text))
            time.sleep(0.3)

    def _scheduler_loop(self):
        while self.running:
            time.sleep(0.2)
            if self.schedule.active and self.schedule.next_ts:
                if now_ts() >= self.schedule.next_ts and not self.alerting:
                    # Trigger alert
                    self.alerting = True
                    self.event_queue.put(("ALERT_START", None))
                    # Let alert window for 120 seconds if user does not respond
                    alert_deadline = now_ts() + 120
                    while self.alerting and now_ts() < alert_deadline and self.running:
                        time.sleep(0.2)
                    if self.alerting:
                        # timed out - stop alert and schedule remains cleared (or snoozed earlier)
                        self.alerting = False
                        # No auto-clear here; let user decide later
                        self.event_queue.put(("ALERT_TIMEOUT", None))

    # ----- Event Handling -----

    def handle_user_text(self, text: str):
        self._log("You", text)

        # First, see if it contains a duration to schedule
        intent, secs = detect_intent(text, alerting=self.alerting)

        # Ask Ollama for a friendly reply, but do not rely on it for logic
        reply = None
        try:
            reply = ollama_reply(f"User said: {text}\nReply briefly as a friendly pill reminder assistant. If they confirmed taking a dose, say 'Good job!'. If they asked to remind after a duration, acknowledge and repeat the duration.")
        except Exception:
            reply = None

        if intent == "CONFIRM_TAKEN":
            self.alerting = False
            self._log("Assistant", reply or "Good job! Want me to remind you again later?")
            self.speaker.say("Good job!")

        elif intent == "SNOOZE" and secs:
            self.alerting = False
            self.schedule.snooze(secs)
            target = fmt_clock(self.schedule.next_ts)
            self._log("Assistant", reply or f"Okay, I’ll remind you in {fmt_hms(secs)} at {target}.")
            self.speaker.say("Okay. I will remind you later.")
        elif intent == "SET_TIMER" and secs:
            self.create_timer(secs)
            target = fmt_clock(self.schedule.next_ts)
            self._log("Assistant", reply or f"Got it. I’ll remind you at {target}.")
            self.speaker.say("Timer set.")
        else:
            # small talk reply or fallback
            self._log("Assistant", reply or "I can set a reminder like “in 3 hours” or “等五分钟”，或者你说“我吃了”。")
            if reply:
                self.speaker.say(reply)

    def create_timer(self, secs: int):
        self.schedule.set_after(secs)
        self.nb.select(self.frame_timer)  # switch to timer page

    def clear_timer(self):
        self.schedule.clear()
        self._log("Assistant", "Timer cleared.")
        self.speaker.say("Timer cleared.")

    def start_alert(self):
        # Visual + audio alert
        self._log("Assistant", "Hey! Don’t forget the dose!")
        self.speaker.say("Hey! Don't forget the dose!")
        self.nb.select(self.frame_chat)

    # ----- UI Tick -----

    def _ui_tick(self):
        # handle queued events
        try:
            while True:
                ev, payload = self.event_queue.get_nowait()
                if ev == "USER_TEXT":
                    self.handle_user_text(payload)
                elif ev == "ALERT_START":
                    self.start_alert()
                elif ev == "ALERT_TIMEOUT":
                    self._log("System", "Alert ended (no response).")
        except queue.Empty:
            pass

        # update timer page
        if self.schedule.active and self.schedule.next_ts:
            rem = self.schedule.remaining()
            self.lbl_next.config(text=f"Next dose: {fmt_clock(self.schedule.next_ts)}")
            self.lbl_remaining.config(text=fmt_hms(rem))
            if rem <= 0:
                # stay active until scheduler thread fires alert; show 00:00
                self.lbl_remaining.config(text="00:00")
        else:
            self.lbl_next.config(text="Next dose: --:--:--")
            self.lbl_remaining.config(text="--:--")

        # UI refresh again
        self.after(200, self._ui_tick)

    # ----- Close -----
    def on_close(self):
        self.running = False
        try:
            self.destroy()
        except Exception:
            os._exit(0)

# --------------------------
# Entry
# --------------------------

if __name__ == "__main__":
    app = DoseAssistantApp()
    app.mainloop()
