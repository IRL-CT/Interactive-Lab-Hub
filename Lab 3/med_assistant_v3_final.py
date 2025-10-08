#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medication Voice Assistant — v3 FINAL
Fixes:
  1) TTS first words get cut on Bluetooth: add a short audio warm‑up using
     espeak‑ng with amplitude 0 before the real speech (keeps sink awake).
  2) Display time not updating: add a 1 Hz live countdown/clock while scheduled.

Other notes:
  - Pillow 10+ safe (uses textbbox fallback).
  - Buttons: TOP=BCM23, BOTTOM=BCM24 via gpiozero; suggest GPIOZERO_PIN_FACTORY=lgpio.
  - Screen pins aligned with your lab: cs=D5, dc=D25, rst=None, backlight=GPIO22.
  - Vosk callback feeds bytes(indata) to avoid cffi TypeError.
  - Natural language time parsing; supports "in 3 minutes", "one minute", "at 8:05 pm".

Run (no display, to verify flow):
  USE_DISPLAY=0 BUTTON_BACKEND=gpio GPIOZERO_PIN_FACTORY=lgpio \
  "../.venv/bin/python" med_assistant_v3_final.py

Run with display (stop course service first):
  sudo systemctl stop piscreen.service --now
  BUTTON_BACKEND=gpio USE_DISPLAY=1 GPIOZERO_PIN_FACTORY=lgpio \
  ../.venv/bin/python med_assistant_v3_final.py

Choose mic by name (optional):
  SD_INPUT_NAME=Logi BUTTON_BACKEND=gpio USE_DISPLAY=0 GPIOZERO_PIN_FACTORY=lgpio \
  ../.venv/bin/python med_assistant_v3_final.py
"""

import os, sys, time, re, queue, threading, subprocess, tempfile, math
from datetime import datetime, timedelta

# -------- console encoding --------
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DEBUG = False

# -------- optional imports --------
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

try:
    import dateparser
except Exception:
    dateparser = None

try:
    import sounddevice as sd
    from vosk import Model, KaldiRecognizer
    _ASR_AVAILABLE = True
except Exception:
    sd = None
    Model = None
    KaldiRecognizer = None
    _ASR_AVAILABLE = False

try:
    from gpiozero import Button
except Exception:
    Button = None

try:
    from evdev import InputDevice, ecodes, list_devices
    _EVDEV = True
except Exception:
    _EVDEV = False

_USE_DISPLAY = os.getenv('USE_DISPLAY', '1') != '0'
_DISPLAY_AVAILABLE = _USE_DISPLAY
try:
    import board, digitalio
    from PIL import Image, ImageDraw, ImageFont
    import adafruit_rgb_display.st7789 as st7789
except Exception:
    _DISPLAY_AVAILABLE = False
    board = digitalio = Image = ImageDraw = ImageFont = st7789 = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

# -------- config --------
WORKDIR = os.path.abspath(os.path.dirname(__file__))
MODEL_DIR = os.path.join(WORKDIR, 'models', 'vosk-en')
if not os.path.isdir(MODEL_DIR):
    alt = os.path.join(WORKDIR, '..', 'speech-scripts', 'models', 'vosk-en')
    if os.path.isdir(alt): MODEL_DIR = alt

TOP_BUTTON_PIN = int(os.getenv('TOP_BUTTON_PIN', '23'))
BOTTOM_BUTTON_PIN = int(os.getenv('BOTTOM_BUTTON_PIN', '24'))
BUTTON_BACKEND = os.getenv('BUTTON_BACKEND', '').strip().lower()  # '', 'gpio', 'evdev', 'keyboard'
BUTTON_DEBOUNCE_S = 0.10

RING_WINDOW_SEC = 30
SNOOZE_SEC = 30
MIN_DELAY_SEC = 5
MAX_DELAY_SEC = 24*3600

ASR_SAMPLE_RATE = 16000
ASR_LISTEN_WINDOW_SEC = 8

LOCAL_TZ_NAME = os.getenv('TZ', 'America/New_York')
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME) if ZoneInfo else None

# -------- utils --------

def now_tz():
    return datetime.now(tz=LOCAL_TZ) if LOCAL_TZ else datetime.now()

def humanize_delta(seconds:int) -> str:
    seconds=max(0,int(seconds)); h,rem=divmod(seconds,3600); m,s=divmod(rem,60)
    if h: return f"{h} hour{'s' if h!=1 else ''} {m} minute{'s' if m!=1 else ''}" if m else f"{h} hour{'s' if h!=1 else ''}"
    if m: return f"{m} minute{'s' if m!=1 else ''}"
    return f"{s} second{'s' if s!=1 else ''}"

def clamp_delay(seconds:int) -> int:
    return max(MIN_DELAY_SEC, min(MAX_DELAY_SEC, seconds))

# -------- TTS --------
class Speaker:
    def __init__(self):
        self._has_espeak = self._check_espeak()
        self._tts_engine = None
        if not self._has_espeak and pyttsx3 is not None:
            try: self._tts_engine = pyttsx3.init()
            except Exception: self._tts_engine = None

    def _check_espeak(self) -> bool:
        try:
            subprocess.run(['espeak-ng','--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    def _prime_audio(self):
        """Warm-up the audio path (esp. Bluetooth) without audible output."""
        if not self._has_espeak:
            return
        try:
            # amplitude 0 means silence; short warm-up to wake the sink
            subprocess.run(['espeak-ng','-a','0','-s','140','warmup'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            # small pause to let the sink fully open
            time.sleep(0.12)
        except Exception:
            pass

    def say(self, text:str, rate_wpm:int=170):
        text=(text or '').encode('ascii',errors='ignore').decode('ascii')
        if not text: return
        print('[TTS]', text)
        if self._has_espeak:
            self._prime_audio()
            try:
                subprocess.run(['espeak-ng','-s',str(rate_wpm), text], check=False)
            except Exception as e:
                print('[TTS] espeak-ng error:', e)
        elif self._tts_engine is not None:
            try:
                self._tts_engine.setProperty('rate', rate_wpm)
                self._tts_engine.say(text); self._tts_engine.runAndWait()
            except Exception as e:
                print('[TTS] pyttsx3 error:', e)

# -------- Display --------
class Display:
    WIDTH=135; HEIGHT=240; ROTATION=90
    def __init__(self):
        self.available=_DISPLAY_AVAILABLE
        self._disp=None
        if not self.available: return
        try:
            cs_pin=digitalio.DigitalInOut(board.D5)
            dc_pin=digitalio.DigitalInOut(board.D25)
            reset_pin=None
            spi=board.SPI()
            self._disp=st7789.ST7789(
                spi, cs=cs_pin, dc=dc_pin, rst=reset_pin,
                baudrate=64000000, width=self.WIDTH, height=self.HEIGHT,
                x_offset=53, y_offset=40,
            )
            self._image=Image.new('RGB',(self.HEIGHT,self.WIDTH))
            self._draw=ImageDraw.Draw(self._image)
            try:
                self._font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
            except Exception:
                self._font=ImageFont.load_default()
            try:
                self._backlight=digitalio.DigitalInOut(board.D22)
                self._backlight.switch_to_output(); self._backlight.value=True
            except Exception:
                pass
            self._clear((0,0,0))
        except Exception as e:
            print('[DISPLAY] Init failed, console fallback:', e)
            self.available=False

    def _clear(self,color=(0,0,0)):
        if not self.available: return
        self._draw.rectangle((0,0,self._image.width,self._image.height), fill=color)
        self._disp.image(self._image, rotation=self.ROTATION)

    def _measure(self,text:str):
        if hasattr(self._draw,'textbbox'):
            b=self._draw.textbbox((0,0),text,font=self._font); return (b[2]-b[0],b[3]-b[1])
        return self._draw.textsize(text,font=self._font)

    def _write_center(self, lines, fill=(255,255,255)):
        for ln in lines:
            print('[DISPLAY]', (ln or '').encode('ascii','ignore').decode('ascii'))
        if not self.available: return
        self._clear((0,0,0))
        total_h=0; sizes=[]
        for ln in lines:
            w,h=self._measure(ln); sizes.append((w,h)); total_h+=h
        y=(self._image.height-total_h)//2
        for (ln,(w,h)) in zip(lines,sizes):
            x=(self._image.width-w)//2
            self._draw.text((x,y),ln,font=self._font,fill=fill); y+=h+2
        self._disp.image(self._image, rotation=self.ROTATION)

    def show_idle(self):
        self._write_center(['Medication Assistant','Press TOP to start'],(180,220,255))
    def show_listening(self):
        self._write_center(['Listening...','Say a time'],(255,255,180))
    def show_scheduled(self, dt:datetime):
        tstr = dt.astimezone(LOCAL_TZ).strftime('%H:%M:%S') if (LOCAL_TZ and dt.tzinfo) else dt.strftime('%H:%M:%S')
        self._write_center(['Scheduled for', tstr], (180,255,200))
    def show_ringing(self):
        self._write_center(['Time to take','medicine'], (255,200,200))
    def show_snoozed(self):
        self._write_center(['Snoozed','30 s'], (200,220,255))
    def show_finished(self):
        self._write_center(['Taken','OK'], (200,255,200))
    def show_error(self,msg:str):
        self._write_center(['Error', msg or ''], (255,180,180))

    # live countdown painter
    def show_countdown(self, target: datetime):
        if not self.available: return
        now = now_tz()
        remaining = max(0, int((target - now).total_seconds()))
        minutes, seconds = divmod(remaining, 60)
        # Build two lines: T-minus and current time
        tline = f"T- {minutes:02d}:{seconds:02d}"
        nline = now.strftime('%H:%M:%S')
        # Draw
        self._clear((0,0,0))
        # Title
        title='Next Reminder'
        tw,th=self._measure(title); x=(self._image.width-tw)//2
        self._draw.text((x,6), title, font=self._font, fill=(180,255,200))
        # Target time
        tgt = target.strftime('%H:%M:%S') if (not LOCAL_TZ or not target.tzinfo) else target.astimezone(LOCAL_TZ).strftime('%H:%M:%S')
        gw,gh=self._measure(tgt); gx=(self._image.width-gw)//2
        self._draw.text((gx, 6+th+6), tgt, font=self._font, fill=(180,255,200))
        # Countdown
        cw,ch=self._measure(tline); cx=(self._image.width-cw)//2
        self._draw.text((cx, 6+th+6+gh+10), tline, font=self._font, fill=(255,255,180))
        # Now time at bottom
        nw,nh=self._measure(nline); nx=(self._image.width-nw)//2
        self._draw.text((nx, self._image.height-nh-8), nline, font=self._font, fill=(200,220,255))
        self._disp.image(self._image, rotation=self.ROTATION)

# -------- ASR --------
class Listener:
    def __init__(self, model_dir:str):
        if not _ASR_AVAILABLE: raise RuntimeError('ASR unavailable')
        if not os.path.isdir(model_dir): raise RuntimeError('Vosk model not found: '+model_dir)
        self._model = Model(model_dir)
        self._device_index = None
        name_hint = os.getenv('SD_INPUT_NAME','').strip()
        if name_hint and sd is not None:
            try:
                for i, d in enumerate(sd.query_devices()):
                    if d.get('max_input_channels',0)>0 and name_hint.lower() in str(d.get('name','')).lower():
                        self._device_index=i; print(f"[ASR] Using input device #{i}: {d['name']}")
                        break
            except Exception as e:
                print('[ASR] query_devices failed:', e)

    def listen(self, max_sec:int) -> str | None:
        rec = KaldiRecognizer(self._model, ASR_SAMPLE_RATE)
        rec.SetWords(True)
        result_text=None
        def cb(indata, frames, time_info, status):
            nonlocal result_text
            try:
                if rec.AcceptWaveform(bytes(indata)):
                    result_text=_extract_text(rec.Result())
            except Exception as e:
                print('[ASR-cb] error:', e)
        kwargs = dict(samplerate=ASR_SAMPLE_RATE, blocksize=8000, dtype='int16', channels=1, callback=cb)
        if self._device_index is not None: kwargs['device']=self._device_index
        with sd.RawInputStream(**kwargs):
            start=time.time()
            while (time.time()-start)<max_sec and result_text is None:
                time.sleep(0.05)
            if result_text is None:
                try: result_text=_extract_text(rec.FinalResult()) or None
                except Exception: pass
        print('[ASR] Heard:', result_text or '(none)')
        return result_text

def _extract_text(j:str)->str:
    try:
        import json; return (json.loads(j).get('text') or '').strip().lower()
    except Exception:
        return ''

# -------- time parsing --------
_ABS_AT_RE = re.compile(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", re.I)
_REL_IN_RE = re.compile(r"\b(?:in|after)\s+(.*)", re.I)
WORDNUM={'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'twenty':20,'thirty':30,'forty':40,'fifty':50}

def parse_time_expr(utter:str):
    utter=(utter or '').strip().lower()
    if not utter: return None,None
    now=now_tz()
    m=_REL_IN_RE.search(utter)
    if m:
        seconds=_parse_rel(m.group(1).strip())
        if seconds: seconds=clamp_delay(seconds); return now+timedelta(seconds=seconds), humanize_delta(seconds)
    # bare relative like "one minute"
    bare=_parse_rel(utter)
    if bare:
        bare=clamp_delay(bare); return now+timedelta(seconds=bare), humanize_delta(bare)
    m=_ABS_AT_RE.search(utter)
    if m:
        hh=int(m.group(1)); mm=int(m.group(2)) if m.group(2) else 0; ampm=(m.group(3) or '').lower()
        if ampm=='pm' and hh!=12: hh+=12
        if ampm=='am' and hh==12: hh=0
        cand=now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if cand <= now + timedelta(seconds=1): cand += timedelta(days=1)
        delta=int((cand-now).total_seconds()); delta=clamp_delay(delta)
        return cand, humanize_delta(delta)
    if dateparser is not None:
        settings={'PREFER_DATES_FROM':'future','RELATIVE_BASE':now}
        tz_name = os.getenv('TZ') or (LOCAL_TZ_NAME if LOCAL_TZ else None)
        if tz_name:
            settings['RETURN_AS_TIMEZONE_AWARE']=True; settings['TIMEZONE']=tz_name
        dp=dateparser.parse(utter, languages=['en'], settings=settings)
        if dp:
            if LOCAL_TZ and dp.tzinfo is None: dp=dp.replace(tzinfo=LOCAL_TZ)
            delta=int((dp-now).total_seconds());
            if delta<=0: dp=now+timedelta(seconds=MIN_DELAY_SEC); delta=MIN_DELAY_SEC
            delta=clamp_delay(delta); return dp, humanize_delta(delta)
    return None,None

def _parse_rel(text:str)->int|None:
    t=text.replace('seconds','sec').replace('second','sec'); t=t.replace('minutes','min').replace('minute','min'); t=t.replace('hours','h').replace('hour','h')
    p=re.compile(r"(\d+)\s*(h|hr|hrs|min|m|sec|s)\b", re.I)
    total=0; found=False
    for n,u in p.findall(t):
        n=int(n); u=u.lower()
        if u in ('h','hr','hrs'): total+=n*3600
        elif u in ('min','m'): total+=n*60
        elif u in ('sec','s'): total+=n
        found=True
    if found and total>0: return total
    m=re.search(r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|twenty|thirty|forty|fifty)\s+(seconds?|minutes?|hours?)\b", text)
    if m:
        n=WORDNUM.get(m.group(1),0); u=m.group(2)
        if u.startswith('hour'): return n*3600
        if u.startswith('minute'): return n*60
        if u.startswith('second'): return n
    return None

# -------- buttons --------
class ButtonDriver:
    def __init__(self,on_top,on_bottom):
        self.on_top=on_top; self.on_bottom=on_bottom
        forced=BUTTON_BACKEND in ('gpio','evdev','keyboard')
        if BUTTON_BACKEND=='gpio' or (not forced and self._try_gpio()): return
        if BUTTON_BACKEND=='evdev' or (not forced and self._try_evdev()): return
        print("[GPIO] Keyboard fallback: t=TOP, b=BOTTOM, q=quit")
        th=threading.Thread(target=self._keyboard_loop,daemon=True); th.start()
    def _try_gpio(self)->bool:
        if Button is None: return False
        try:
            self._btn_top=Button(TOP_BUTTON_PIN,pull_up=True,bounce_time=BUTTON_DEBOUNCE_S)
            self._btn_bottom=Button(BOTTOM_BUTTON_PIN,pull_up=True,bounce_time=BUTTON_DEBOUNCE_S)
            self._btn_top.when_pressed=lambda: self.on_top()
            self._btn_bottom.when_pressed=lambda: self.on_bottom()
            print(f"[GPIO] Using gpiozero TOP={TOP_BUTTON_PIN} BOTTOM={BOTTOM_BUTTON_PIN}")
            return True
        except Exception as e:
            print('[GPIO] gpiozero init failed:', e); return False
    def _try_evdev(self)->bool:
        if not _EVDEV: return False
        paths=list_devices();
        if not paths: return False
        print('[GPIO] Using evdev devices:', paths)
        def reader(p):
            try:
                dev=InputDevice(p)
                for ev in dev.read_loop():
                    if ev.type==ecodes.EV_KEY and ev.value==1:
                        if ev.code in (ecodes.KEY_UP,ecodes.KEY_ENTER,ecodes.KEY_VOLUMEUP,ecodes.KEY_KPENTER): self.on_top()
                        elif ev.code in (ecodes.KEY_DOWN,ecodes.KEY_VOLUMEDOWN,ecodes.KEY_PAGEDOWN,ecodes.KEY_NEXT): self.on_bottom()
            except Exception as e:
                print('[EVDEV] reader error:', e)
        for p in paths: threading.Thread(target=reader,args=(p,),daemon=True).start()
        return True
    def _keyboard_loop(self):
        try:
            import termios, tty
            fd=sys.stdin.fileno(); old=termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                while True:
                    ch=sys.stdin.read(1)
                    if ch=='t': self.on_top()
                    elif ch=='b': self.on_bottom()
                    elif ch=='q': os._exit(0)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            while True:
                s=input().strip().lower()
                if s=='t': self.on_top()
                elif s=='b': self.on_bottom()
                elif s=='q': os._exit(0)

# -------- core assistant --------
class Assistant:
    IDLE='IDLE'; AWAIT_TIME='AWAIT_TIME'; SCHEDULED='SCHEDULED'; RINGING='RINGING'; SNOOZE='SNOOZE'
    def __init__(self):
        self.display=Display(); self.speaker=Speaker()
        self.listener=Listener(MODEL_DIR) if _ASR_AVAILABLE and os.path.isdir(MODEL_DIR) else None
        self.state=self.IDLE
        self.event_q: queue.Queue[tuple[str, object | None]] = queue.Queue()
        self.schedule_dt=None
        self._ring_deadline=None
        self._reprompt=0
        self._countdown_thread=None
        self._countdown_stop=threading.Event()
        self.buttons=ButtonDriver(self._on_top,self._on_bottom)

    def run(self):
        print('=== Medication Voice Assistant (v3-final) ===')
        print('WORKDIR:', WORKDIR)
        print('Vosk model:', MODEL_DIR, '(ok)' if os.path.isdir(MODEL_DIR) else '(missing)')
        print('Display enabled:', self.display.available, ' ASR:', bool(self.listener))
        print('---------------------------------------')
        self.display.show_idle(); print('[STATE] IDLE - waiting for TOP button')
        try:
            while True:
                try:
                    evt, data = self.event_q.get(timeout=0.2)
                except queue.Empty:
                    if self.state==self.RINGING and self._ring_deadline and time.time()>=self._ring_deadline:
                        self._ring_deadline=None; self.event_q.put(('WINDOW_TIMEOUT', None))
                    continue
                if evt=='BTN_TOP': self._on_top()
                elif evt=='BTN_BOTTOM': self._on_bottom()
                elif evt=='TIME_REACHED': self._on_time_reached()
                elif evt=='WINDOW_TIMEOUT': self._on_window_timeout()
                elif evt=='SNOOZE_TIMEOUT': self._on_snooze_timeout()
        except KeyboardInterrupt:
            print('\n[EXIT] KeyboardInterrupt')

    # ---------- event handlers ----------
    def _on_top(self):
        if self.state==self.IDLE:
            self.speaker.say('Starting a new medication plan. When should I remind you?')
            self.display.show_listening(); self.state=self.AWAIT_TIME; self._reprompt=0
            self._capture_and_schedule()
        elif self.state==self.RINGING:
            self.speaker.say('Okay, I will remind you again in 30 seconds.')
            self.display.show_snoozed(); self.state=self.SNOOZE
            threading.Thread(target=lambda:(time.sleep(SNOOZE_SEC), self.event_q.put(('SNOOZE_TIMEOUT', None))), daemon=True).start()

    def _on_bottom(self):
        if self.state==self.RINGING:
            self.speaker.say('Good job. Finished!')
            self.display.show_finished(); self.schedule_dt=None
            self._stop_countdown()
            self.state=self.IDLE; self.display.show_idle()

    def _on_time_reached(self):
        if self.state==self.SCHEDULED:
            self._stop_countdown()
            self.display.show_ringing(); self.speaker.say("It's time to take your medicine.")
            self._ring_deadline=time.time()+RING_WINDOW_SEC; self.state=self.RINGING

    def _on_window_timeout(self):
        if self.state==self.RINGING:
            self.state=self.SNOOZE
            threading.Thread(target=lambda:(time.sleep(SNOOZE_SEC), self.event_q.put(('SNOOZE_TIMEOUT', None))), daemon=True).start()

    def _on_snooze_timeout(self):
        if self.state==self.SNOOZE:
            self.display.show_ringing(); self.speaker.say("It's time to take your medicine.")
            self._ring_deadline=time.time()+RING_WINDOW_SEC; self.state=self.RINGING

    # ---------- scheduling ----------
    def _capture_and_schedule(self):
        if self.listener is not None:
            utter=self.listener.listen(max_sec=ASR_LISTEN_WINDOW_SEC)
        else:
            try: utter=input("[INPUT] Type time (e.g., 'in 3 minutes'): ").strip()
            except EOFError: utter=None
        dt, delta = parse_time_expr(utter or '')
        if dt is None:
            self._reprompt+=1
            if self._reprompt<=1:
                self.speaker.say("Sorry, I didn't catch the time. Please say it again.")
                self.display.show_listening()
                if self.listener is not None: utter=self.listener.listen(max_sec=ASR_LISTEN_WINDOW_SEC)
                else:
                    try: utter=input('[INPUT] Type time again: ').strip()
                    except EOFError: utter=None
                dt, delta = parse_time_expr(utter or '')
            if dt is None:
                self.speaker.say("I still couldn't parse that time. Let's try again later.")
                self.display.show_error('Parse failed'); time.sleep(1.0)
                self.display.show_idle(); self.state=self.IDLE; return
        self.schedule_dt=dt
        if re.search(r"\b(in|after)\b", (utter or ''), re.I) or _parse_rel(utter or ''):
            self.speaker.say(f"Got it. I will remind you in {delta}.")
        else:
            at_str = dt.astimezone(LOCAL_TZ).strftime('%I:%M %p').lstrip('0') if (LOCAL_TZ and dt.tzinfo) else dt.strftime('%H:%M')
            self.speaker.say(f"Got it. I will remind you at {at_str}.")
        self.display.show_scheduled(dt); self.state=self.SCHEDULED
        self._start_schedule_waiter(); self._start_countdown()

    def _start_schedule_waiter(self):
        target=self.schedule_dt
        if not target: return
        def waiter():
            while True:
                if self.state!=self.SCHEDULED: return
                if now_tz() >= target:
                    self.event_q.put(('TIME_REACHED', None)); return
                time.sleep(0.2)
        threading.Thread(target=waiter, daemon=True).start()

    # live countdown thread
    def _start_countdown(self):
        if not self.display.available or not self.schedule_dt: return
        self._stop_countdown()
        self._countdown_stop.clear()
        target=self.schedule_dt
        def tick():
            # update at ~10 Hz to look smooth, but draw only once per second boundary
            last_sec=-1
            while (not self._countdown_stop.is_set()) and self.state==self.SCHEDULED:
                remaining = max(0, int((target - now_tz()).total_seconds()))
                if remaining!=last_sec:
                    self.display.show_countdown(target)
                    last_sec=remaining
                time.sleep(0.1)
        self._countdown_thread=threading.Thread(target=tick, daemon=True); self._countdown_thread.start()

    def _stop_countdown(self):
        self._countdown_stop.set()
        self._countdown_thread=None

# -------- helpers --------

def _is_relative(utter:str|None)->bool:
    if not utter: return False
    return bool(re.search(r"\b(in|after)\b", utter, re.I))

# -------- main --------
if __name__=='__main__':
    print('=== Medication Voice Assistant ===')
    print('WORKDIR:', WORKDIR)
    print('Vosk model:', MODEL_DIR, '(ok)' if os.path.isdir(MODEL_DIR) else '(missing)')
    print('Display available:', _DISPLAY_AVAILABLE)
    print('ASR available:', _ASR_AVAILABLE)
    print('GPIO pins (gpio backend): TOP=', TOP_BUTTON_PIN, ' BOTTOM=', BOTTOM_BUTTON_PIN)
    print('----------------------------------')
    app=Assistant(); app.run()
