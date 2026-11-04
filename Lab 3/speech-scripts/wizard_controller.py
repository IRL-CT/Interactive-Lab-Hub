import random
import sys
from pathlib import Path

from faster_whisper import WhisperModel
from echo_bot import Speaker, DEFAULT_VOICE

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


AUDIO_FILE = Path("decision.wav")
QUESTION_FILE = Path("selected_question.txt")


QUESTION_CARDS = {
    "control": [
        "What part of this is still within your control?",
        "If the result stayed unknown, what would you still choose to do?",
    ],
    "action": [
        "What is one step you can take tomorrow?",
        "What would trying seriously look like this week?",
    ],
    "fear": [
        "What are you protecting yourself from?",
        "What would you do if you did not need to feel certain first?",
    ],
    "people": [
        "What do the people involved need from you?",
        "What conversation are you avoiding?",
    ],
    "choice": [
        "Which choice would you regret never testing?",
        "Which choice is closer to the person you want to become?",
    ],
}


KEYWORD_GROUPS = {
    "control": (
        "win", "won", "lose", "result", "fail", "succeed",
        "success", "championship", "tournament",
        "competition", "match", "game",
    ),
    "action": (
        "start", "begin", "wait", "waiting",
        "delay", "avoiding", "stuck", "procrastinate",
    ),
    "fear": (
        "afraid", "fear", "scared", "worried",
        "anxious", "uncertain", "unsure",
        "not sure", "risk",
    ),
    "people": (
        "team", "friend", "partner", "family",
        "relationship", "people", "together",
    ),
    "choice": (
        "decision", "decide", "choice",
        "choose", "option", "whether", "should",
    ),
}


def transcribe_audio(model, audio_file):
    segments, info = model.transcribe(str(audio_file), beam_size=1)

    transcript = " ".join(
        segment.text.strip() for segment in segments
    ).strip()

    return transcript, info.duration


def suggest_question(transcript):
    text = transcript.lower()
    candidates = []

    for group, keywords in KEYWORD_GROUPS.items():
        if any(keyword in text for keyword in keywords):
            candidates.extend(QUESTION_CARDS[group])

    # No keywords matched: draw from all ten cards.
    if not candidates:
        for cards in QUESTION_CARDS.values():
            candidates.extend(cards)

    # Remove duplicates while keeping the original order.
    candidates = list(dict.fromkeys(candidates))

    drawn_question = random.choice(candidates)

    return (
        "I cannot tell you what happened. "
        + drawn_question
    )


def choose_question(transcript, return_point):
    question = suggest_question(transcript)

    print()
    print("=" * 60)
    print("SATOR SQUARE - AUTOMATIC CONTROLLER")
    print("=" * 60)
    print()
    print("Return point:", return_point)
    print()
    print("USER TRANSCRIPT")
    print(transcript)
    print()
    print("-" * 60)
    print("DRAWN QUESTION CARD")
    print(question)
    print()

    QUESTION_FILE.write_text(
        question,
        encoding="utf-8",
    )

    print("QUESTION SENT TO DEVICE")
    print(question)
    print("=" * 60)
    print()

    return question


def main():
    if not AUDIO_FILE.is_file():
        sys.exit("decision.wav was not found.")

    print("Loading base.en...")

    model = WhisperModel(
        "base.en",
        device="cpu",
        compute_type="int8",
    )

    transcript, duration = transcribe_audio(model, AUDIO_FILE)
    print(f"Audio duration: {duration:.2f}s")

    question = choose_question(
        transcript,
        return_point="ONE MONTH",
    )

    print("Connecting future self...")
    speaker = Speaker(DEFAULT_VOICE)
    speaker.say(question)
    print("Question delivered.")


if __name__ == "__main__":
    main()
