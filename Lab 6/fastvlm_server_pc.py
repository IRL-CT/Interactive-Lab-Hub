#!/usr/bin/env python3
# fastvlm_server.py
# FastVLM-7B caption server with:
#  - 4/8-bit or full precision loading
#  - synchronous warmup (pre-alloc KV cache)
#  - dynamic micro-batching for many concurrent single-image requests (/caption)
#  - bulk multi-image endpoint (/caption_batch)
#  - NEW: local folder captioning endpoint (/caption_folder) — send a folder name
#
# Examples (Cloudflare tunnel shown; swap for your host as needed):
#   # Single image
#   curl -X POST https://scout-maria-sizes-referral.trycloudflare.com/caption \
#     -F "image=@/path/to/photo.jpg"
#
#   # Bulk (one request, multiple files)
#   curl -X POST https://scout-maria-sizes-referral.trycloudflare.com/caption_batch \
#     -F "image=@/data/a.jpg" -F "image=@/data/b.png" \
#     -F "prompt=Describe the scene in English."
#
#   # Folder next to this server file, e.g. "./images"
#   curl -X POST https://scout-maria-sizes-referral.trycloudflare.com/caption_folder \
#     -F "folder=images" \
#     -F "prompt=Describe the scene in English." \
#     -F "max_new_tokens=48" -F "min_new_tokens=8"
#
# Tuning (env vars):
#   FASTVLM_MODEL_ID=apple/FastVLM-7B
#   FASTVLM_REV=<hf_commit_or_tag>         # optional
#   FASTVLM_QUANT=4bit|8bit|none           # default 4bit
#   FASTVLM_4BIT_TYPE=nf4|fp4              # default nf4
#   FASTVLM_COMPUTE_DTYPE=fp16|bf16        # default fp16
#   FASTVLM_MAX_NEW_TOKENS=64              # captioning rarely needs 196; 32–96 is good
#   FASTVLM_MIN_NEW_TOKENS=16
#   FASTVLM_WARMUP_TOKENS=64
#   FASTVLM_MAX_BATCH=6                    # try 4–8 on a 3090 with short outputs
#   FASTVLM_BATCH_TIMEOUT_MS=8             # micro-batching window; 4–10ms typical
#   FASTVLM_DYNAMIC_BATCH=1                # enable dynamic batching (default 1)
#   FASTVLM_SANITIZE=0                     # 1 -> lowercase, comma-separated sanitize
#   FASTVLM_FOLDER_MAX_FILES=1000          # cap for /caption_folder
#   HOST=0.0.0.0
#   PORT=7860
#
# Notes:
#  - Keep ONE server process that owns the model. Do not run multiple workers.
#  - Concurrency comes from dynamic batching, not parallel generate() calls.
#  - /caption_folder reads a sibling folder of this script's directory (no recursion).

import io, os, re, threading, time
from dataclasses import dataclass
from collections import deque
from typing import List, Tuple, Dict

import torch
from PIL import Image
from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# Optional AVIF/HEIC support
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except Exception:
    try:
        import avif  # pillow-avif-plugin auto-registers
    except Exception:
        pass

# ---- Performance-friendly flags ------------------------------------------------
torch.backends.cudnn.benchmark = True
torch.set_grad_enabled(False)
if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True

# ---- Configuration --------------------------------------------------------------
MODEL_ID  = os.environ.get("FASTVLM_MODEL_ID", "apple/FastVLM-0.5B")
FASTVLM_REV = os.environ.get("FASTVLM_REV")  # optional
QUANT_MODE = os.environ.get("FASTVLM_QUANT", "4bit").lower()   # "4bit" | "8bit" | "none"
FOURBIT_TYPE = os.environ.get("FASTVLM_4BIT_TYPE", "nf4").lower()  # "nf4" | "fp4"
COMPUTE_DTYPE = os.environ.get("FASTVLM_COMPUTE_DTYPE", "fp16").lower()  # "fp16" | "bf16"

MAX_NEW_TOKENS_DEFAULT = int(os.environ.get("FASTVLM_MAX_NEW_TOKENS", "64"))
MIN_NEW_TOKENS_DEFAULT = int(os.environ.get("FASTVLM_MIN_NEW_TOKENS", "16"))
WARMUP_NEW_TOKENS = int(os.environ.get("FASTVLM_WARMUP_TOKENS", "64"))

# Micro-batching & batching
MAX_BATCH = int(os.environ.get("FASTVLM_MAX_BATCH", "6"))
BATCH_TIMEOUT_MS = int(os.environ.get("FASTVLM_BATCH_TIMEOUT_MS", "8"))
DYNAMIC_BATCH = os.environ.get("FASTVLM_DYNAMIC_BATCH", "1") == "1"

SANITIZE = os.environ.get("FASTVLM_SANITIZE", "0") == "1"
FOLDER_MAX_FILES = int(os.environ.get("FASTVLM_FOLDER_MAX_FILES", "1000"))

# Apple remote code expects this special image token id
IMAGE_TOKEN_INDEX = -200

# ---- Single-GPU CUDA placement (no device_map/accelerate) ----------------------
if not torch.cuda.is_available():
    raise SystemExit("CUDA GPU required. (Install CUDA PyTorch build; e.g., a 3090 with CUDA drivers.)")

DEVICE = torch.device("cuda:0")
compute_dtype = torch.bfloat16 if COMPUTE_DTYPE.startswith("bf") else torch.float16

print(f"[FastVLM:Flask] Loading {MODEL_ID} (quant={QUANT_MODE}) on {DEVICE}; compute_dtype={compute_dtype} ...")

# ---- Tokenizer -----------------------------------------------------------------
tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
if tok.pad_token_id is None:
    tok.pad_token_id = tok.eos_token_id

# ---- Model load (no device_map) -----------------------------------------------
quant_cfg = None
load_kwargs = dict(trust_remote_code=True, low_cpu_mem_usage=True)
if FASTVLM_REV:
    load_kwargs["revision"] = FASTVLM_REV

if QUANT_MODE == "4bit":
    quant_cfg = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=FOURBIT_TYPE,     # "nf4" (default) or "fp4"
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )
    load_kwargs.update(dict(quantization_config=quant_cfg))
elif QUANT_MODE == "8bit":
    quant_cfg = BitsAndBytesConfig(load_in_8bit=True)
    load_kwargs.update(dict(quantization_config=quant_cfg))
else:  # "none" -> unquantized
    load_kwargs.update(dict(torch_dtype=compute_dtype))

# Load on CPU then move to CUDA explicitly.
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **load_kwargs).eval()
model.to(DEVICE)  # moves quantized layers as well
model_dtype = getattr(model, "dtype", None) or compute_dtype

# Vision preprocessing via the model's own tower
try:
    vtower = model.get_vision_tower()
    vtower.to(DEVICE)
    img_proc = vtower.image_processor
except Exception as e:
    raise SystemExit(f"Model does not expose a vision tower as expected: {e}")

# Serialize generation to keep CUDA context stable & predictable
gen_lock = threading.Lock()

# ===== Prompt ===================================================================
NAV_PROMPT = "Describe the scene in English."

# ===== Sanitization (optional) ==================================================
BAD_TAILS = re.compile(
    r"\b(i\s*'?m\s*sorry|i\s*am\s*sorry|note:|however|therefore|please|let\s+me\s+know|i\s+hope)\b",
    re.IGNORECASE,
)
def sanitize(text: str) -> str:
    if not text:
        return "none"
    t = text.replace("\n", " ").strip()
    m = BAD_TAILS.search(t)
    if m:
        t = t[:m.start()].strip()
    t = t.strip(" `\"'*")
    t = re.split(r"[.;:!?]", t)[0].strip()
    t = re.sub(r"\[[^\]]*\]|\([^)]*\)", "", t).strip()
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ,\-]", " ", t)
    t = re.sub(r"\s*,\s*", ", ", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"(,\s*){2,}", ", ", t).strip(" ,")
    return t if t else "none"

# ===== Builders =================================================================
@torch.inference_mode()
def build_inputs_for_prompt(pil_img: Image.Image, prompt: str):
    """
    Prepare token ids and pixel values for one image+prompt.

    IMPORTANT CHANGE:
    - Treat the incoming `prompt` as a SYSTEM instruction (style / behavior),
      and keep the USER message just as <image>. This makes per-request prompts
      (your modes) much more influential.
    """
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user",   "content": "<image>"},
    ]
    rendered = tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
    if "<image>" not in rendered:
        raise RuntimeError("Chat template missing <image> placeholder.")
    pre, post = rendered.split("<image>", 1)

    pre_ids  = tok(pre,  return_tensors="pt", add_special_tokens=False).input_ids.to(DEVICE)
    post_ids = tok(post, return_tensors="pt", add_special_tokens=False).input_ids.to(DEVICE)

    img_tok = torch.tensor([[IMAGE_TOKEN_INDEX]], dtype=pre_ids.dtype, device=DEVICE)
    input_ids = torch.cat([pre_ids, img_tok, post_ids], dim=1)
    attention_mask = torch.ones_like(input_ids, device=DEVICE)

    px = img_proc(images=pil_img, return_tensors="pt")["pixel_values"].to(
        DEVICE, dtype=model_dtype, non_blocking=True
    )
    return input_ids, attention_mask, px

@torch.inference_mode()
def build_batch(pairs: List[Tuple[Image.Image, str]]):
    """
    Create a padded batch of input_ids/attention_mask and a batch of pixel_values.

    Each pair is (PIL_image, prompt). The prompt is treated as a SYSTEM instruction,
    and the user message is just <image>.
    """
    input_ids_list = []
    input_lens = []
    pil_list = []
    for pil_img, prompt in pairs:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user",   "content": "<image>"},
        ]
        rendered = tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        if "<image>" not in rendered:
            raise RuntimeError("Chat template missing <image> placeholder.")
        pre, post = rendered.split("<image>", 1)
        pre_ids  = tok(pre,  return_tensors="pt", add_special_tokens=False).input_ids[0]
        post_ids = tok(post, return_tensors="pt", add_special_tokens=False).input_ids[0]
        img_tok = torch.tensor([IMAGE_TOKEN_INDEX], dtype=pre_ids.dtype)
        ids = torch.cat([pre_ids, img_tok, post_ids], dim=0)  # 1D
        input_ids_list.append(ids)
        input_lens.append(ids.shape[0])
        pil_list.append(pil_img)

    pad_id = tok.pad_token_id
    B = len(input_ids_list)
    max_len = max(x.shape[0] for x in input_ids_list)
    batched_ids = torch.full((B, max_len), pad_id, dtype=input_ids_list[0].dtype)
    for i, ids in enumerate(input_ids_list):
        batched_ids[i, :ids.shape[0]] = ids

    attn_mask = (batched_ids != pad_id).long()
    batched_ids = batched_ids.to(DEVICE, non_blocking=True)
    attn_mask  = attn_mask.to(DEVICE, non_blocking=True)

    px = img_proc(images=pil_list, return_tensors="pt")["pixel_values"].to(
        DEVICE, dtype=model_dtype, non_blocking=True
    )
    return batched_ids, attn_mask, px, input_lens

# ===== Inference ================================================================
@torch.inference_mode()
def run_caption(pil_img: Image.Image, prompt: str, max_new: int, min_new: int) -> str:
    input_ids, attention_mask, px = build_inputs_for_prompt(pil_img, prompt)
    with gen_lock:
        out = model.generate(
            inputs=input_ids,
            attention_mask=attention_mask,
            images=px,
            max_new_tokens=int(max_new),
            min_new_tokens=int(min_new),
            do_sample=False,
            num_beams=1,
            no_repeat_ngram_size=3,
            repetition_penalty=1.05,
            use_cache=True,
            eos_token_id=tok.eos_token_id,
            pad_token_id=tok.eos_token_id,
        )
    gen_only = out[0, input_ids.shape[1]:]
    text = tok.decode(gen_only, skip_special_tokens=True).strip()
    if not text:
        full = tok.decode(out[0], skip_special_tokens=True).strip()
        text = full if full else "none"
    return sanitize(text) if SANITIZE else (text or "none")

@torch.inference_mode()
def run_caption_batch(pil_list: List[Image.Image], prompts: List[str], max_new: int, min_new: int) -> List[str]:
    pairs = list(zip(pil_list, prompts))
    input_ids, attention_mask, px, input_lens = build_batch(pairs)
    with gen_lock:
        out = model.generate(
            inputs=input_ids,
            attention_mask=attention_mask,
            images=px,
            max_new_tokens=int(max_new),
            min_new_tokens=int(min_new),
            do_sample=False,
            num_beams=1,
            no_repeat_ngram_size=3,
            repetition_penalty=1.05,
            use_cache=True,
            eos_token_id=tok.eos_token_id,
            pad_token_id=tok.eos_token_id,
        )

    texts = []
    for i in range(out.shape[0]):
        gen_only = out[i, input_lens[i]:]
        t = tok.decode(gen_only, skip_special_tokens=True).strip()
        if not t:
            t = tok.decode(out[i], skip_special_tokens=True).strip()
        texts.append(sanitize(t) if SANITIZE else (t or "none"))
    return texts

# ===== Utilities for folder endpoint ===========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".avif"}

def _secure_folder_path(folder_name: str) -> str:
    # Allow only a simple folder name (no slashes); restrict to sibling of script dir.
    if not folder_name or any(sep in folder_name for sep in (os.sep, os.altsep) if sep):
        raise ValueError("folder must be a simple name without path separators")
    if folder_name in (".", ".."):
        raise ValueError("invalid folder name")
    path = os.path.realpath(os.path.join(SCRIPT_DIR, folder_name))
    # Ensure it's directly under the script dir (neighbor)
    if os.path.dirname(path) != SCRIPT_DIR:
        raise ValueError("folder must be a neighbor of the server script")
    return path

def _list_image_files(folder_path: str, limit: int) -> List[str]:
    files = []
    for name in sorted(os.listdir(folder_path)):
        p = os.path.join(folder_path, name)
        if not os.path.isfile(p):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext in ALLOWED_EXT:
            files.append(p)
        # If extension filter misses, we still try to open later if needed — but to stay fast,
        # we rely on extension filter here.
        if len(files) >= limit:
            break
    return files

# ===== Warmup ===================================================================
_READY = False
_STARTUP_LAT_MS = None

def _sync_warmup():
    """Synchronous warmup at startup: builds CUDA context, compiles kernels, allocates KV cache."""
    global _READY, _STARTUP_LAT_MS
    t0 = time.perf_counter()

    warm_imgs = [Image.new("RGB", (640, 640), (0, 0, 0)) for _ in range(max(1, MAX_BATCH))]
    pairs = [(im, NAV_PROMPT) for im in warm_imgs]
    input_ids, attention_mask, px, _ = build_batch(pairs)

    with torch.inference_mode(), gen_lock:
        _ = model.generate(
            inputs=input_ids,
            attention_mask=attention_mask,
            images=px,
            max_new_tokens=max(WARMUP_NEW_TOKENS, MAX_NEW_TOKENS_DEFAULT),
            min_new_tokens=1,
            do_sample=False, num_beams=1, use_cache=True,
            eos_token_id=tok.eos_token_id, pad_token_id=tok.eos_token_id,
        )
    with torch.inference_mode(), gen_lock:
        _ = model.generate(
            inputs=input_ids,
            attention_mask=attention_mask,
            images=px,
            max_new_tokens=4,
            min_new_tokens=1,
            do_sample=False, num_beams=1, use_cache=True,
            eos_token_id=tok.eos_token_id, pad_token_id=tok.eos_token_id,
        )

    _STARTUP_LAT_MS = int((time.perf_counter() - t0) * 1000)
    _READY = True
    print(f"[FastVLM:Flask] Warmup complete in ~{_STARTUP_LAT_MS} ms; server is READY.")

# ===== Dynamic micro-batching ===================================================
@dataclass
class _Job:
    pil: Image.Image
    prompt: str
    max_new: int
    min_new: int
    event: threading.Event
    result: str = None
    error: str = None

queue = deque()
q_lock = threading.Lock()
q_cv = threading.Condition(q_lock)

def _batcher_loop():
    while True:
        with q_cv:
            while not queue:
                q_cv.wait()
            t0 = time.perf_counter()
            while len(queue) < MAX_BATCH:
                left = BATCH_TIMEOUT_MS/1000 - (time.perf_counter() - t0)
                if left <= 0:
                    break
                q_cv.wait(timeout=left)
            n = min(MAX_BATCH, len(queue))
            jobs = [queue.popleft() for _ in range(n)]

        try:
            pairs = [(j.pil, j.prompt) for j in jobs]
            input_ids, attention_mask, px, input_lens = build_batch(pairs)
            with gen_lock:
                out = model.generate(
                    inputs=input_ids,
                    attention_mask=attention_mask,
                    images=px,
                    max_new_tokens=max(j.max_new for j in jobs),
                    min_new_tokens=min(j.min_new for j in jobs),
                    do_sample=False, num_beams=1,
                    no_repeat_ngram_size=3, repetition_penalty=1.05,
                    use_cache=True,
                    eos_token_id=tok.eos_token_id, pad_token_id=tok.eos_token_id,
                )
            for i, j in enumerate(jobs):
                gen_only = out[i, input_lens[i]:]
                txt = tok.decode(gen_only, skip_special_tokens=True).strip()
                if not txt:
                    txt = tok.decode(out[i], skip_special_tokens=True).strip()
                j.result = sanitize(txt) if SANITIZE else (txt or "none")
        except Exception as e:
            err = str(e)
            for j in jobs:
                j.error = err
        finally:
            for j in jobs:
                j.event.set()

# ---- Warm up BEFORE serving requests ------------------------------------------
_sync_warmup()
if DYNAMIC_BATCH:
    threading.Thread(target=_batcher_loop, daemon=True).start()

# ===== Flask App ================================================================
app = Flask(__name__)

@app.post("/caption")
def caption():
    if not _READY:
        return jsonify(error="server not ready"), 503

    f = request.files.get("image") or request.files.get("file")
    if not f:
        return jsonify(error="expected multipart/form-data with file field 'image'"), 400

    prompt  = request.form.get("prompt") or NAV_PROMPT
    max_new = int(request.form.get("max_new_tokens", str(MAX_NEW_TOKENS_DEFAULT)))
    min_new = int(request.form.get("min_new_tokens", str(MIN_NEW_TOKENS_DEFAULT)))

    raw = f.read()
    if len(raw) < 10:
        return jsonify(error=f"uploaded file too small ({len(raw)} bytes)"), 400
    try:
        pil = Image.open(io.BytesIO(raw)); pil.load(); pil = pil.convert("RGB")
    except Exception as e:
        sig = list(raw[:16]) if raw else []
        return jsonify(error=f"Pillow could not open image: {type(e).__name__}: {e}. First 16 bytes: {sig}"), 400

    if not DYNAMIC_BATCH:
        try:
            text = run_caption(pil, prompt, max_new, min_new)
            return jsonify(caption=text, prompt_used=prompt)
        except Exception as e:
            return jsonify(error=str(e)), 500

    job = _Job(pil=pil, prompt=prompt, max_new=max_new, min_new=min_new, event=threading.Event())
    with q_cv:
        queue.append(job)
        q_cv.notify()
    if not job.event.wait(timeout=60):
        return jsonify(error="inference timed out"), 504
    if job.error:
        return jsonify(error=job.error), 500
    return jsonify(caption=job.result, prompt_used=prompt)

@app.post("/caption_batch")
def caption_batch():
    if not _READY:
        return jsonify(error="server not ready"), 503

    files = request.files.getlist("image") or request.files.getlist("images")
    if not files:
        return jsonify(error="expected multipart/form-data with file field 'image' (repeatable) or 'images'"), 400
    if len(files) > MAX_BATCH:
        return jsonify(error=f"too many images; MAX_BATCH={MAX_BATCH}"), 400

    prompts = request.form.getlist("prompt")
    if not prompts:
        prompts = [request.form.get("prompt") or NAV_PROMPT] * len(files)
    elif len(prompts) == 1 and len(files) > 1:
        prompts = prompts * len(files)
    elif len(prompts) != len(files):
        return jsonify(error="number of prompts must be 1 or equal to number of images"), 400

    max_new = int(request.form.get("max_new_tokens", str(MAX_NEW_TOKENS_DEFAULT)))
    min_new = int(request.form.get("min_new_tokens", str(MIN_NEW_TOKENS_DEFAULT)))

    pil_list = []
    for f in files:
        raw = f.read()
        if len(raw) < 10:
            return jsonify(error=f"uploaded file too small ({len(raw)} bytes)"), 400
        try:
            pil = Image.open(io.BytesIO(raw)); pil.load(); pil = pil.convert("RGB")
        except Exception as e:
            sig = list(raw[:16]) if raw else []
            return jsonify(error=f"Pillow could not open image: {type(e).__name__}: {e}. First 16 bytes: {sig}"), 400
        pil_list.append(pil)

    try:
        texts = run_caption_batch(pil_list, prompts, max_new, min_new)
        return jsonify(captions=texts, prompts_used=prompts)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.post("/caption_folder")
def caption_folder():
    """
    Caption every image in a folder that is a neighbor (sibling) of this server script.
    Request: multipart/form-data with:
      - folder: simple folder name (e.g., 'images') located at SCRIPT_DIR/folder
      - prompt (optional)
      - max_new_tokens, min_new_tokens (optional)
    Response: JSON dict { "<filename>": "<caption or error: ...>", ... }
    """
    if not _READY:
        return jsonify(error="server not ready"), 503

    folder_name = request.form.get("folder") or request.args.get("folder")
    if not folder_name:
        return jsonify(error="missing 'folder'"), 400

    try:
        folder_path = _secure_folder_path(folder_name)
    except ValueError as ve:
        return jsonify(error=str(ve)), 400

    if not os.path.isdir(folder_path):
        return jsonify(error=f"folder not found: {folder_name}"), 404

    prompt = request.form.get("prompt") or NAV_PROMPT
    max_new = int(request.form.get("max_new_tokens", str(MAX_NEW_TOKENS_DEFAULT)))
    min_new = int(request.form.get("min_new_tokens", str(MIN_NEW_TOKENS_DEFAULT)))

    files = _list_image_files(folder_path, FOLDER_MAX_FILES)
    if not files:
        return jsonify(error=f"no images found in folder '{folder_name}' (allowed: {sorted(ALLOWED_EXT)})"), 404

    results: Dict[str, str] = {}
    # Process in batches for speed + memory safety
    i = 0
    try:
        while i < len(files):
            chunk_paths = files[i:i+MAX_BATCH]
            pil_list, names = [], []
            for p in chunk_paths:
                name = os.path.basename(p)
                names.append(name)
                try:
                    with open(p, "rb") as fh:
                        raw = fh.read()
                    pil = Image.open(io.BytesIO(raw)); pil.load(); pil = pil.convert("RGB")
                    pil_list.append(pil)
                except Exception as e:
                    results[name] = f"error: {type(e).__name__}: {e}"
            # If at least one image opened, run one batched generate
            if pil_list:
                prompts = [prompt] * len(pil_list)
                texts = run_caption_batch(pil_list, prompts, max_new, min_new)
                # Map back only to those successfully opened (skip errors already filled)
                j = 0
                for name in names:
                    if name in results and results[name].startswith("error:"):
                        continue
                    results[name] = texts[j]
                    j += 1
            i += MAX_BATCH
    except Exception as e:
        return jsonify(error=str(e), partial_results=results), 500

    return jsonify(results=results, count=len(results), folder=folder_name, prompt_used=prompt)

@app.get("/health")
def health():
    return jsonify(
        ready=_READY,
        startup_warmup_ms=_STARTUP_LAT_MS,
        model=MODEL_ID,
        quantization=QUANT_MODE,
        device=str(DEVICE),
        dtype=str(model_dtype),
        max_batch=MAX_BATCH,
        dynamic_batch=DYNAMIC_BATCH,
        batch_timeout_ms=BATCH_TIMEOUT_MS,
        max_new_tokens=MAX_NEW_TOKENS_DEFAULT,
        min_new_tokens=MIN_NEW_TOKENS_DEFAULT,
        script_dir=SCRIPT_DIR
    ), 200

@app.get("/")
def root():
    return (
        "FastVLM-7B caption server (CUDA, prewarmed, dynamic micro-batching). "
        "POST image to /caption, multiple images to /caption_batch, or folder name to /caption_folder"
    ), 200

# ===== Main ====================================================================
if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "7860"))
    app.run(host=host, port=port, debug=False, threaded=True)
