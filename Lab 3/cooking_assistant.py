#!/usr/bin/env python3
"""Autonomous voice cooking assistant for Raspberry Pi."""

import argparse
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
DEFAULT_VAD = LAB_DIR / "models" / "silero_vad.onnx"
DEFAULT_VOICE = LAB_DIR / "voices" / "en_US-lessac-medium.onnx"
SAMPLE_RATE = 16_000


@dataclass
class Conversation:
    step: int = 0
    previous_instruction: str = "First, chop one onion into small pieces."
    pending_timer_minutes: int | None = None
    timer_action: tuple[str, int | None] | None = None

    def respond(self, heard: str, timer_remaining: int | None = None) -> tuple[str, bool]:
        text = heard.lower().strip()
        self.timer_action = None
        if any(word in text for word in ("goodbye", "quit", "stop cooking", "exit")):
            return "Goodbye. Enjoy your meal!", True
        if text == "hi" or any(word in text for word in ("hello", "hi ", "hey")):
            return "Hello! I am ready to help you cook. Say start when you are ready.", False
        if "start" in text:
            self.step = 1
            self.previous_instruction = "First, chop one onion into small pieces."
            return self.previous_instruction, False
        if "repeat" in text or "again" in text:
            return self.previous_instruction, False
        if "wait" in text or "not ready" in text or "still cutting" in text:
            return "No problem. Take your time and say next when you are ready.", False
        missing_ingredient = any(
            phrase in text
            for phrase in ("don't have", "do not have", "no ", "without", "out of")
        )
        if missing_ingredient:
            substitutions = {
                "olive oil": "vegetable oil",
                "onion": "a shallot or half a teaspoon of onion powder",
                "butter": "olive oil",
                "milk": "oat milk or soy milk",
                "egg": "a flax egg",
                "salt": "a small amount of soy sauce",
                "garlic": "one eighth teaspoon of garlic powder per clove",
                "tomato": "canned tomatoes",
            }
            for ingredient, substitute in substitutions.items():
                if ingredient in text:
                    return f"You can substitute {substitute} for {ingredient}. Say next to continue.", False
            return "Tell me which ingredient you are missing, and I will try to suggest a substitute.", False
        if "next" in text or "ready" in text:
            self.step += 1
            instructions = {
                1: "First, chop one onion into small pieces.",
                2: "Heat one tablespoon of oil in the pan over medium heat.",
                3: "Add the onion and cook it until it becomes soft.",
                4: "Add the remaining ingredients and stir them together.",
                5: "Cook for five minutes, then turn off the heat.",
            }
            self.previous_instruction = instructions.get(self.step, "That was the final step. Your dish is ready.")
            return self.previous_instruction, False
        if "cancel" in text and "timer" in text:
            self.timer_action = ("cancel", None)
            self.pending_timer_minutes = None
            return "The timer has been cancelled.", False
        if ("remaining" in text or "left" in text) and "timer" in text:
            if timer_remaining is None:
                return "There is no timer running.", False
            minutes, seconds = divmod(max(0, timer_remaining), 60)
            return f"The timer has {minutes} minutes and {seconds} seconds remaining.", False
        if "timer" in text or "minute" in text:
            number_words = {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            }
            match = re.search(r"\b(\d{1,2})\b", text)
            minutes = int(match.group(1)) if match else next(
                (value for word, value in number_words.items() if word in text), None
            )
            if minutes is None:
                return "How many minutes should I set the timer for?", False
            if not 1 <= minutes <= 60:
                return "Please choose a timer between one and sixty minutes.", False
            self.pending_timer_minutes = minutes
            return f"I heard {minutes} minutes. Please say yes to confirm.", False
        if text in {"yes", "yes.", "correct", "that's correct", "that is correct"}:
            if self.pending_timer_minutes is None:
                return "There is nothing waiting for confirmation.", False
            minutes = self.pending_timer_minutes
            self.pending_timer_minutes = None
            self.timer_action = ("start", minutes)
            return f"Confirmed. The {minutes} minute timer has started.", False
        if text in {"no", "no."}:
            self.pending_timer_minutes = None
            return "Okay. Please say the correct time again.", False
        return "I did not understand that. Say start, next, repeat, wait, or ask about an ingredient.", False


class SimulatedAudio:
    def listen(self):
        return input("\nYOU: ").strip()

    def say(self, text):
        print(f"PI: {text}")


class PiAudio:
    def __init__(self, model, vad_path, voice_path, min_silence):
        import numpy as np
        import sherpa_onnx
        import sounddevice as sd
        from faster_whisper import WhisperModel
        from piper import PiperVoice

        for path, label in ((vad_path, "VAD model"), (voice_path, "Piper voice")):
            if not path.is_file():
                raise FileNotFoundError(f"{label} not found at {path}. Run speech-scripts/setup.sh")
        self.np, self.sd = np, sd
        self.recognizer = WhisperModel(model, device="cpu", compute_type="int8")
        self.voice = PiperVoice.load(str(voice_path))
        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = str(vad_path)
        config.silero_vad.min_silence_duration = min_silence
        config.silero_vad.min_speech_duration = 0.25
        config.sample_rate = SAMPLE_RATE
        self.config, self.sherpa = config, sherpa_onnx

    def listen(self):
        print("Listening...", flush=True)
        vad = self.sherpa.VoiceActivityDetector(self.config, buffer_size_in_seconds=30)
        window = self.config.silero_vad.window_size
        buffer = self.np.empty(0, dtype=self.np.float32)
        with self.sd.InputStream(channels=1, dtype="float32", samplerate=SAMPLE_RATE) as stream:
            while True:
                chunk, _ = stream.read(1600)
                buffer = self.np.concatenate([buffer, chunk.reshape(-1)])
                while len(buffer) >= window:
                    vad.accept_waveform(buffer[:window])
                    buffer = buffer[window:]
                if not vad.empty():
                    utterance = self.np.array(vad.front.samples, dtype=self.np.float32)
                    vad.pop()
                    segments, _ = self.recognizer.transcribe(utterance, beam_size=1)
                    return " ".join(part.text.strip() for part in segments).strip()

    def say(self, text):
        print(f"PI: {text}", flush=True)
        for chunk in self.voice.synthesize(text):
            audio = self.np.frombuffer(chunk.audio_int16_bytes, dtype=self.np.int16)
            self.sd.play(audio, samplerate=chunk.sample_rate)
            self.sd.wait()


class TimerManager:
    def __init__(self, announce):
        self.announce = announce
        self.timer = None
        self.deadline = None

    def start(self, minutes):
        self.cancel()
        seconds = minutes * 60
        self.deadline = time.monotonic() + seconds
        self.timer = threading.Timer(seconds, self._finished)
        self.timer.daemon = True
        self.timer.start()

    def cancel(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = None
        self.deadline = None

    def remaining(self):
        if self.deadline is None:
            return None
        return max(0, int(self.deadline - time.monotonic() + 0.999))

    def _finished(self):
        self.timer = None
        self.deadline = None
        self.announce("Your timer is finished.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--model", default="tiny.en")
    parser.add_argument("--vad-model", type=Path, default=DEFAULT_VAD)
    parser.add_argument("--voice", type=Path, default=DEFAULT_VOICE)
    parser.add_argument("--min-silence", type=float, default=1.0)
    args = parser.parse_args()
    audio = SimulatedAudio() if args.simulate else PiAudio(args.model, args.vad_model, args.voice, args.min_silence)
    conversation = Conversation()
    timer = TimerManager(audio.say)
    audio.say("Cooking assistant ready. Say hello or start when you are ready.")
    while True:
        heard = audio.listen()
        if not heard:
            continue
        if not args.simulate:
            print(f"YOU: {heard}", flush=True)
        reply, should_exit = conversation.respond(heard, timer.remaining())
        audio.say(reply)
        if conversation.timer_action:
            action, minutes = conversation.timer_action
            timer.start(minutes) if action == "start" else timer.cancel()
        if should_exit:
            timer.cancel()
            return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
