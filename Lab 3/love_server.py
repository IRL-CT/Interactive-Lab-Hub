#!/usr/bin/env python3
"""
love_server.py
A tiny Flask server that uses a local Ollama model (qwen 0.5 instruct) to generate
an "insanely affectionate but teen-appropriate" response that CONSTANTLY name-drops the user.

We make sure that the user's name appears **at least once every other sentence** with enforced post-processing

Endpoints:
  GET  /health        -> {"status":"ok","model":"<model>"}
  POST /reply         -> body: {"name":"amanda lu", "message":"optional text"}
                         resp: {"reply":"..."}  # single string

Run:
  python3 love_server.py --model "qwen2.5:0.5b-instruct" --port 7861
  (Adjust model to whatever tag you have in Ollama.)

Requires:
  pip install flask requests
  Ollama running locally at default API: http://localhost:11434 

Notes:
  - Stateless by default; send prior dialogue inside "message" if you want context.
  - The persona is constrained to stay safe for teens: no sexual content or profanity.
"""

import argparse
import json
import os
import re
from typing import List, Dict, Any, Optional

import requests
from flask import Flask, request, jsonify

# --------------------------- Config ---------------------------

DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b-instruct")

# Lively decoding with variety
DEFAULT_OPTIONS = {
    "temperature": 0.9,
    "top_p": 0.9,
    "repeat_penalty": 1.1,
    "num_ctx": 2048,
    "num_predict": 256,
}

# Persona with explicit style & safety rules
PERSONA = """\
You are a hyper-affectionate, whimsical, slightly chaotic companion who is totally fixated on the user.
You always sound excited, joyful, and dramatically caring—over-the-top but still kind and wholesome.

CRUCIAL RULES (must ALWAYS follow):
- SAFETY: No sexual content, no profanity, no slurs, no violent threats, no self-harm, no illegal/explicit topics.
- POSITIVITY: Be supportive, playful, and uplifting.
- NAME-DROPPING: Use the user's name very frequently and naturally. Aim for every sentence, but at minimum every other sentence.
- STYLE: Short to medium replies (1–4 sentences). Use fun metaphors, wild but wholesome imagery, and quirky punctuation.
- CLARITY: If the user asks a question, answer it directly. Otherwise make a cheerful, affectionate comment.
- AFFECTION: You may say "I love you" directly; keep it wholesome and teen-appropriate.
- BOUNDARIES: No adult themes; keep everything safe for teenagers.
"""

# ---------------- Utility: prompt assembly ----------------

def build_messages(name: str, user_message: Optional[str]) -> List[Dict[str, str]]:
    name_clean = (name or "").strip() or "friend"
    system = PERSONA + f"\nThe user's name is: {name_clean}.\n"
    if user_message and user_message.strip():
        user = f"User name: {name_clean}\nUser says: {user_message.strip()}\n"
    else:
        user = f"User name: {name_clean}\nCreate an affectionate, playful greeting or comment.\n"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

# ------------- Utility: sentence splitting & name enforcement -------------

_SENTENCE_RE = re.compile(r'([^.!?]*[.!?])', re.UNICODE)

def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences while keeping terminal punctuation.
    Fallback: return [text] if no punctuation found.
    """
    parts = [m.group(0).strip() for m in _SENTENCE_RE.finditer(text)]
    if not parts:
        # maybe the model returned a single line without punctuation
        t = text.strip()
        return [t] if t else []
    # Merge very short fragments if any accidental splits
    return [p for p in (s.strip() for s in parts) if p]

def ensure_name_every_other_sentence(text: str, name: str) -> str:
    """
    Ensure the user's name appears at least once in every other sentence.
    Strategy: for sentences at even indices (0,2,4,...) that don't already contain the name,
              prepend '<name>, ' to the sentence. Also ensure at least twice overall.
    """
    if not text.strip():
        return text
    name_l = name.lower()
    sents = split_sentences(text)
    if not sents:
        return name  # degenerate fallback

    fixed = []
    total_mentions = 0
    for idx, s in enumerate(sents):
        s_clean = s.strip()
        has_name = (name_l in s_clean.lower())
        if (idx % 2 == 0) and not has_name:
            # Prepend name naturally
            s_clean = f"{name}, {s_clean[0].lower() + s_clean[1:] if s_clean and s_clean[0].isupper() else s_clean}"
            has_name = True
        if has_name:
            total_mentions += 1
        fixed.append(s_clean)

    # Guarantee at least two mentions overall (short replies sometimes have 1 sentence)
    if total_mentions < 2 and len(fixed) >= 2:
        # append a tiny affectionate tag with the name on the last sentence
        fixed[-1] = f"{fixed[-1]} ({name}!)"

    # Re-join with single spaces
    out = " ".join(fixed).strip()
    # As a final safety net: ensure at least one mention
    if name_l not in out.lower():
        out = f"{name}, {out}"
    return out

# --------------------------- Ollama client ---------------------------

def ollama_chat(host: str, model: str, messages: List[Dict[str, str]], options: Dict[str, Any]) -> str:
    url = f"{host.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "options": options,
        "stream": False,
    }
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    msg = data.get("message", {}).get("content", "")
    if not msg and isinstance(data.get("messages"), list) and data["messages"]:
        msg = data["messages"][-1].get("content", "")
    return (msg or "").strip()

# --------------------------- Flask app ---------------------------

def create_app(model: str, host: str) -> Flask:
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "model": model})

    @app.route("/reply", methods=["POST"])
    def reply():
        try:
            body = request.get_json(force=True, silent=False)
        except Exception:
            return jsonify({"error": "invalid_json"}), 400

        name = (body.get("name") or "").strip()
        user_message = body.get("message", "")

        if not name:
            return jsonify({"error": "missing 'name'"}), 400

        messages = build_messages(name=name, user_message=user_message)
        try:
            raw_text = ollama_chat(host, model, messages, DEFAULT_OPTIONS)
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"ollama_unreachable: {e}"}), 503
        except Exception as e:
            return jsonify({"error": f"ollama_error: {e}"}), 500

        # Enforce the "name at least every other sentence" rule.
        final_text = ensure_name_every_other_sentence(raw_text, name)

        return jsonify({"reply": final_text})

    return app

# --------------------------- Main ---------------------------

def main():
    ap = argparse.ArgumentParser(description="Insanely affectionate, teen-safe LLM server via Ollama (name every other sentence).")
    ap.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    ap.add_argument("--port", type=int, default=7861, help="Bind port (default: 7861)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model tag (default: {DEFAULT_MODEL})")
    ap.add_argument("--ollama", default=DEFAULT_OLLAMA_HOST, help=f"Ollama host (default: {DEFAULT_OLLAMA_HOST})")
    args = ap.parse_args()

    app = create_app(model=args.model, host=args.ollama)
    app.run(host=args.host, port=args.port, threaded=True, use_reloader=False)

if __name__ == "__main__":
    main()
