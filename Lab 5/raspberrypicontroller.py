"""
Sphero Ollie & BB-8 Controller (RPI)

- Records wall-clock receive time for each instruction (SSE/UDP) with channel tag.
- Computes per-step and cross-host deltas (ms):
    pc_pipeline_ms (from PC), pc->pi network, recv->apply, apply->ble,
    cap->recv, cap->apply, cap->ble.
- Rolling 10s averages dumped to controller_metrics.jsonl
- RobotWorker accepts (seq, apply_ts, pc_cap_ts) to attribute BLE write timing to the correct instruction.
"""

import json
import logging
import math
import threading
import time
import inspect
import os
import shutil
import subprocess
import socket
from dataclasses import dataclass
from typing import Optional, Tuple
from collections import defaultdict

import tkinter as tk
from tkinter import ttk
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.scanner import ToyNotFoundError
from spherov2.types import Color

# Event type (collision) — try a couple of locations (lib variants)
try:
    from spherov2.sphero_edu import EventType
except Exception:
    try:
        from spherov2.types import EventType
    except Exception:
        EventType = None

# ---------------------------- Metrics --------------------------------------- #

class RollingMetrics:
    """
    Thread-safe rolling 10s averages dumped to JSONL.
    On this Pi we derive cross-host deltas using wall clock times attached by the PC.
    """
    def __init__(self, path: str, window_s: float = 10.0):
        self.path = path
        self.window_s = window_s
        self._lock = threading.Lock()
        self._sums = defaultdict(float)   # metric -> sum(ms)
        self._counts = defaultdict(int)   # metric -> count
        self._counters = defaultdict(int) # counter name -> count
        self._chan_counts = defaultdict(int)  # 'udp'/'sse'
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._flush()

    def add_sample(self, name: str, value_ms: float):
        if value_ms is None:
            return
        with self._lock:
            self._sums[name] += float(value_ms)
            self._counts[name] += 1

    def incr_counter(self, name: str, inc: int = 1):
        with self._lock:
            self._counters[name] += inc

    def incr_channel(self, chan: str, inc: int = 1):
        with self._lock:
            self._chan_counts[chan] += inc

    def _loop(self):
        next_t = time.time() + self.window_s
        while not self._stop.is_set():
            now = time.time()
            if now >= next_t:
                self._flush()
                next_t = now + self.window_s
            time.sleep(0.2)

    def _flush(self):
        with self._lock:
            if not self._counts and not self._counters and not self._chan_counts:
                return
            avg = {}
            for k, s in self._sums.items():
                c = max(1, self._counts.get(k, 0))
                if self._counts.get(k, 0) == 0:
                    continue
                avg[k] = s / c

            chan_share = {}
            total_chan = sum(self._chan_counts.values()) or 1
            for k, v in self._chan_counts.items():
                chan_share[k] = v / total_chan

            out = {
                "ts": time.time(),
                "window_s": self.window_s,
                "avg_ms": avg,
                "counts": dict(self._counters),
                "channel_share": chan_share,
            }
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(out, separators=(",", ":")) + "\n")
            except Exception:
                pass
            # reset window
            self._sums.clear()
            self._counts.clear()
            self._counters.clear()
            self._chan_counts.clear()

# Global metrics (file path overridable via env)
METRICS_PATH = os.environ.get("CONTROLLER_METRICS_FILE", "controller_metrics.jsonl")
METRICS = RollingMetrics(METRICS_PATH, window_s=10.0)

# ---------------------------- Bluetooth Helpers ----------------------------- #

def _run_cmd(args) -> Tuple[int, str]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, check=False)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 127, str(e)

def _bluetooth_status(log: Optional[logging.Logger] = None):
    info = {
        "present": False,
        "powered": False,
        "soft_blocked": False,
        "hard_blocked": False,
        "service_active": False,
        "controller": None,
    }
    _, out = _run_cmd(["systemctl", "is-active", "bluetooth"])
    info["service_active"] = (out.strip() == "active")
    btctl = shutil.which("bluetoothctl")
    if not btctl:
        if log:
            log.error("bluetoothctl not found; install BlueZ.")
        return info
    _, out = _run_cmd([btctl, "show"])
    if "Controller" in out:
        info["present"] = True
        for line in out.splitlines():
            if line.strip().startswith("Controller "):
                info["controller"] = line.strip().split(" ", 2)[1]
            if line.strip().startswith("Powered:"):
                powered_val = line.split(":", 1)[1].strip().lower()
                info["powered"] = (powered_val == "yes")
    else:
        info["present"] = False
    rfkill = shutil.which("rfkill")
    if rfkill:
        _, r = _run_cmd([rfkill, "list", "bluetooth"])
        if "Soft blocked: yes" in r:
            info["soft_blocked"] = True
        if "Hard blocked: yes" in r:
            info["hard_blocked"] = True
    return info

def ensure_bluetooth_powered(log: logging.Logger, attempt_fix: bool = True) -> Tuple[bool, str]:
    st = _bluetooth_status(log)
    if st["present"] and st["powered"]:
        return True, "Bluetooth adapter present and powered."
    btctl = shutil.which("bluetoothctl")
    hint_lines = []
    if not st["service_active"]:
        hint_lines.append("bluetoothd is not active; run: sudo systemctl start bluetooth")
    if st["soft_blocked"] or st["hard_blocked"]:
        hint_lines.append("Bluetooth is rfkill blocked; run: sudo rfkill unblock bluetooth")
    if not st["present"]:
        hint_lines.append("No Bluetooth controller detected by bluetoothctl.")
    if btctl is None:
        hint_lines.append("Install BlueZ tools: sudo apt install bluez bluetooth pi-bluetooth")
        return False, " | ".join(hint_lines) if hint_lines else "BlueZ tools missing."
    if attempt_fix:
        _run_cmd([btctl, "power", "on"])
        rfkill = shutil.which("rfkill")
        if rfkill and (st["soft_blocked"] or st["hard_blocked"]):
            _run_cmd([rfkill, "unblock", "bluetooth"])
        st2 = _bluetooth_status(log)
        if st2["present"] and st2["powered"]:
            return True, "Bluetooth adapter is now powered."
    if not hint_lines:
        hint_lines.append("Adapter is off; try: bluetoothctl power on")
    return False, " | ".join(hint_lines)

# ---------------------------- Logging to Tk Text ---------------------------- #

class TkTextHandler(logging.Handler):
    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.configure(state="disabled")
    def emit(self, record):
        msg = self.format(record) + "\n"
        def write():
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", msg)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        self.text_widget.after(0, write)

# ---------------------------- Robot Worker Thread --------------------------- #

@dataclass
class DriveStateAbs:
    heading: Optional[int] = None
    speed: int = 0

@dataclass
class DriveStateRel:
    rel_heading: int = 0
    speed: int = 0

class RobotWorker:
    """
    Maintains BLE connection & streams drive commands.
    Low-latency tick = 0.025s (40 Hz).

    Metrics hook:
    - set_desired_relative(rel, speed, seq=None, apply_ts=None, pc_cap_ts=None)
      stores seq + timestamps for attributing BLE write to that instruction.
    """
    def __init__(self, name: str, find_func, status_callback, log: logging.Logger):
        self.name = name
        self.find_func = find_func
        self.status_callback = status_callback
        self.log = log
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._connected = threading.Event()
        self._toy_name: Optional[str] = None

        # Desired states
        self._abs_desired = DriveStateAbs()
        self._rel_desired = DriveStateRel()
        self._control_mode = "ABS"  # "ABS" or "REL"
        self._reverse_mode = False

        # Last sent absolute
        self._last_sent = DriveStateAbs(heading=None, speed=-1)

        # Rolling & heading bookkeeping
        self._use_roll = False
        self._roll_needs_duration = False
        self._last_roll_keepalive_ts = 0.0
        self._roll_keepalive_period = 0.25
        self._roll_duration = 0.40

        # Heading estimate (absolute)
        self._abs_heading_est: int = 0
        self._last_heading_poll_ts = 0.0
        self._heading_poll_period = 0.25

        # rotate helper
        self._rotate_delta: Optional[threading.Event] = None
        self._rotate_value: int = 0

        # collision recovery
        self._recover_request = False
        self._recovering = False
        self._recovery_speed = 120
        self._recovery_duration = 0.5
        self._recovery_rotate = 60

        self._lock = threading.Lock()

        # Metrics linkage for current instruction
        self._m_seq: Optional[int] = None
        self._m_apply_ts: Optional[float] = None
        self._m_pc_cap_ts: Optional[float] = None
        self._m_ble_recorded: bool = False

    # lifecycle & connection omitted (unchanged patterns) ---------------------

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def is_connected(self) -> bool:
        return self._connected.is_set()

    def connect(self, toy_name: Optional[str] = None, timeout: float = 8.0):
        if self.is_running():
            self.log.info("%s: already running.", self.name)
            return
        self._toy_name = toy_name or None
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, args=(timeout,), daemon=True)
        self._thread.start()

    def disconnect(self):
        if not self.is_running():
            return
        self._stop.set()
        self._thread.join(timeout=5)
        if self._thread.is_alive():
            self.log.warning("%s: worker didn't stop cleanly.", self.name)
        self._thread = None

    # commands from UI/SSE/UDP -----------------------------------------------

    def set_desired_absolute(self, heading: Optional[int], speed: int):
        with self._lock:
            if heading is not None:
                self._abs_desired.heading = int(heading) % 360
            self._abs_desired.speed = max(0, min(255, int(speed)))
            self._control_mode = "ABS"

    def set_desired(self, heading: Optional[int], speed: int):
        self.set_desired_absolute(heading, speed)

    def set_desired_relative(self, rel_heading: int, speed: int,
                             seq: Optional[int] = None,
                             apply_ts: Optional[float] = None,
                             pc_cap_ts: Optional[float] = None):
        with self._lock:
            self._rel_desired.rel_heading = int(rel_heading) % 360
            self._rel_desired.speed = max(0, min(255, int(speed)))
            self._control_mode = "REL"
            # Metrics linkage
            if seq is not None:
                if seq != self._m_seq:
                    self._m_ble_recorded = False
                self._m_seq = seq
                self._m_apply_ts = apply_ts
                self._m_pc_cap_ts = pc_cap_ts

    def stop_now(self):
        with self._lock:
            if self._control_mode == "ABS":
                self._abs_desired.speed = 0
            else:
                self._rel_desired.speed = 0

    def rotate_by(self, delta_deg: int):
        with self._lock:
            if self._rotate_delta is None:
                self._rotate_delta = threading.Event()
            self._rotate_value = int(delta_deg)
            self._rotate_delta.set()

    def set_reverse_mode(self, enabled: bool):
        with self._lock:
            self._reverse_mode = bool(enabled)

    # internals ---------------------------------------------------------------

    def _post_status(self, text: str):
        self.status_callback(text)

    def _enqueue_collision(self):
        with self._lock:
            self._recover_request = True

    def _run_loop(self, timeout: float):
        # Bluetooth check
        self._post_status("Checking Bluetooth…")
        ok, hint = ensure_bluetooth_powered(self.log, attempt_fix=True)
        if not ok:
            self._post_status(f"Bluetooth not ready: {hint}")
            self.log.error("%s: Bluetooth not ready: %s", self.name, hint)
            return

        self._post_status("Scanning…")
        self.log.info("%s: scanning (filter=%s, timeout=%.1fs)", self.name, self._toy_name, timeout)
        toy = None
        try:
            toy = self.find_func(toy_name=self._toy_name, timeout=timeout)
        except ToyNotFoundError:
            self._post_status("Not found")
            self.log.error("%s: toy not found.", self.name)
            return
        except Exception as e:
            self._post_status(f"Scan error: {e}")
            self.log.exception("%s: scan error", self.name)
            return

        self._post_status("Connecting…")
        try:
            with SpheroEduAPI(toy) as api:
                # roll capability detection
                roll_func = getattr(api, "roll", None)
                if callable(roll_func):
                    try:
                        sig = inspect.signature(roll_func)
                        self._use_roll = True
                        self._roll_needs_duration = "duration" in sig.parameters
                    except Exception:
                        self._use_roll = True
                        self._roll_needs_duration = True
                else:
                    self._use_roll = False
                    self._roll_needs_duration = False

                self._connected.set()
                safe_name = getattr(toy, "name", None) or self.name
                self._post_status(f"Connected ({safe_name}) | roll={self._use_roll} dur={self._roll_needs_duration}")
                self.log.info("%s: connected to %s", self.name, safe_name)

                try:
                    api.set_stabilization(True)
                except Exception:
                    pass
                try:
                    api.set_main_led(Color(0, 80, 255))
                    api.set_speed(0)
                except Exception:
                    self.log.debug("%s: initial LED/speed set failed.", self.name)

                if EventType is not None:
                    try:
                        def _on_collision(api_obj):
                            self.log.info("%s: collision detected", self.name)
                            self._enqueue_collision()
                        api.register_event(EventType.on_collision, _on_collision)
                    except Exception as e:
                        self.log.debug("%s: event register failed: %s", self.name, e)

                tick = 0.025  # 40 Hz
                while not self._stop.is_set():
                    now = time.time()

                    if now - self._last_heading_poll_ts >= self._heading_poll_period:
                        try:
                            self._abs_heading_est = int(api.get_heading()) % 360
                        except Exception:
                            pass
                        self._last_heading_poll_ts = now

                    # Handle queued rotate
                    rotate_evt = None
                    rotate_val = 0
                    with self._lock:
                        if self._rotate_delta is not None and self._rotate_delta.is_set():
                            rotate_evt = self._rotate_delta
                            rotate_val = self._rotate_value
                            self._rotate_delta = None
                    if rotate_evt is not None:
                        try:
                            cur = self._abs_heading_est
                            new_heading = (int(cur) + int(rotate_val)) % 360
                            api.set_heading(new_heading)
                            self._last_sent.heading = new_heading
                            self._abs_heading_est = new_heading
                            self.log.info("%s: rotate_by %d° -> heading=%d", self.name, rotate_val, new_heading)
                        except Exception as e:
                            self.log.error("%s: rotate_by error: %s", self.name, e)

                    # Collision recovery
                    with self._lock:
                        do_recover = self._recover_request and not self._recovering
                        if do_recover:
                            self._recover_request = False
                            self._recovering = True
                    if do_recover:
                        try:
                            self._do_collision_recovery(api)
                        finally:
                            self._recovering = False
                        continue

                    # Build command from mode
                    with self._lock:
                        mode = self._control_mode
                        reverse = self._reverse_mode
                        if mode == "ABS":
                            desired_speed = self._abs_desired.speed
                            cmd_heading_abs = self._abs_desired.heading if self._abs_desired.heading is not None else (self._last_sent.heading or 0)
                        else:  # REL
                            desired_speed = self._rel_desired.speed
                            rel = self._rel_desired.rel_heading
                            base = self._abs_heading_est
                            cmd_heading_abs = (base + rel) % 360
                        if reverse:
                            cmd_heading_abs = (cmd_heading_abs + 180) % 360

                    allow_heading_update = desired_speed > 0
                    changed_heading = (self._last_sent.heading is None) or (self._delta_deg(self._last_sent.heading, cmd_heading_abs) >= 1)
                    changed_speed = (self._last_sent.speed != desired_speed)

                    try:
                        did_send = False
                        if self._use_roll and self._roll_needs_duration:
                            need_send = (changed_speed or (allow_heading_update and changed_heading)
                                         or (now - self._last_roll_keepalive_ts > self._roll_keepalive_period))
                            if need_send:
                                api.roll(int(cmd_heading_abs), int(desired_speed), float(self._roll_duration))
                                self._last_sent.heading = int(cmd_heading_abs)
                                self._last_sent.speed = int(desired_speed)
                                self._last_roll_keepalive_ts = now
                                did_send = True
                        elif self._use_roll and not self._roll_needs_duration:
                            if changed_speed or (allow_heading_update and changed_heading):
                                api.roll(int(cmd_heading_abs), int(desired_speed))
                                self._last_sent.heading = int(cmd_heading_abs)
                                self._last_sent.speed = int(desired_speed)
                                did_send = True
                        else:
                            if allow_heading_update and changed_heading:
                                api.set_heading(int(cmd_heading_abs))
                                self._last_sent.heading = int(cmd_heading_abs)
                                did_send = True
                            if changed_speed or (allow_heading_update and changed_heading):
                                api.set_speed(int(desired_speed))
                                self._last_sent.speed = int(desired_speed)
                                did_send = True

                        # Metrics: first BLE write for current seq
                        if did_send:
                            with self._lock:
                                if self._m_seq is not None and not self._m_ble_recorded and self._m_apply_ts is not None:
                                    ble_ts = time.time()
                                    METRICS.incr_counter("ble_writes", 1)
                                    METRICS.add_sample("apply_to_ble_ms", (ble_ts - self._m_apply_ts) * 1000.0)
                                    if self._m_pc_cap_ts:
                                        METRICS.add_sample("cap_to_ble_ms", (ble_ts - self._m_pc_cap_ts) * 1000.0)
                                    self._m_ble_recorded = True

                    except TypeError as te:
                        self.log.warning("%s: roll signature mismatch (%s); fallback.", self.name, te)
                        self._use_roll = False
                        continue
                    except Exception as e:
                        self.log.error("%s: drive error: %s", self.name, e)
                        break

                    time.sleep(tick)

                # Stop gracefully
                try:
                    api.stop_roll()
                    api.set_speed(0)
                except Exception:
                    pass
        except Exception as e:
            self._post_status(f"Error: {e}")
            self.log.exception("%s: error maintaining connection", self.name)
        finally:
            self._connected.clear()
            self._post_status("Disconnected")
            self.log.info("%s: disconnected", self.name)

    def _do_collision_recovery(self, api: SpheroEduAPI):
        try:
            cur = self._abs_heading_est
            back = (cur + 180) % 360
            if self._use_roll and self._roll_needs_duration:
                api.roll(int(back), int(self._recovery_speed), float(self._recovery_duration))
            elif self._use_roll:
                api.roll(int(back), int(self._recovery_speed))
                time.sleep(self._recovery_duration)
            else:
                api.set_heading(int(back))
                api.set_speed(int(self._recovery_speed))
                time.sleep(self._recovery_duration)
            try:
                api.set_speed(0)
            except Exception:
                pass
            turn = (cur + self._recovery_rotate) % 360
            try:
                api.set_heading(int(turn))
                self._last_sent.heading = int(turn)
                self._abs_heading_est = int(turn)
            except Exception:
                pass
            try:
                api.set_speed(0)
                self._last_sent.speed = 0
            except Exception:
                pass
        except Exception as e:
            self.log.error("%s: recovery failed: %s", self.name, e)

    @staticmethod
    def _delta_deg(a: int, b: int) -> float:
        d = (b - a + 180) % 360 - 180
        return abs(d)

# ---------------------------- SSE (instruction) Client ---------------------- #

class SseClient:
    """
    Minimal SSE client using urllib (no extra deps).
    Parses line-by-line to avoid buffering; calls on_control(dict).
    """
    def __init__(self, base_url: str, on_control, status_callback, logger: logging.Logger, reconnect_initial=0.8):
        self.base = base_url.rstrip("/")
        self.url = f"{self.base}/events"
        self.on_control = on_control
        self.on_status = status_callback
        self.log = logger
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._connected = False
        self._lock = threading.Lock()
        self._backoff = reconnect_initial

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._thread = None

    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    def _set_connected(self, val: bool):
        with self._lock:
            self._connected = val

    def _run(self):
        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "Controller/1.0",
            "Connection": "keep-alive",
        }
        while not self._stop.is_set():
            try:
                self.on_status("Connecting…")
                req = Request(self.url, headers=headers, method="GET")
                with urlopen(req, timeout=30) as resp:
                    ct = resp.headers.get("Content-Type", "")
                    if "text/event-stream" not in ct:
                        self.log.warning("SSE: unexpected content-type: %r", ct)
                    self._backoff = 0.8
                    self._set_connected(True)
                    self.on_status("Connected")

                    event_name = "message"
                    data_lines = []
                    while not self._stop.is_set():
                        line = resp.readline()
                        if not line:
                            raise EOFError("SSE stream ended")
                        s = line.decode("utf-8", "replace").rstrip("\r\n")
                        if s.startswith(":"):
                            continue
                        if s.startswith("event:"):
                            event_name = s[6:].strip() or "message"
                            continue
                        if s.startswith("data:"):
                            data_lines.append(s[5:].lstrip())
                            continue
                        if s == "":
                            if event_name == "control" and data_lines:
                                raw = "\n".join(data_lines)
                                data_lines.clear()
                                try:
                                    obj = json.loads(raw)
                                    obj["_arrival"] = time.time()
                                    obj["rpi_recv_ts"] = obj["_arrival"]
                                    obj["chan"] = "sse"
                                    METRICS.incr_counter("instr_recv", 1)
                                    METRICS.incr_channel("sse", 1)
                                    # Cross-host deltas when available
                                    pc_send = obj.get("pc_send_ts")
                                    pc_cap = obj.get("pc_cap_ts")
                                    pc_pipe = obj.get("pc_cap_to_send_ms")
                                    if isinstance(pc_pipe, (int, float)):
                                        METRICS.add_sample("pc_pipeline_ms", float(pc_pipe))
                                    if isinstance(pc_send, (int, float)):
                                        METRICS.add_sample("net_pc_to_pi_ms", (obj["rpi_recv_ts"] - pc_send) * 1000.0)
                                    if isinstance(pc_cap, (int, float)):
                                        METRICS.add_sample("cap_to_recv_ms", (obj["rpi_recv_ts"] - pc_cap) * 1000.0)
                                    self.on_control(obj)
                                except Exception as e:
                                    self.log.debug("SSE: bad control data: %s", e)
                            else:
                                data_lines.clear()
                                event_name = "message"

            except (URLError, HTTPError, TimeoutError, ConnectionResetError, EOFError) as e:
                if self._stop.is_set():
                    break
                self._set_connected(False)
                self.on_status(f"Reconnecting in {self._backoff:.1f}s… ({e})")
                time.sleep(self._backoff)
                self._backoff = min(5.0, self._backoff * 1.7)
            except Exception as e:
                if self._stop.is_set():
                    break
                self._set_connected(False)
                self.on_status(f"Error: {e!s} — reconnecting in {self._backoff:.1f}s…")
                time.sleep(self._backoff)
                self._backoff = min(5.0, self._backoff * 1.7)
            finally:
                self._set_connected(False)

# ---------------------------- UDP Fast Path Receiver ------------------------ #

class UdpReceiver:
    """
    Listens for JSON lines from the PC; now includes timing/seq.
    """
    def __init__(self, host: str, port: int, on_packet, logger: logging.Logger):
        self.host = host
        self.port = port
        self.on_packet = on_packet
        self.log = logger
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.log.info("UDP: listening on %s:%d", self.host, self.port)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self._thread = None

    def _run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.settimeout(0.2)
            while not self._stop.is_set():
                try:
                    data, _addr = sock.recvfrom(2048)
                except socket.timeout:
                    continue
                except Exception:
                    break
                try:
                    s = data.decode("utf-8", "replace").strip()
                    if not s:
                        continue
                    obj = json.loads(s)
                    obj["_arrival"] = time.time()
                    obj["rpi_recv_ts"] = obj["_arrival"]
                    obj["chan"] = "udp"
                    METRICS.incr_counter("instr_recv", 1)
                    METRICS.incr_channel("udp", 1)
                    pc_send = obj.get("pc_send_ts")
                    pc_cap = obj.get("pc_cap_ts")
                    pc_pipe = obj.get("pc_cap_to_send_ms")
                    if isinstance(pc_pipe, (int, float)):
                        METRICS.add_sample("pc_pipeline_ms", float(pc_pipe))
                    if isinstance(pc_send, (int, float)):
                        METRICS.add_sample("net_pc_to_pi_ms", (obj["rpi_recv_ts"] - pc_send) * 1000.0)
                    if isinstance(pc_cap, (int, float)):
                        METRICS.add_sample("cap_to_recv_ms", (obj["rpi_recv_ts"] - pc_cap) * 1000.0)
                    self.on_packet(obj)
                except Exception:
                    continue
        finally:
            try:
                sock.close()
            except Exception:
                pass

# ---------------------------- GUI Application (no video) -------------------- #

class JoystickCanvas(tk.Canvas):
    def __init__(self, master, radius=140, knob_radius=16, **kwargs):
        size = radius * 2 + 12
        super().__init__(master, width=size, height=size, bg="#101418", highlightthickness=0, **kwargs)
        self.radius = radius
        self.knob_r = knob_radius
        self.center = (size // 2, size // 2)
        self.knob_pos = list(self.center)
        self._dragging = False
        self._draw_static()
        self._draw_knob(*self.center)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw_static(self):
        cx, cy = self.center
        r = self.radius
        self.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#3a3f45", width=3)
        self.create_line(cx - r, cy, cx + r, cy, fill="#2a2f35")
        self.create_line(cx, cy - r, cx, cy + r, fill="#2a2f35")

    def _draw_knob(self, x, y):
        if hasattr(self, "_knob_id"):
            self.delete(self._knob_id)
        self._knob_id = self.create_oval(x - self.knob_r, y - self.knob_r, x + self.knob_r, y + self.knob_r,
                                         fill="#28a0ff", outline="#cfe9ff", width=2)

    def _on_press(self, e):
        self._dragging = True
        self._move_knob(e.x, e.y)

    def _on_drag(self, e):
        if self._dragging:
            self._move_knob(e.x, e.y)

    def _on_release(self, _e):
        self._dragging = False

    def _move_knob(self, x, y):
        cx, cy = self.center
        dx, dy = x - cx, y - cy
        dist = math.hypot(dx, dy)
        if dist > self.radius:
            scale = self.radius / dist
            dx *= scale; dy *= scale
            x, y = int(cx + dx), int(cy + dy)
        self.knob_pos = [x, y]
        self._draw_knob(x, y)

    def reset(self):
        self.knob_pos = list(self.center)
        self._draw_knob(*self.center)

    def pose(self) -> Tuple[int, float]:
        cx, cy = self.center
        x, y = self.knob_pos
        vx, vy = (x - cx), (cy - y)
        mag = max(0.0, min(1.0, math.hypot(vx, vy) / self.radius))
        if mag < 0.02:
            return 0, 0.0
        heading = int((math.degrees(math.atan2(vx, vy)) + 360) % 360)
        return heading, mag

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sphero Controller — Manual + SSE/UDP Autonomous (Raspberry Pi 5) + Metrics")
        self.configure(bg="#0b0f13")
        try:
            self.tk.call('tk', 'scaling', 1.25)
        except Exception:
            pass

        # Logging
        self.logger = logging.getLogger("sphero_controller")
        self.logger.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S")
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO); ch.setFormatter(fmt)
        self.logger.addHandler(ch)

        # Start metrics thread
        METRICS.start()

        # Status vars
        self.ollie_status = tk.StringVar(value="Disconnected")
        self.bb8_status = tk.StringVar(value="Disconnected")
        self.active_target = tk.StringVar(value="Ollie")
        self.mode = tk.StringVar(value="Autonomous")
        self.reverse_mode = tk.BooleanVar(value=False)

        # SSE vars
        self.sse_base = tk.StringVar(value="http://localhost:7966")
        self.sse_status = tk.StringVar(value="Disconnected")
        self.last_state = tk.StringVar(value="-")

        # UDP fast path
        self.udp_port = tk.IntVar(value=7970)

        # Autonomy caps
        self.max_speed_var = tk.IntVar(value=150)

        # Workers
        self.ollie = RobotWorker("Ollie", scanner.find_Ollie, lambda s: self._set_var(self.ollie_status, s), self.logger)
        self.bb8 = RobotWorker("BB-8", scanner.find_BB8, lambda s: self._set_var(self.bb8_status, s), self.logger)

        # Receivers
        self._sse: Optional[SseClient] = None
        self._udp: Optional[UdpReceiver] = None

        # Shared latest instruction
        self._instr_lock = threading.Lock()
        self._last_instr = None   # dict with timing fields

        # UI
        self._build_ui()

        # periodic loops
        self._schedule_manual_drive_tick()
        self._schedule_autonomy_tick()

        self.bind("<space>", lambda _e: self._stop_all())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.logger.info("Ready. Connect SSE and/or Start UDP; switch to Autonomous to drive.")

    def _set_var(self, var: tk.StringVar, value: str):
        self.after(0, lambda: var.set(value))

    def _build_ui(self):
        self._style_widgets()
        top = ttk.Frame(self, padding=10); top.pack(side="top", fill="x")
        # Ollie
        frm_ollie = ttk.Labelframe(top, text="Ollie")
        frm_ollie.pack(side="left", padx=10, pady=5, fill="x", expand=True)
        ttk.Label(frm_ollie, text="Name filter:").grid(row=0, column=0, sticky="w")
        self.entry_ollie = ttk.Entry(frm_ollie, width=18); self.entry_ollie.grid(row=0, column=1, padx=6)
        ttk.Button(frm_ollie, text="Connect", command=self._connect_ollie).grid(row=0, column=2, padx=4)
        ttk.Button(frm_ollie, text="Disconnect", command=self._disconnect_ollie).grid(row=0, column=3, padx=4)
        ttk.Label(frm_ollie, text="Status:").grid(row=1, column=0, sticky="w", pady=(6,0))
        ttk.Label(frm_ollie, textvariable=self.ollie_status).grid(row=1, column=1, columnspan=3, sticky="w", pady=(6,0))
        # BB-8
        frm_bb8 = ttk.Labelframe(top, text="BB-8")
        frm_bb8.pack(side="left", padx=10, pady=5, fill="x", expand=True)
        ttk.Label(frm_bb8, text="Name filter:").grid(row=0, column=0, sticky="w")
        self.entry_bb8 = ttk.Entry(frm_bb8, width=18); self.entry_bb8.grid(row=0, column=1, padx=6)
        ttk.Button(frm_bb8, text="Connect", command=self._connect_bb8).grid(row=0, column=2, padx=4)
        ttk.Button(frm_bb8, text="Disconnect", command=self._disconnect_bb8).grid(row=0, column=3, padx=4)
        ttk.Label(frm_bb8, text="Status:").grid(row=1, column=0, sticky="w", pady=(6,0))
        ttk.Label(frm_bb8, textvariable=self.bb8_status).grid(row=1, column=1, columnspan=3, sticky="w", pady=(6,0))
        # Target + Mode + Reverse
        frm_target = ttk.Frame(self, padding=(10, 0, 10, 0))
        frm_target.pack(side="top", fill="x")
        ttk.Label(frm_target, text="Active target:").pack(side="left")
        for label in ("Ollie", "BB-8", "Both"):
            ttk.Radiobutton(frm_target, text=label, value=label, variable=self.active_target).pack(side="left", padx=6)
        ttk.Label(frm_target, text="Mode:").pack(side="left", padx=(20, 6))
        for m in ("Manual", "Autonomous"):
            ttk.Radiobutton(frm_target, text=m, value=m, variable=self.mode).pack(side="left", padx=4)
        ttk.Checkbutton(frm_target, text="Reverse drive (add 180°)", variable=self.reverse_mode,
                        command=self._apply_reverse_mode).pack(side="right")
        # Middle
        mid = ttk.Frame(self, padding=10); mid.pack(side="top", fill="both", expand=True)
        left = ttk.Frame(mid); left.pack(side="left", fill="y", padx=10)
        self.joystick = JoystickCanvas(left, radius=150, knob_radius=18); self.joystick.pack(side="top", padx=10, pady=10)
        self.speed_var = tk.IntVar(value=120)
        self.speed_slider = ttk.Scale(left, from_=0, to=255, orient="horizontal", length=320,
                                      command=lambda _v: None, variable=self.speed_var)
        self.speed_slider.pack(side="top", pady=(6,0))
        ttk.Label(left, text="Manual Speed").pack(side="top")
        rotate_frame = ttk.Frame(left); rotate_frame.pack(side="top", pady=8)
        ttk.Label(rotate_frame, text="Rotate:").pack(side="left", padx=(0,6))
        ttk.Button(rotate_frame, text="−90°", command=lambda: self._rotate_active(-90)).pack(side="left", padx=3)
        ttk.Button(rotate_frame, text="180°", command=lambda: self._rotate_active(180)).pack(side="left", padx=3)
        ttk.Button(rotate_frame, text="+90°", command=lambda: self._rotate_active(+90)).pack(side="left", padx=3)
        ttk.Button(left, text="Stop (Space)", command=self._stop_all).pack(side="top", pady=12)
        # Right: Streaming controls
        right = ttk.Frame(mid); right.pack(side="left", fill="both", expand=True, padx=10)
        auto = ttk.Labelframe(right, text="Autonomous (Instruction Streams)")
        auto.pack(side="top", fill="x", padx=4, pady=6)
        ttk.Label(auto, text="SSE base URL:").grid(row=0, column=0, sticky="w")
        ttk.Entry(auto, width=30, textvariable=self.sse_base).grid(row=0, column=1, sticky="w", padx=(6,12))
        ttk.Button(auto, text="Connect SSE", command=self._connect_sse).grid(row=0, column=2, padx=4)
        ttk.Button(auto, text="Disconnect SSE", command=self._disconnect_sse).grid(row=0, column=3, padx=4)
        ttk.Label(auto, text="SSE Status:").grid(row=1, column=0, sticky="w", pady=(8,0))
        ttk.Label(auto, textvariable=self.sse_status).grid(row=1, column=1, columnspan=3, sticky="w", pady=(8,0))
        ttk.Label(auto, text="UDP listen port:").grid(row=2, column=0, sticky="w", pady=(8,0))
        ttk.Entry(auto, width=8, textvariable=self.udp_port).grid(row=2, column=1, sticky="w", padx=(6,12), pady=(8,0))
        ttk.Button(auto, text="Start UDP", command=self._start_udp).grid(row=2, column=2, padx=4, pady=(8,0))
        ttk.Button(auto, text="Stop UDP", command=self._stop_udp).grid(row=2, column=3, padx=4, pady=(8,0))
        ttk.Label(auto, text="Max auto speed cap").grid(row=3, column=0, sticky="w", pady=(8,0))
        ttk.Scale(auto, from_=50, to=255, orient="horizontal", length=240,
                  command=lambda v: None, variable=self.max_speed_var).grid(row=3, column=1, columnspan=3, sticky="w", padx=(6,0), pady=(8,0))
        ttk.Label(auto, text="Last state:").grid(row=4, column=0, sticky="w", pady=(8,0))
        ttk.Label(auto, textvariable=self.last_state).grid(row=4, column=1, columnspan=3, sticky="w", pady=(8,0))
        # Bottom: debug log
        bottom = ttk.Frame(self, padding=10); bottom.pack(side="bottom", fill="both")
        self.txt_log = tk.Text(bottom, height=12, bg="#0f1419", fg="#e2e8f0")
        self.txt_log.pack(fill="both", expand=True)
        th = TkTextHandler(self.txt_log); th.setLevel(logging.INFO)
        th.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S"))
        self.logger.addHandler(th)

    def _style_widgets(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background="#0b0f13")
        style.configure("TLabelframe", background="#0b0f13", foreground="#e2e8f0")
        style.configure("TLabelframe.Label", background="#0b0f13", foreground="#a8b3c4")
        style.configure("TLabel", background="#0b0f13", foreground="#e2e8f0")
        style.configure("TButton", padding=6)
        style.configure("TRadiobutton", background="#0b0f13", foreground="#e2e8f0")

    # connect/disconnect
    def _connect_ollie(self):
        name = getattr(self, "entry_ollie").get().strip() or None
        self.ollie.connect(toy_name=name)

    def _disconnect_ollie(self):
        self.ollie.disconnect()

    def _connect_bb8(self):
        name = getattr(self, "entry_bb8").get().strip() or None
        self.bb8.connect(toy_name=name)

    def _disconnect_bb8(self):
        self.bb8.disconnect()

    # manual drive loop
    def _schedule_manual_drive_tick(self):
        self._manual_drive_tick()
        self.after(50, self._schedule_manual_drive_tick)  # 20 Hz

    def _manual_drive_tick(self):
        if self.mode.get() != "Manual":
            return
        heading, mag = getattr(self, "joystick").pose()
        base_speed = getattr(self, "speed_var").get()
        target_speed = int(base_speed * mag)
        tgt = self._get_active_target()
        if tgt in ("Ollie", "Both") and self.ollie.is_connected():
            self.ollie.set_desired(heading, target_speed)
        if tgt in ("BB-8", "Both") and self.bb8.is_connected():
            self.bb8.set_desired(heading, target_speed)

    # autonomy tick (apply SSE/UDP)
    def _schedule_autonomy_tick(self):
        self._autonomy_tick()
        self.after(15, self._schedule_autonomy_tick)  # ~66 Hz

    def _autonomy_tick(self):
        if self.mode.get() != "Autonomous":
            return
        instr = None
        with self._instr_lock:
            if self._last_instr is not None:
                instr = dict(self._last_instr)

        if not instr:
            self._apply_rel(0, 0, None, None)
            return

        arrival = float(instr.get("rpi_recv_ts", time.time()))
        if (time.time() - arrival) > 0.35:
            self._apply_rel(0, 0, None, None)
            return

        rel_heading = int(instr.get("rel_heading", 0)) % 360
        speed = int(instr.get("speed", 0))
        self._set_var(self.last_state, str(instr.get("state", "-")))

        # Cap autonomous speed
        speed = max(0, min(int(self.max_speed_var.get()), speed))

        # Metrics: recv->apply and cap->apply
        apply_ts = time.time()
        METRICS.incr_counter("instr_applied", 1)
        rcv = instr.get("rpi_recv_ts")
        if isinstance(rcv, (int, float)):
            METRICS.add_sample("recv_to_apply_ms", (apply_ts - rcv) * 1000.0)
        pc_cap = instr.get("pc_cap_ts")
        if isinstance(pc_cap, (int, float)):
            METRICS.add_sample("cap_to_apply_ms", (apply_ts - pc_cap) * 1000.0)

        seq = instr.get("seq")
        self._apply_rel(rel_heading, speed, seq, pc_cap, apply_ts)

    def _apply_rel(self, rel_heading: int, speed: int, seq: Optional[int], pc_cap_ts: Optional[float], apply_ts: Optional[float]=None):
        tgt = self._get_active_target()
        if tgt in ("Ollie", "Both") and self.ollie.is_connected():
            self.ollie.set_desired_relative(rel_heading, speed, seq=seq, apply_ts=apply_ts, pc_cap_ts=pc_cap_ts)
        if tgt in ("BB-8", "Both") and self.bb8.is_connected():
            self.bb8.set_desired_relative(rel_heading, speed, seq=seq, apply_ts=apply_ts, pc_cap_ts=pc_cap_ts)

    # SSE controls
    def _connect_sse(self):
        base = (self.sse_base.get() or "").strip()
        if not base:
            self._set_var(self.sse_status, "Enter a base URL, e.g. http://<PC>:7966")
            return

        def on_control(obj: dict):
            with self._instr_lock:
                self._last_instr = obj  # latest-wins

        def on_status(text: str):
            self._set_var(self.sse_status, text)

        if self._sse:
            try: self._sse.stop()
            except Exception: pass
            self._sse = None

        self._sse = SseClient(base, on_control=on_control, status_callback=on_status, logger=self.logger)
        self._sse.start()

    def _disconnect_sse(self):
        if self._sse:
            try: self._sse.stop()
            except Exception: pass
        self._sse = None
        self._set_var(self.sse_status, "Disconnected")

    # UDP controls
    def _start_udp(self):
        port = int(self.udp_port.get())
        if self._udp:
            try: self._udp.stop()
            except Exception: pass
            self._udp = None

        def on_packet(obj: dict):
            # Normalize payload (already contains timing & seq from PC)
            h = int(obj.get("rel_heading", obj.get("h", 0))) % 360
            s = int(obj.get("speed", obj.get("s", 0)))
            obj2 = {
                "seq": obj.get("seq"),
                "rel_heading": h, "speed": s,
                "pc_cap_ts": obj.get("pc_cap_ts"),
                "pc_send_ts": obj.get("pc_send_ts"),
                "pc_cap_to_send_ms": obj.get("pc_cap_to_send_ms"),
                "state": obj.get("state", "UDP"),
                "rpi_recv_ts": obj.get("rpi_recv_ts", time.time()),
                "chan": obj.get("chan", "udp"),
            }
            with self._instr_lock:
                self._last_instr = obj2

        self._udp = UdpReceiver("0.0.0.0", port, on_packet=on_packet, logger=self.logger)
        self._udp.start()

    def _stop_udp(self):
        if self._udp:
            try: self._udp.stop()
            except Exception: pass
        self._udp = None

    # helpers
    def _get_active_target(self):
        return self.active_target.get()

    def _apply_reverse_mode(self):
        mode = self.reverse_mode.get()
        self.ollie.set_reverse_mode(mode)
        self.bb8.set_reverse_mode(mode)
        self.logger.info("Reverse mode: %s", "ON" if mode else "OFF")

    def _rotate_active(self, delta):
        tgt = self._get_active_target()
        if tgt in ("Ollie", "Both") and self.ollie.is_connected():
            self.ollie.rotate_by(delta)
        if tgt in ("BB-8", "Both") and self.bb8.is_connected():
            self.bb8.rotate_by(delta)

    def _stop_all(self):
        self.joystick.reset()
        self.speed_var.set(0)
        self.ollie.stop_now()
        self.bb8.stop_now()
        self.logger.info("STOP")

    def _on_close(self):
        try: self._stop_all()
        except Exception: pass
        self._disconnect_sse()
        self._stop_udp()
        self.ollie.disconnect(); self.bb8.disconnect()
        METRICS.stop()
        self.after(150, self.destroy)

if __name__ == "__main__":
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    print("Safety first: keep the area clear. Supervise the robot at all times.")
    App().mainloop()
