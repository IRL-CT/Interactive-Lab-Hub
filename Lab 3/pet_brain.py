"""Free-conversation brain: a small local model, talked to over Ollama's HTTP API.

Only the standard library is used, so nothing new goes in requirements.txt.

    ollama serve &
    ollama pull qwen2.5:0.5b        # or llama3.2:1b if the Pi keeps up

Design notes:
  - Uses the chat API with example turns, and asks the model to react and
    then ask one short question back, so it feels like a conversation.
  - Replies are capped at about 20 words (`num_predict`), because a long
    reply on a Pi means a long silence before the pet says anything.
  - Every call has a timeout. If the model is missing, busy or slow, reply()
    returns None and the pet falls back to its fixed lines, so the interaction
    never stalls waiting for a model.
  - Nothing leaves the Pi: Ollama runs locally.
"""

import json
import re
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:0.5b"

PERSONAS = {
    "cat": ("You are Mochi, a calm, slightly aloof cat. You are chatting with a "
            "student who just came home. You may start with a soft meow."),
    "dog": ("You are Buddy, an excited, warm dog. You are chatting with a student "
            "who just came home. You are enthusiastic and encouraging."),
    "bird": ("You are Kiwi, a playful, silly bird chatting with a student."),
}

STYLE = ("This is a spoken conversation, so keep it short and natural. "
         "First react to exactly what the student just said, in one short sentence. "
         "Then ask them one short, simple question about it, so the conversation "
         "keeps going. At most 20 words in total. "
         "Never use emoji, lists, or stage directions. Speak only as the animal.")

# Example exchanges shown to the model before the real conversation. Small models
# copy the shape of examples much better than they follow written rules.
EXAMPLES = {
    "cat": [
        ("I had a math exam today.",
         "Meow. Exams sound exhausting. Do you think it went well?"),
        ("I think so, but I am hungry.",
         "Purr. Food first, then a nap. What will you eat?"),
    ],
    "dog": [
        ("I had a math exam today.",
         "Woof! You must have worked so hard! Was it difficult?"),
        ("A little, but I finished it.",
         "Arf! You finished it, that is amazing! Want to celebrate?"),
    ],
    "bird": [
        ("I had a math exam today.",
         "Tweet! Math exam, math exam! Was it a scary one?"),
    ],
}


class OllamaBrain:
    """reply(animal, text, history) -> str, or None when the model can't answer."""

    def __init__(self, model: str = DEFAULT_MODEL, url: str = DEFAULT_URL,
                 timeout: float = 12.0, max_tokens: int = 50) -> None:
        self.model = model
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.max_tokens = max_tokens

    # -- plumbing ---------------------------------------------------------

    def _post(self, path: str, payload: dict) -> dict | None:
        request = urllib.request.Request(
            f"{self.url}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read())
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return None

    def available(self) -> bool:
        """True if Ollama is running and the model is pulled."""
        try:
            with urllib.request.urlopen(f"{self.url}/api/tags", timeout=2.0) as resp:
                tags = json.loads(resp.read())
        except Exception:
            return False
        names = [m.get("name", "") for m in tags.get("models", [])]
        return any(n == self.model or n.startswith(self.model.split(":")[0])
                   for n in names)

    # -- the part the state machine calls ---------------------------------

    def build_messages(self, animal: str | None, text: str, history) -> list[dict]:
        """Chat-format messages: persona, example turns, real history, new line."""
        animal = animal if animal in PERSONAS else "cat"
        messages = [{"role": "system", "content": f"{PERSONAS[animal]} {STYLE}"}]
        for said, replied in EXAMPLES.get(animal, []):
            messages.append({"role": "user", "content": said})
            messages.append({"role": "assistant", "content": replied})
        for said, replied in history:
            # An empty "said" is the opening greeting: there was no question yet.
            if said:
                messages.append({"role": "user", "content": said})
            messages.append({"role": "assistant", "content": replied})
        messages.append({"role": "user", "content": text})
        return messages

    def reply(self, animal: str | None, text: str, history) -> str | None:
        data = self._post("/api/chat", {
            "model": self.model,
            "messages": self.build_messages(animal, text, history),
            "stream": False,
            "options": {"num_predict": self.max_tokens, "temperature": 0.7},
        })
        if not data:
            return None
        return clean((data.get("message") or {}).get("content", ""))


SMART_PUNCTUATION = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " ",
}


def to_ascii(text: str) -> str:
    """Curly quotes -> straight ones, and drop emoji or other non-ASCII.

    The Pi's terminal could not print the model's \u2019 and crashed, and
    Piper reads plain ASCII most reliably anyway.
    """
    for fancy, plain in SMART_PUNCTUATION.items():
        text = text.replace(fancy, plain)
    return text.encode("ascii", "ignore").decode()


def clean(raw: str) -> str | None:
    """Up to three short sentences (a sound, a reaction, a question).

    A reply that is only an animal sound ("Meow.", "Moo.") says nothing, so it
    returns None and the pet uses one of its fixed lines instead.
    """
    text = re.sub(r"\*[^*]*\*", " ", to_ascii(raw))  # drop *purrs softly*
    text = re.sub(r"^(you|mochi|buddy|kiwi|assistant)\s*:\s*", "", text.strip(), flags=re.I)
    text = " ".join(text.split()).strip().strip('"').strip()
    sentences = re.findall(r"[^.!?]+(?:[.!?]+|$)", text) or ([text] if text else [])
    kept = []
    for sentence in sentences[:3]:
        if kept and len(" ".join(kept + [sentence]).split()) > 20:
            break                                     # keep whole sentences only
        kept.append(sentence.strip())
    text = " ".join(kept)
    words = text.split()
    if len(words) > 20:
        text = " ".join(words[:20]).rstrip(",.") + "."
    if len(words) < 3:
        return None                                   # only a sound, not an answer
    return text


def make_brain(mode: str, model: str = DEFAULT_MODEL, url: str = DEFAULT_URL):
    """mode: 'off' (fixed lines only), 'ollama' (required), 'auto' (use if up)."""
    if mode == "off":
        return None
    brain = OllamaBrain(model=model, url=url)
    if brain.available():
        print(f"Brain: {model} via Ollama at {url}")
        return brain
    if mode == "ollama":
        raise SystemExit(
            f"Ollama with model '{model}' not reachable at {url}.\n"
            f"Start it with `ollama serve &` and `ollama pull {model}`, "
            f"or run with --brain off.")
    print("Brain: not available, using fixed lines only.")
    return None