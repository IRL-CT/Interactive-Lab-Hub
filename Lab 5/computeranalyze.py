"""
Sphero Ollie & BB-8 Computer Vision “brain”

Our Behavior
--------------------------------
- SEARCH (forward + continuous spin):
  - SEARCH begins only after a brief holdoff when the person is lost.

- STUCK detection & escape:
  - If the camera image stays nearly identical for >=2.0s AND there is no human,
    we trigger an “ESCAPE_BACK” for ~0.9s: command a straight-back move

- Rotation to keep human centered ALWAYS takes priority over STOP:
  - Even if the bbox/face STOP threshold is met, we still steer to center and use a tiny
    forward speed (pivot_speed_stop) so Pi accepts heading updates.

Video ingest kinds
------------------
--kind udp      : OpenCV/FFmpeg H.264/MPEG-TS (e.g., udp://@:7971?fifo_size=5000000&overrun_nonfatal=1)
--kind mjpeg    : HTTP multipart stream /mjpeg/<index>
--kind snapshot : HTTP polling /snapshot/<index>.jpg

Control out
-----------
- SSE at /events (non-blocking, latest-only)
- UDP fast path: --udp-host <rpi_ip> --udp-port 7970

Metrics
-------
- Per-frame wall-clock timestamps in each payload
- 10s rolling averages to computer_metrics.jsonl
"""

import argparse
import asyncio
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
from aiohttp import web

# Vision stack
try:
    import cv2
except Exception:
    cv2 = None
try:
    from ultralytics import YOLO
except Exception:
    YOLO = None
try:
    import mediapipe as mp  # optional (face stop rule)
except Exception:
    mp = None

import urllib.request
from urllib.error import URLError, HTTPError

import socket
import torch
from collections import defaultdict


# ---------------------------- Metrics --------------------------------------- #

class RollingMetrics:
    """
    Thread-safe rolling 10s averages dumped to JSONL.
    Call add_sample(name, ms) / incr_counter(name), set_label(key,val).
    """
    def __init__(self, path: str, window_s: float = 10.0):
        self.path = path
        self.window_s = window_s
        self._lock = threading.Lock()
        self._sums = defaultdict(float)   # metric -> sum(ms)
        self._counts = defaultdict(int)   # metric -> count
        self._counters = defaultdict(int) # counter name -> count
        self._labels = {}
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
        # final flush
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

    def set_label(self, key: str, value):
        with self._lock:
            self._labels[key] = value

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
            if not self._counts and not self._counters:
                return
            avg = {}
            for k, s in self._sums.items():
                c = max(1, self._counts.get(k, 0))
                if self._counts.get(k, 0) == 0:
                    continue
                avg[k] = s / c
            out = {
                "ts": time.time(),
                "window_s": self.window_s,
                "avg_ms": avg,
                "counts": dict(self._counters),
                "labels": dict(self._labels),
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


# ---------------------------- MJPEG client (browser-like) ------------------- #

class MjpegClient:
    def __init__(self, url: str, logger: logging.Logger, timeout: float = 5.0, chunk_size: int = 65536):
        self.url = url
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.log = logger
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest = None

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

    def get_latest(self):
        with self._lock:
            return None if self._latest is None else self._latest

    @staticmethod
    def _parse_boundary(ct_header: str) -> bytes:
        boundary = "frame"
        try:
            if ct_header:
                parts = [p.strip() for p in ct_header.split(";")]
                for p in parts:
                    if p.lower().startswith("boundary="):
                        b = p.split("=", 1)[1].strip().strip('"').strip("'")
                        boundary = b.lstrip("-") or "frame"
                        break
        except Exception:
            pass
        return ("--" + boundary).encode("ascii", "ignore")

    def _run(self):
        headers = {
            "User-Agent": "ComputerVision/1.0",
            "Accept": "multipart/x-mixed-replace",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
        }
        backoff = 0.5
        while not self._stop.is_set():
            try:
                req = urllib.request.Request(self.url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    ct = resp.headers.get("Content-Type", "")
                    boundary = self._parse_boundary(ct)
                    if not boundary:
                        raise RuntimeError("MJPEG boundary not found in Content-Type")

                    buf = bytearray()
                    self.log.info("MJPEG: connected (boundary=%r)", boundary)
                    backoff = 0.5

                    while not self._stop.is_set():
                        chunk = resp.read(self.chunk_size)
                        if not chunk:
                            raise EOFError("MJPEG stream ended")
                        buf += chunk

                        while True:
                            start = buf.find(boundary)
                            if start == -1:
                                if len(buf) > 2_000_000:
                                    del buf[:-4096]
                                break
                            if start > 0:
                                del buf[:start]
                                start = 0

                            header_start = start + len(boundary)
                            if len(buf) < header_start + 4:
                                break
                            if buf[header_start:header_start + 2] == b"\r\n":
                                header_start += 2

                            end_headers = buf.find(b"\r\n\r\n", header_start)
                            if end_headers == -1:
                                break

                            headers_block = bytes(buf[header_start:end_headers])
                            content_length = None
                            for line in headers_block.split(b"\r\n"):
                                k = line.split(b":", 1)
                                if len(k) == 2 and k[0].strip().lower() == b"content-length":
                                    try:
                                        content_length = int(k[1].strip())
                                    except Exception:
                                        content_length = None

                            data_start = end_headers + 4
                            if content_length is not None:
                                if len(buf) < data_start + content_length:
                                    break
                                img_bytes = bytes(buf[data_start:data_start + content_length])
                                del buf[:data_start + content_length]
                            else:
                                next_boundary = buf.find(boundary, data_start)
                                if next_boundary == -1:
                                    if len(buf) > 4_000_000:
                                        del buf[:-4096]
                                    break
                                img_bytes = bytes(buf[data_start:next_boundary])
                                del buf[:next_boundary]

                            try:
                                arr = np.frombuffer(img_bytes, dtype=np.uint8)
                                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR) if cv2 is not None else None
                                if frame is not None:
                                    with self._lock:
                                        self._latest = frame
                            except Exception:
                                pass

            except Exception as e:
                if self._stop.is_set():
                    break
                self.log.warning("MJPEG: stream error: %s; reconnecting in %.1fs", e, backoff)
                time.sleep(backoff)
                backoff = min(5.0, backoff * 1.7)


# ---------------------------- SSE Broadcaster ------------------------------- #

class SseBroadcaster:
    """Non-blocking, latest-only SSE broadcaster (safe from other threads)."""
    def __init__(self, logger: logging.Logger):
        self.log = logger
        self._clients = set()  # set[asyncio.Queue[str]]
        self._lock = asyncio.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def attach_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self.log.info("SSE: attached to event loop.")

    async def add_client(self):
        q: asyncio.Queue = asyncio.Queue(maxsize=2)
        async with self._lock:
            self._clients.add(q)
        self.log.info("SSE: client connected (%d total)", len(self._clients))
        return q

    async def remove_client(self, q):
        async with self._lock:
            self._clients.discard(q)
        self.log.info("SSE: client disconnected (%d total)", len(self._clients))

    def broadcast(self, obj: dict):
        if not self._loop:
            return
        try:
            data = json.dumps(obj, separators=(",", ":"))
            payload = f"event: control\ndata: {data}\n\n"
        except Exception:
            return

        async def _send():
            dead = []
            for q in list(self._clients):
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    try:
                        _ = q.get_nowait()  # drop oldest
                        q.put_nowait(payload)
                    except Exception:
                        dead.append(q)
                except Exception:
                    dead.append(q)
            for q in dead:
                await self.remove_client(q)

        self._loop.call_soon_threadsafe(asyncio.create_task, _send())


# ---------------------------- UDP Sender (fast path) ------------------------ #

class UdpSender:
    """Tiny JSON line sender over UDP (unreliable but ultra-low latency)."""
    def __init__(self, host: Optional[str], port: Optional[int], logger: logging.Logger):
        self.addr = None
        self.sock = None
        self.log = logger
        if host and port:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)  # low delay TOS
                self.addr = (host, int(port))
                self.log.info("UDP: will send to %s:%d", host, int(port))
            except Exception as e:
                self.log.error("UDP: cannot init sender: %s", e)
                self.sock = None
                self.addr = None

    def send(self, obj: dict):
        if not self.sock or not self.addr:
            return
        try:
            payload = json.dumps(
                {
                    "seq": obj.get("seq", 0),
                    "rel_heading": int(obj.get("rel_heading", 0)),
                    "speed": int(obj.get("speed", 0)),
                    "state": obj.get("state", "-"),
                    # timestamps (optional; controller may ignore)
                    "pc_cap_ts": obj.get("pc_cap_ts"),
                    "pc_send_ts": obj.get("pc_send_ts"),
                    "pc_cap_to_send_ms": obj.get("pc_cap_to_send_ms"),
                },
                separators=(",", ":")
            ).encode("utf-8")
            self.sock.sendto(payload, self.addr)
        except Exception:
            pass


# ---------------------------- Detection logic ------------------------------- #

@dataclass
class Target:
    cx: float
    cy: float
    h_ratio: float
    w_ratio: float
    conf: float
    t: float


class Computer:
    """
    Baseline behavior + metrics, with UDP/MJPEG/Snapshot ingest.
    """
    def __init__(self, video_base: str, index: int, kind: str,
                 broadcaster: SseBroadcaster, udp_sender: UdpSender,
                 logger: logging.Logger, metrics: RollingMetrics):
        self.base = video_base.rstrip("/")
        self.index = int(index)
        self.kind = kind.lower().strip()
        self.broadcast = broadcaster.broadcast
        self.udp = udp_sender
        self.log = logger
        self.metrics = metrics

        self._device = "cpu"
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._mjpeg: Optional[MjpegClient] = None
        self._udp_cap: Optional["cv2.VideoCapture"] = None
        self._model = None

        # Behavior tunables (baseline)
        self.close_thresh = 0.50
        self.face_close_thresh = 0.18
        self.target_memory_s = 0.25
        self.search_holdoff_s = 2.0
        self.search_rate_degps = 25.0 * 0.75
        self.search_speed_factor = 0.45 * 0.75
        self.stuck_diff_thresh = 2.0
        self.stuck_detect_s = 2.0
        self.stuck_escape_s = 0.9
        self.stuck_escape_speed = 80
        self._still_accum_s = 0.0
        self._sig_prev = None
        self._last_frame_diff = 0.0
        self._escape_until: Optional[float] = None
        self.pivot_speed_stop = 6
        self.follow_setpoint = 0.28
        self.max_speed = 150
        self.min_speed_floor = 50
        self.speed_tau = 0.25
        self.turn_speed_trim = 0.5
        self.yaw_kp = 180.0
        self.yaw_kd = 60.0
        self.yaw_max_face = 110
        self.yaw_max_approach = 20
        self.yaw_slew_degps = 300.0
        self.aim_deadband = 0.03

        # Stats/overlay
        self._fps = 0.0
        self._last_fps_t = 0.0
        self._fps_count = 0
        self._ov_lock = threading.Lock()
        self._last_overlay: Optional[np.ndarray] = None

        # State
        self._last_target: Optional[Target] = None
        self._last_seen_time: float = 0.0
        self._rel_forward_offset = 0
        self._calibrated = False
        self._probe_in_flight = False

        # Telemetry / seq
        self._seq = 0

        # Command smoothing / loss handling
        self._cmd_speed_ema = 0.0
        self._last_cmd_rel = 0.0
        self._last_dx = 0.0
        self._no_target_since: Optional[float] = None

        # SEARCH integrator
        self._search_angle = 0.0

    def _mjpeg_url(self) -> str:
        return f"{self.base}/mjpeg/{self.index}"

    def _snapshot_url(self) -> str:
        return f"{self.base}/snapshot/{self.index}.jpg?ts={int(time.time() * 1000)}"

    def get_latest_overlay(self) -> Optional[np.ndarray]:
        with self._ov_lock:
            return None if self._last_overlay is None else self._last_overlay

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
        self._thread = None
        if self._mjpeg:
            try:
                self._mjpeg.stop()
            except Exception:
                pass
        self._mjpeg = None
        if self._udp_cap is not None:
            try:
                self._udp_cap.release()
            except Exception:
                pass
            self._udp_cap = None

    # ---------------------------- I/O helpers ------------------------------- #

    def _fetch_snapshot_frame(self, timeout: float = 2.0):
        url = self._snapshot_url()
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "ComputerVision/1.0",
                    "Accept": "image/jpeg",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            if not data:
                return None
            arr = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return frame
        except (URLError, HTTPError, TimeoutError, ValueError):
            return None
        except Exception:
            return None

    def _draw_overlay(self, frame, det_target, target, rel_heading, speed, state_msg):
        img = frame.copy()
        if cv2 is None:
            return img
        h, w = img.shape[:2]
        cv2.line(img, (w // 2, 0), (w // 2, h), (200, 200, 200), 1)
        cv2.line(img, (0, h // 2), (w, h // 2), (200, 200, 200), 1)
        if target is not None:
            cx = int(target.cx * w); cy = int(target.cy * h)
            box_h = int(target.h_ratio * h); box_w = int(target.w_ratio * w)
            x1 = max(0, cx - box_w // 2); y1 = max(0, cy - box_h // 2)
            x2 = min(w - 1, cx + box_w // 2); y2 = min(h - 1, cy + box_h // 2)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(img, (cx, cy), 5, (0, 255, 0), -1)
        src = (self.base if self.kind == "udp"
               else (f"{self.base}/mjpeg/{self.index}" if self.kind == "mjpeg"
                     else f"{self.base}/snapshot/{self.index}.jpg?ts=..."))
        lines = [
            f"Device: {self._device} | fps≈{self._fps:.1f}",
            f"State: {state_msg}",
            f"RelHead={rel_heading if rel_heading is not None else '-'}  Speed={speed}  Max={self.max_speed}",
            f"SEARCH: rate≈{self.search_rate_degps:.1f}°/s speed≈{int(max(40,self.search_speed_factor*self.max_speed))}",
            f"Still≈{self._still_accum_s:.1f}s diff≈{self._last_frame_diff:.1f}",
            f"Stop(h)≥{self.close_thresh:.2f} Face≥{self.face_close_thresh:.2f}",
            f"Src: {src}",
        ]
        y = 20
        for s in lines:
            cv2.putText(img, s, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 255, 30), 2, cv2.LINE_AA)
            y += 22
        return img

    # ---------------------------- Main loop --------------------------------- #

    def _run(self):
        # Device
        try:
            dev = "cuda:0" if torch.cuda.is_available() else "cpu"
        except Exception:
            dev = "cpu"
        self._device = dev
        self.metrics.set_label("device", self._device)
        self.metrics.set_label("kind", self.kind)

        # Model
        if YOLO is None or cv2 is None:
            self.log.error("Computer: ultralytics and opencv-python required.")
            return
        self.log.info("Computer: loading YOLO model (device=%s)...", dev)
        try:
            model_name = os.environ.get("YOLO_MODEL", "yolov8n.pt")
            self._model = YOLO(model_name)
        except Exception as e:
            self.log.exception("Computer: failed to load model: %s", e)
            return

        # Open source
        if self.kind == "mjpeg":
            url = self._mjpeg_url()
            self._mjpeg = MjpegClient(url, logger=self.log)
            self._mjpeg.start()
            self.log.info("Computer: MJPEG client started for %s", url)
        elif self.kind == "udp":
            self.log.info("Computer: opening UDP video at %s", self.base)
            self._udp_cap = cv2.VideoCapture(self.base, cv2.CAP_FFMPEG)
            if not self._udp_cap.isOpened():
                self.log.error("Computer: failed to open UDP source at %s", self.base)
                return
        elif self.kind == "snapshot":
            self.log.info("Computer: snapshot polling from %s", self.base)
        else:
            self.log.warning("Computer: unknown kind '%s'; defaulting to snapshot.", self.kind)
            self.kind = "snapshot"
            self.metrics.set_label("kind", self.kind)

        snapshot_period = 1.0 / 20.0
        last_loop_t = time.time()

        while not self._stop.is_set():
            # CAPTURE
            if self.kind == "mjpeg":
                frame = self._mjpeg.get_latest() if self._mjpeg else None
                if frame is None:
                    time.sleep(0.005)
                    continue
                pc_cap_ts = time.time()
            elif self.kind == "udp":
                ok, frame = self._udp_cap.read()
                if not ok or frame is None:
                    time.sleep(0.002)
                    continue
                pc_cap_ts = time.time()
            else:
                t_cap0 = time.time()
                frame = self._fetch_snapshot_frame(timeout=2.0)
                if frame is None:
                    self.log.warning("Computer: snapshot not available.")
                    time.sleep(0.1)
                    continue
                elapsed = time.time() - t_cap0
                to_sleep = max(0.0, snapshot_period - elapsed)
                if to_sleep > 0:
                    time.sleep(to_sleep)
                pc_cap_ts = time.time()

            h, w = frame.shape[:2]
            now = time.time()
            dt = max(1e-3, now - last_loop_t)
            last_loop_t = now

            # YOLO person-only detection
            t_pred0 = time.time()
            results = self._model.predict(
                frame, imgsz=640, conf=0.4, iou=0.5,
                device=self._device, classes=[0], verbose=False
            )
            t_pred1 = time.time()
            det_target = self._select_target(results, w, h, t_pred1)
            target = self._update_target_memory(det_target, t_pred1)

            # Update stuck detector (use raw detection absence)
            self._update_stuck(frame, no_human=(det_target is None), dt=dt)

            # Movement decision (RELATIVE headings)
            rel_heading_cmd, speed_cmd, state_msg = self._compute_drive_command(target, w, h, dt)
            t_decide = time.time()

            speed_cmd = max(0, min(self.max_speed, int(speed_cmd)))

            # Seq + message (with wall-clock metrics)
            self._seq = (self._seq + 1) & 0x7fffffff
            pc_send_ts = time.time()
            msg = {
                "seq": self._seq,
                "rel_heading": int(rel_heading_cmd or 0),
                "speed": int(speed_cmd or 0),
                "state": state_msg,
                # timestamps
                "pc_cap_ts": pc_cap_ts,
                "pc_pred_end_ts": t_pred1,
                "pc_decide_ts": t_decide,
                "pc_send_ts": pc_send_ts,
                # durations
                "pc_pred_ms": int((t_pred1 - t_pred0) * 1000),
                "pc_decide_ms": int((t_decide - t_pred1) * 1000),
                "pc_cap_to_pred_ms": int((t_pred0 - pc_cap_ts) * 1000),
                "pc_cap_to_send_ms": int((pc_send_ts - pc_cap_ts) * 1000),
            }

            # Metrics (PC side)
            self.metrics.incr_counter("frames", 1)
            self.metrics.incr_counter("msgs", 1)
            self.metrics.add_sample("pc_pred_ms", msg["pc_pred_ms"])
            self.metrics.add_sample("pc_decide_ms", msg["pc_decide_ms"])
            self.metrics.add_sample("pc_cap_to_pred_ms", msg["pc_cap_to_pred_ms"])
            self.metrics.add_sample("pc_cap_to_send_ms", msg["pc_cap_to_send_ms"])

            # Send on both channels
            self.broadcast(msg)
            self.udp.send(msg)

            # Overlay
            overlay = self._draw_overlay(frame, det_target, target, rel_heading_cmd, speed_cmd, state_msg)
            with self._ov_lock:
                self._last_overlay = overlay

            # FPS stats
            self._fps_count += 1
            if (pc_send_ts - self._last_fps_t) >= 1.0:
                self._fps = self._fps_count / max(1e-6, (pc_send_ts - self._last_fps_t))
                self._fps_count = 0
                self._last_fps_t = pc_send_ts

    # ---------------------------- Target handling --------------------------- #

    @staticmethod
    def _select_target(results, w, h, now) -> Optional[Target]:
        best = None
        try:
            if not results:
                return None
            res = results[0]
            if not hasattr(res, "boxes") or res.boxes is None:
                return None
            boxes = res.boxes
            for i in range(len(boxes)):
                xyxy = boxes.xyxy[i].tolist()
                conf = float(boxes.conf[i].item())
                x1, y1, x2, y2 = xyxy
                bw, bh = max(1, x2 - x1), max(1, y2 - y1)
                area = bw * bh
                score = area * conf
                if best is None or score > best[0]:
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    best = (score, Target(
                        cx=cx / w, cy=cy / h,
                        h_ratio=bh / h, w_ratio=bw / w, conf=conf, t=now
                    ))
        except Exception:
            return None
        return best[1] if best else None

    def _update_target_memory(self, det_target: Optional[Target], now: float) -> Optional[Target]:
        # Heavier smoothing for center/size, short memory.
        if det_target is not None:
            a = 0.55
            if self._last_target is None:
                self._last_target = det_target
            else:
                sm = Target(
                    cx=self._last_target.cx * (1 - a) + det_target.cx * a,
                    cy=self._last_target.cy * (1 - a) + det_target.cy * a,
                    h_ratio=self._last_target.h_ratio * (1 - a) + det_target.h_ratio * a,
                    w_ratio=self._last_target.w_ratio * (1 - a) + det_target.w_ratio * a,
                    conf=max(self._last_target.conf * (1 - a) + det_target.conf * a, det_target.conf),
                    t=now
                )
                self._last_target = sm
            self._last_seen_time = now
            self._no_target_since = None
            return self._last_target
        else:
            if self._last_target and (now - self._last_seen_time) <= self.target_memory_s:
                return self._last_target
            self._last_target = None
            if self._no_target_since is None:
                self._no_target_since = now
            return None

    # ---------------------------- Stuck detector ---------------------------- #

    def _update_stuck(self, frame_bgr, no_human: bool, dt: float):
        """Increment stillness if frames are nearly identical while no human is detected."""
        try:
            g = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            small = cv2.resize(g, (16, 16), interpolation=cv2.INTER_AREA)
            if self._sig_prev is None:
                self._sig_prev = small
                self._last_frame_diff = 0.0
                self._still_accum_s = 0.0
                return
            diff = np.mean(np.abs(small.astype(np.int16) - self._sig_prev.astype(np.int16)))
            self._last_frame_diff = float(diff)
            self._sig_prev = small
            if no_human and diff < self.stuck_diff_thresh:
                self._still_accum_s += dt
            else:
                self._still_accum_s = 0.0

            if self._still_accum_s >= self.stuck_detect_s and (self._escape_until is None or time.time() >= self._escape_until):
                self._escape_until = time.time() + self.stuck_escape_s
                self._still_accum_s = 0.0  # reset accumulator after triggering
        except Exception:
            # On any error, don't break the loop; just reset stuck metrics.
            self._still_accum_s = 0.0

    # ---------------------------- Control logic (baseline) ------------------- #

    def _compute_drive_command(self, target: Optional[Target], w: int, h: int, dt: float):
        now = time.time()

        # 0) STUCK escape dominates when active (and no target)
        if self._escape_until is not None and now < self._escape_until and target is None:
            rel = int(round(self._slew_rel(180.0, dt)))  # straight-back approximation
            self._cmd_speed_ema = self._ema(self._cmd_speed_ema, float(self.stuck_escape_speed), dt, self.speed_tau)
            return rel, int(self._cmd_speed_ema), "ESCAPE_BACK"

        # 1) If target dropped recently but not long enough for SEARCH, lerp to 0
        if target is None:
            lost_s = (now - self._no_target_since) if self._no_target_since else 0.0
            if lost_s < self.search_holdoff_s:
                self._cmd_speed_ema = self._ema(self._cmd_speed_ema, 0.0, dt, self.speed_tau)
                rel = int(round(self._slew_rel(0.0, dt)))
                return rel, int(self._cmd_speed_ema), f"LOST {lost_s:.1f}s | decel & hold"

            # 2) ORIGINAL SEARCH (forward + continuous spin), ~3/4 speed/rate
            self._search_angle = (self._search_angle + self.search_rate_degps * dt) % 360.0
            rel = int(round(self._slew_rel(self._search_angle, dt)))
            desired_speed = int(min(self.max_speed, max(40, self.search_speed_factor * self.max_speed)))
            self._cmd_speed_ema = self._ema(self._cmd_speed_ema, float(desired_speed), dt, self.speed_tau)
            return rel, int(self._cmd_speed_ema), f"SEARCH_SPIN rel={rel}° @ {desired_speed}"

        # 3) Target available: compute steering FIRST (rotation always trumps STOP)
        dx = target.cx - 0.5
        d_dx = (dx - self._last_dx) / max(1e-3, dt)
        self._last_dx = dx

        raw_steer = self.yaw_kp * dx + self.yaw_kd * d_dx
        # FACE vs APPROACH based on deadband; then clamp
        if abs(dx) > self.aim_deadband:
            steer = self._clamp(raw_steer, -self.yaw_max_face, self.yaw_max_face)
            phase = "FACE"
        else:
            steer = self._clamp(raw_steer, -self.yaw_max_approach, self.yaw_max_approach)
            phase = "APPROACH"

        rel = int(round(self._slew_rel(steer, dt)))

        # STOP logic only affects speed (not heading)
        dist_ratio = target.h_ratio
        too_close_bbox = dist_ratio >= self.close_thresh

        if too_close_bbox:
            desired_speed = self.pivot_speed_stop
            state = f"STOP-PIVOT | {phase} dx={dx:+.2f}, r={dist_ratio:.2f}, steer={steer:+.0f}°"
        else:
            desired_speed = self._speed_for_distance(dist_ratio)
            # Trim forward speed when steering hard
            trim = 1.0 - self.turn_speed_trim * (abs(steer) / max(1e-6, float(self.yaw_max_face)))
            desired_speed = max(self.min_speed_floor, int(desired_speed * max(0.2, trim)))
            state = f"{phase} | dx={dx:+.2f}, r={dist_ratio:.2f}, steer={steer:+.0f}°"

        self._cmd_speed_ema = self._ema(self._cmd_speed_ema, float(desired_speed), dt, self.speed_tau)
        return rel, int(self._cmd_speed_ema), state

    # --- helpers: speed & yaw shaping ---

    def _speed_for_distance(self, h_ratio: float) -> int:
        """
        Proportional control to keep box size near setpoint, clamped to [min, max].
        """
        e = self.follow_setpoint - h_ratio  # positive if far (box small) -> go faster
        kp = 380.0
        spd = self.min_speed_floor + kp * e
        if e <= 0:
            # Too close relative to setpoint => bias toward slow
            spd = max(0.0, self.min_speed_floor * 0.4 + 200.0 * e)
        return int(max(0.0, min(self.max_speed, spd)))

    def _ema(self, prev: float, target: float, dt: float, tau: float) -> float:
        alpha = max(0.0, min(1.0, dt / max(1e-6, tau)))
        return prev + alpha * (target - prev)

    def _slew_rel(self, desired_rel: float, dt: float) -> float:
        """
        Apply rate limit to relative-heading command (deg/s), then remember it.
        """
        max_delta = self.yaw_slew_degps * dt
        new_rel = self._clamp(desired_rel, self._last_cmd_rel - max_delta, self._last_cmd_rel + max_delta)
        self._last_cmd_rel = new_rel
        return new_rel

    @staticmethod
    def _clamp(x, lo, hi):
        return lo if x < lo else hi if x > hi else x


# ---------------------------- HTTP Server (SSE + Video) --------------------- #

VIDEO_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Computer Preview</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root { color-scheme: dark; }
    html, body { margin:0; height:100%; background:#000; display:grid; place-items:center; }
    img { width:100vw; height:100vh; object-fit:contain; background:#000; }
  </style>
</head>
<body>
  <img src="/video.mjpeg?ts={ts}" alt="Overlay preview" />
</body>
</html>
"""

class AppServer:
    def __init__(self, host: str, port: int, computer: Computer, broadcaster: SseBroadcaster, logger: logging.Logger, metrics: RollingMetrics):
        self.host = host
        self.port = port
        self.computer = computer
        self.broadcast = broadcaster
        self.log = logger
        self.metrics = metrics
        self.app = web.Application()
        self.app.add_routes([
            web.get("/events", self.handle_events),
            web.get("/status", self.handle_status),
            web.get("/video", self.handle_video_page),
            web.get("/video.mjpeg", self.handle_video_mjpeg),
            web.get("/video.jpg", self.handle_video_snapshot),
        ])
        self.app.on_startup.append(self._on_startup)
        self.app.on_shutdown.append(self._on_shutdown)

    async def _on_startup(self, app):
        loop = asyncio.get_running_loop()
        self.broadcast.attach_loop(loop)
        self.computer.start()
        self.metrics.start()
        self.log.info("SSE server on http://%s:%d  (Ctrl+C to stop)", self.host, self.port)

    async def _on_shutdown(self, app):
        self.computer.stop()
        self.metrics.stop()

    async def handle_status(self, request):
        data = {
            "video_base": self.computer.base,
            "index": self.computer.index,
            "kind": self.computer.kind,
            "device": self.computer._device,
            "fps": self.computer._fps,
        }
        return web.json_response(data)

    async def handle_events(self, request):
        # SSE headers
        resp = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "X-Accel-Buffering": "no",
            },
        )
        await resp.prepare(request)

        # Best-effort Nagle disable
        try:
            transport = request.transport
            sock = transport.get_extra_info("socket")
            if sock:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass

        q = await self.broadcast.add_client()

        try:
            await resp.write(b": hello\n\n")
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=1.0)
                    await resp.write(payload.encode("utf-8"))
                except asyncio.TimeoutError:
                    await resp.write(b": keep-alive\n\n")
        except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
            pass
        finally:
            try:
                await resp.write_eof()
            except Exception:
                pass
            await self.broadcast.remove_client(q)
        return resp

    async def handle_video_page(self, request):
        html = VIDEO_HTML.replace("{ts}", str(int(time.time() * 1000)))
        return web.Response(text=html, content_type="text/html")

    async def handle_video_snapshot(self, request):
        frame = self.computer.get_latest_overlay()
        if frame is None:
            return web.Response(status=503, text="No frame yet")
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            return web.Response(status=500, text="Encode error")
        return web.Response(
            body=buf.tobytes(),
            content_type="image/jpeg",
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    async def handle_video_mjpeg(self, request):
        boundary = "frame"
        resp = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": f"multipart/x-mixed-replace; boundary={boundary}",
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
        await resp.prepare(request)

        # Disable Nagle for preview too
        try:
            transport = request.transport
            sock = transport.get_extra_info("socket")
            if sock:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass

        try:
            period = 1.0 / 15.0
            while True:
                frame = self.computer.get_latest_overlay()
                if frame is None:
                    await asyncio.sleep(0.05)
                    continue
                ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if not ok:
                    await asyncio.sleep(period)
                    continue
                part = (
                    f"--{boundary}\r\n"
                    "Content-Type: image/jpeg\r\n"
                    f"Content-Length: {len(buf)}\r\n\r\n"
                ).encode("ascii") + buf.tobytes() + b"\r\n"
                await resp.write(part)
                await asyncio.sleep(period)
        except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
            pass
        finally:
            try:
                await resp.write_eof()
            except Exception:
                pass
        return resp


# ---------------------------- Main ------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(description="SSE/UDP Vision Computer (baseline behavior + metrics + UDP/MJPEG/Snapshot ingest)")
    parser.add_argument("--video-base", type=str, default="udp://@:7971?fifo_size=5000000&overrun_nonfatal=1",
                        help="For --kind udp, pass a full FFmpeg URL; for HTTP kinds, pass base server URL (e.g., http://localhost:7965)")
    parser.add_argument("--index", type=int, default=1, help="Camera index/path (used for mjpeg/snapshot)")
    parser.add_argument("--kind", type=str, default="udp", choices=["mjpeg", "snapshot", "udp"],
                        help="Video ingest kind")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind host for HTTP/SSE server")
    parser.add_argument("--port", type=int, default=7966, help="Bind port for HTTP/SSE server")
    parser.add_argument("--udp-host", type=str, default="", help="(Optional) UDP target host (RPI IP or overlay IP)")
    parser.add_argument("--udp-port", type=int, default=7970, help="(Optional) UDP target port (default 7970)")
    args = parser.parse_args()

    # Logging
    logger = logging.getLogger("computer")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S"))
    logger.addHandler(ch)

    metrics_path = os.environ.get("COMPUTER_METRICS_FILE", "computer_metrics.jsonl")
    metrics = RollingMetrics(metrics_path, window_s=10.0)

    broadcaster = SseBroadcaster(logger)
    udp_sender = UdpSender(args.udp_host.strip(), args.udp_port if args.udp_host.strip() else None, logger)

    computer = Computer(video_base=args.video_base, index=args.index, kind=args.kind,
                        broadcaster=broadcaster, udp_sender=udp_sender, logger=logger, metrics=metrics)
    server = AppServer(host=args.host, port=args.port, computer=computer, broadcaster=broadcaster, logger=logger, metrics=metrics)
    web.run_app(server.app, host=args.host, port=args.port, access_log=None)


if __name__ == "__main__":
    main()
