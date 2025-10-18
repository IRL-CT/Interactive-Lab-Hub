#!/usr/bin/env python3
# face_server.py
# Simple JSON HTTP server for face recognition on Raspberry Pi 5 (or any Linux box).
# - Loads InsightFace once, caches gallery embeddings, and serves recognition on port 7860.
# - Request:  POST /recognize  {"image_path": "/path/to/captured.jpg"}
# - Response: {"name": "<clean full name>", "confidence": 74.98}
#
# Start separately:
#   python3 face_server.py --headshots ~/facerecog/headshots --model buffalo_m --det 320 --host 0.0.0.0 --port 7860
#
# Dependencies:
#   python3 -m pip install flask onnxruntime insightface opencv-python numpy

import os, sys, argparse, json, hashlib, tempfile, io, glob, re, time, threading, contextlib
from typing import List, Tuple
import numpy as np
import cv2
from flask import Flask, request, jsonify

# Quiet noisy libs on stdout
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("INSIGHTFACE_LOG_LEVEL", "error")

# Lower ONNX Runtime logs to FATAL so they don't pollute output
try:
    import onnxruntime as ort
    if hasattr(ort, "set_default_logger_severity"):
        ort.set_default_logger_severity(4)  # FATAL
except Exception:
    pass

from insightface.app import FaceAnalysis

CACHE_BASENAME = ".emb_cache"

# ----------------- Utility: quiet stdout context -----------------
@contextlib.contextmanager
def quiet_stdout():
    with open(os.devnull, "w") as devnull, contextlib.redirect_stdout(devnull):
        yield

# ----------------- Providers -----------------
def _available_providers():
    try:
        import onnxruntime as _ort
        return set(_ort.get_available_providers() or [])
    except Exception:
        return {"CPUExecutionProvider"}

_AVAIL_PROVIDERS = _available_providers()

def _providers(use_gpu: bool):
    prov = []
    if use_gpu and "CUDAExecutionProvider" in _AVAIL_PROVIDERS:
        prov.append("CUDAExecutionProvider")
    prov.append("CPUExecutionProvider")
    return prov

# ----------------- Name cleaning -----------------
_SUFFIX_NUM = re.compile(r"(_\d{6,})+$")

def clean_name_from_filename(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename))[0]
    base = _SUFFIX_NUM.sub("", base)
    base = re.sub(r"[_\-]+", " ", base)
    base = re.sub(r"[^A-Za-z0-9' ]+", "", base)
    tokens = [t for t in base.split() if not t.isdigit()]
    cleaned = " ".join(tokens).strip().lower()
    return cleaned or "unknown"

# ----------------- Cache helpers -----------------
def _gallery_files(gallery_dir: str) -> List[str]:
    exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp")
    files = []
    for e in exts:
        files.extend(glob.glob(os.path.join(gallery_dir, e)))
    files = sorted(files)
    if not files:
        raise RuntimeError(f"No images found in gallery folder: {gallery_dir}")
    return files

def _cache_paths(gallery_dir: str, model: str, det_size: int) -> Tuple[str, str]:
    abs_gallery = os.path.abspath(gallery_dir)
    h = hashlib.sha1(f"{abs_gallery}|{model}|{det_size}".encode()).hexdigest()[:12]
    idx = os.path.join(abs_gallery, f"{CACHE_BASENAME}_{h}.json")
    npz = os.path.join(abs_gallery, f"{CACHE_BASENAME}_{h}.npz")
    os.makedirs(abs_gallery, exist_ok=True)
    return idx, npz

def _atomic_replace_write_bytes(path: str, data: bytes):
    folder = os.path.dirname(path) or "."
    os.makedirs(folder, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, dir=folder, prefix=".tmp_", suffix=".tmp") as tf:
        tmp_path = tf.name
        tf.write(data)
        tf.flush()
        os.fsync(tf.fileno())
    os.replace(tmp_path, path)

def _atomic_save_npz(path: str, **arrays):
    bio = io.BytesIO()
    np.savez_compressed(bio, **arrays)
    payload = bio.getvalue()
    _atomic_replace_write_bytes(path, payload)

def _atomic_save_json(path: str, obj: dict):
    payload = (json.dumps(obj)).encode("utf-8")
    _atomic_replace_write_bytes(path, payload)

def _load_cache(idx_path: str, npz_path: str):
    if not (os.path.isfile(idx_path) and os.path.isfile(npz_path)):
        return None
    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        with np.load(npz_path) as data:
            names = list(map(str, data["names"]))
            mat = data["embeddings"].astype(np.float32)
        mtimes = meta.get("mtimes", {})
        return {"names": names, "mat": mat, "mtimes": mtimes}
    except Exception:
        return None

def _save_cache(idx_path: str, npz_path: str, names: List[str], mat: np.ndarray, mtimes_map: dict):
    names_arr = np.array(names, dtype=np.str_)
    mat = mat.astype(np.float32, copy=False)
    _atomic_save_npz(npz_path, names=names_arr, embeddings=mat)
    _atomic_save_json(idx_path, {"mtimes": mtimes_map})

def _file_mtime_map(paths: List[str]) -> dict:
    m = {}
    for p in paths:
        try:
            m[os.path.basename(p)] = os.path.getmtime(p)
        except Exception:
            pass
    return m

# ----------------- Server state -----------------
class FaceServer:
    def __init__(self, headshots: str, model: str, det: int, use_gpu: bool):
        self.headshots = headshots
        self.model = model
        self.det = det
        self.use_gpu = use_gpu
        self.providers = _providers(use_gpu)
        self.lock = threading.Lock()
        self.app = None
        self.names = []
        self.mat = None
        self.idx_path, self.npz_path = _cache_paths(self.headshots, self.model, self.det)

    def init_app(self):
        order = [self.model] + [m for m in ["buffalo_m", "buffalo_l", "antelopev2"] if m != self.model]
        last_err = None
        for name in order:
            try:
                with quiet_stdout():
                    app = FaceAnalysis(name=name, providers=self.providers)
                    app.prepare(ctx_id=(0 if ("CUDAExecutionProvider" in self.providers) else -1),
                                det_size=(self.det, self.det))
                if not hasattr(app, "models") or "detection" not in app.models:
                    raise RuntimeError(f'Model package "{name}" loaded without detection.')
                self.app = app
                return
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"Failed to initialize InsightFace: {last_err}")

    def _build_gallery_cached(self, force_rebuild: bool=False):
        files = _gallery_files(self.headshots)
        cache = None if force_rebuild else _load_cache(self.idx_path, self.npz_path)
        target_mtimes = _file_mtime_map(files)
        names: List[str] = []
        vecs: List[np.ndarray] = []
        mtimes_map = {}

        if cache:
            cached_names = cache["names"]
            cached_mat = cache["mat"]
            cached_mtimes = cache["mtimes"]
            name2idx = {n: i for i, n in enumerate(cached_names)}
            to_compute, kept_rows = [], []
            for fp in files:
                base = os.path.basename(fp)
                mt = target_mtimes.get(base)
                if base in name2idx and cached_mtimes.get(base) == mt:
                    kept_rows.append(name2idx[base])
                    names.append(base)
                    mtimes_map[base] = mt
                else:
                    to_compute.append(fp)
            if kept_rows:
                vecs.extend([cached_mat[i] for i in kept_rows])
            for fp in to_compute:
                try:
                    img = cv2.imread(fp)
                    if img is None:
                        continue
                    with quiet_stdout():
                        faces = self.app.get(img)
                    if not faces:
                        continue
                    f = max(faces, key=lambda x: float(getattr(x, "det_score", 0.0)))
                    emb = np.asarray(f.normed_embedding, dtype=np.float32)
                    emb = emb / max(float(np.linalg.norm(emb)), 1e-12)
                    names.append(os.path.basename(fp))
                    vecs.append(emb.astype(np.float32))
                    mtimes_map[os.path.basename(fp)] = target_mtimes.get(os.path.basename(fp))
                except Exception:
                    continue
            if vecs:
                mat = np.vstack(vecs).astype(np.float32, copy=False)
                _save_cache(self.idx_path, self.npz_path, names, mat, mtimes_map)
            else:
                raise RuntimeError("No valid faces found in gallery after filtering.")
            self.names = names
            self.mat = np.vstack(vecs).astype(np.float32, copy=False)
            return

        # No cache: compute all
        for fp in files:
            try:
                img = cv2.imread(fp)
                if img is None:
                    continue
                with quiet_stdout():
                    faces = self.app.get(img)
                if not faces:
                    continue
                f = max(faces, key=lambda x: float(getattr(x, "det_score", 0.0)))
                emb = np.asarray(f.normed_embedding, dtype=np.float32)
                emb = emb / max(float(np.linalg.norm(emb)), 1e-12)
                names.append(os.path.basename(fp))
                vecs.append(emb.astype(np.float32))
                mtimes_map[os.path.basename(fp)] = target_mtimes.get(os.path.basename(fp))
            except Exception:
                continue
        if not vecs:
            raise RuntimeError("No valid faces found in gallery after filtering.")
        mat = np.vstack(vecs).astype(np.float32, copy=False)
        _save_cache(self.idx_path, self.npz_path, names, mat, mtimes_map)
        self.names = names
        self.mat = mat

    def refresh_gallery_if_needed(self):
        # Light-weight refresh each call if needed
        # Protected by a lock just in case
        with self.lock:
            self._build_gallery_cached(force_rebuild=False)

    def recognize(self, image_path: str):
        if not os.path.isfile(image_path):
            return {"name": "unknown", "confidence": 0.0, "error": "image_not_found"}
        img = cv2.imread(image_path)
        if img is None:
            return {"name": "unknown", "confidence": 0.0, "error": "image_read_failed"}

        with quiet_stdout():
            faces = self.app.get(img)
        if not faces:
            return {"name": "unknown", "confidence": 0.0, "error": "no_face_in_query"}

        f = max(faces, key=lambda x: float(getattr(x, "det_score", 0.0)))
        q_emb = np.asarray(f.normed_embedding, dtype=np.float32)
        q_emb = q_emb / max(float(np.linalg.norm(q_emb)), 1e-12)

        if self.mat is None or len(self.names) == 0:
            return {"name": "unknown", "confidence": 0.0, "error": "empty_gallery"}

        sims = self.mat @ q_emb
        best_i = int(np.argmax(sims))
        best_name_file = self.names[best_i]
        conf = float((float(sims[best_i]) + 1.0) * 50.0)  # 0..100
        return {"name": clean_name_from_filename(best_name_file), "confidence": round(conf, 2)}

# ----------------- Flask app -----------------
def create_app(server_state: FaceServer):
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "headshots": server_state.headshots, "model": server_state.model, "det": server_state.det})

    @app.route("/recognize", methods=["POST"])
    def recognize():
        try:
            data = request.get_json(force=True, silent=False)
        except Exception:
            return jsonify({"name": "unknown", "confidence": 0.0, "error": "bad_json"}), 400

        image_path = data.get("image_path")
        if not image_path:
            return jsonify({"name": "unknown", "confidence": 0.0, "error": "missing_image_path"}), 400

        # Refresh (incremental) then recognize
        try:
            server_state.refresh_gallery_if_needed()
            result = server_state.recognize(image_path)
            return jsonify(result)
        except Exception as e:
            return jsonify({"name": "unknown", "confidence": 0.0, "error": str(e)}), 500

    return app

def main():
    parser = argparse.ArgumentParser(description="Face recognition HTTP server")
    parser.add_argument("--headshots", type=str, default="headshots", help='Gallery folder (default: "headshots")')
    parser.add_argument("--model", type=str, default="buffalo_m", help='InsightFace package (default: "buffalo_m")')
    parser.add_argument("--det", type=int, default=320, help="Detector size (default: 320)")
    parser.add_argument("--gpu", action="store_true", help="Use GPU if available")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=7860, help="Port (default: 7860)")
    args = parser.parse_args()

    state = FaceServer(args.headshots, args.model, args.det, args.gpu)
    state.init_app()
    # Build gallery once at startup (subsequent calls are incremental)
    state._build_gallery_cached(force_rebuild=False)

    app = create_app(state)
    # threaded=True to handle multiple requests; use_reloader=False for stability
    app.run(host=args.host, port=args.port, threaded=True, use_reloader=False)

if __name__ == "__main__":
    main()
