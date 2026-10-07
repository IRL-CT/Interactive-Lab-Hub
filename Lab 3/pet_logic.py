"""State machine for the Chatterbox pet (Lab 3, Part 2).

Kept free of hardware imports so it can be tested on any machine, and so the
Pi script only has to do microphone, screen, button and speaker work.

The rules it encodes (see the README):
  - nothing is listening until the button is pressed
  - the button always means "go to the next animal"
  - three failed tries (nothing heard, or a word that is not a keyword)
    send it back to sleep, so it never loops forever
  - the bird always repeats what it heard (never the language model)
"""

import random
from dataclasses import dataclass

ANIMALS = ["cat", "dog", "bird"]

PETS = {
    "cat": {
        "name": "Mochi",
        "greeting": "Meow. I am Mochi. Was your day good or tiring?",
        "length_scale": 1.15,  # a little slower: calm and aloof
    },
    "dog": {
        "name": "Buddy",
        "greeting": "Woof! I am Buddy. Did you have a good day?",
        "length_scale": 0.85,  # a little faster: eager
    },
    "bird": {
        "name": "Kiwi",
        "greeting": "Tweet! I am Kiwi. Say one word for me to repeat!",
        "length_scale": 1.0,
    },
}

ANSWERS = {
    "good": "I'm glad to hear that!",
    "tiring": "You should take a little rest.",
    "yes": "Yay!",
    "no": "That's okay.",
}

# What people actually said in testing: "tired", not "tiring"; "yeah", not "yes".
SYNONYMS = {
    "good": {"good", "great", "fine", "nice", "okay", "ok", "happy", "awesome"},
    "tiring": {"tiring", "tired", "exhausted", "sleepy", "hard", "busy", "stressful"},
    "yes": {"yes", "yeah", "yep", "sure", "please"},
    "no": {"no", "nope", "nah"},
}

GENERIC = {
    "cat": ["Meow. That sounds like a lot.", "Mrrp. Tell me more?",
            "Purr. I am listening."],
    "dog": ["Woof! Tell me more!", "Arf! I like hearing about that.",
            "Bark! Go on!"],
    "bird": ["Tweet! Say more!", "Chirp chirp?", "Tweet! I am listening!"],
}
HISTORY_TURNS = 4
# A keyword only counts as the whole answer in a short utterance. In a longer
# sentence ("I don't have a good day") the keyword is not the point, so the
# brain handles it instead.
KEYWORD_MAX_WORDS = 3
NEGATIONS = {"not", "no", "dont", "never", "nope", "didnt", "wasnt"}

PROMPT_CHOOSE = "Pick a friend: cat, dog, or bird."
SLEEP_SCREEN = "Press to start"
MAX_TRIES = 3
BIRD_ECHO_WORDS = 5   # Kiwi repeats at most this many of your last words


@dataclass
class Response:
    """What the hardware layer should do after one input."""

    say: str | None = None      # line to speak, or None for silence
    led: str = "off"            # led colour while speaking this line
    screen: str = ""            # what the screen shows afterwards
    heard_text: str = ""        # the raw transcript, shown so mis-hearings are visible
    animal: str | None = None   # which voice to speak it with


class PetMachine:
    """ASLEEP -> CHOOSE -> CONVERSE, with a three-try limit everywhere."""

    def __init__(self, brain=None) -> None:
        # `brain` is optional. If given, it answers anything the keywords do not
        # cover, so the conversation is not limited to fixed lines. It must have
        # reply(animal, text, history) and may return None when it is
        # unavailable or too slow, in which case a fixed line is used instead.
        self.state = "ASLEEP"
        self.animal: str | None = None
        self.tries = 0
        self.led = "off"
        self.screen = SLEEP_SCREEN
        self.brain = brain
        self.history: list[tuple[str, str]] = []

    # ---------- helpers ----------

    def _sleep(self, line: str | None) -> Response:
        self.state = "ASLEEP"
        self.animal = None
        self.tries = 0
        self.screen = SLEEP_SCREEN
        self.led = "off"
        return Response(say=line, led="blue" if line else "off", screen=self.screen)

    def _listen_for_animal(self, line: str | None) -> Response:
        self.state = "CHOOSE"
        self.screen = " / ".join(ANIMALS)
        self.led = "green"
        return Response(say=line, led="blue" if line else "green", screen=self.screen)

    def _greet(self, animal: str, heard: str = "") -> Response:
        self.animal = animal
        self.state = "CONVERSE"
        self.tries = 0
        pet = PETS[animal]
        self.screen = pet["name"]
        self.led = "green"  # after it finishes greeting, it is your turn again
        # The greeting is a question, so it belongs in the history: otherwise a
        # reply like "not really" reaches the brain with nothing to answer.
        self.history = [("", pet["greeting"])]
        return Response(say=pet["greeting"], led="blue", screen=self.screen,
                        heard_text=heard, animal=animal)

    def _reply(self, line: str, heard: str) -> Response:
        """A successful turn: remember it and clear the failure count."""
        self.tries = 0
        self.history.append((heard, line))
        self.history = self.history[-HISTORY_TURNS:]
        return Response(say=line, led="blue", screen=self.screen,
                        heard_text=heard, animal=self.animal)

    def _fail(self, first: str, second: str, heard: str = "") -> Response:
        """Escalating re-prompt: say something new each time, then give up."""
        self.tries += 1
        if self.tries >= MAX_TRIES:
            response = self._sleep("I'll rest. Press to start again.")
            response.heard_text = heard
            return response
        line = first if self.tries == 1 else second
        # The transcript goes on screen too, so a mis-hearing is visible.
        return Response(say=line, led="blue", screen=self.screen,
                        heard_text=heard, animal=self.animal)

    # ---------- inputs ----------

    def press(self) -> Response:
        """The button: wakes it up, then walks through the animals."""
        if self.state == "ASLEEP":
            return self._listen_for_animal(PROMPT_CHOOSE)
        if self.animal is None:
            return self._greet(ANIMALS[0])
        nxt = ANIMALS[(ANIMALS.index(self.animal) + 1) % len(ANIMALS)]
        return self._greet(nxt)

    def nothing_heard(self) -> Response:
        """The endpointer fired but nothing was transcribed."""
        if self.state == "ASLEEP":
            return Response(screen=self.screen)
        return self._fail(
            "I did not hear anything. Please try again.",
            "You can also press the button to switch friends.",
        )

    def hear(self, text: str) -> Response:
        """One transcribed utterance."""
        if self.state == "ASLEEP":
            return Response(screen=self.screen)  # not listening yet, on purpose

        words = _words(text)

        if self.state == "CHOOSE":
            for animal in ANIMALS:
                if animal in words:
                    return self._greet(animal, heard=text)
            return self._fail(
                "Please say cat, dog, or bird.",
                "You can also press the button to switch friends.",
                heard=text,
            )

        # CONVERSE
        if "bye" in words:
            return self._sleep("Bye! Come back soon.")

        if self.animal == "bird":
            # Kiwi's whole game is copying you, so it never uses keywords or
            # the language model: it repeats what it heard (a few words at most).
            echo = " ".join(text.strip().rstrip(".!?").split()[-BIRD_ECHO_WORDS:])
            return self._reply(f"Tweet! {echo}!", text)

        # Fast path: a short answer made of one of the keywords is answered
        # instantly, with no model. Longer sentences go to the brain, so a
        # keyword buried in a sentence cannot hijack the reply.
        negated = bool(NEGATIONS & set(words))
        if len(words) <= KEYWORD_MAX_WORDS or self.brain is None:
            for keyword, reply in ANSWERS.items():
                if SYNONYMS[keyword] & set(words):
                    if keyword != "no" and negated:
                        break     # "not good" is not a cheerful answer
                    return self._reply(reply, text)

        # Anything else is a real sentence. Hand it to the brain if there is one.
        if self.brain is not None:
            free = self.brain.reply(self.animal, text, self.history)
            if free:
                return self._reply(free, text)
            # brain unreachable or too slow: fall through to the fixed lines

        if self.brain is not None:
            return self._reply(_generic(self.animal), text)

        return self._fail(
            "Please say good, tired, yes, no, or bye.",
            "You can also press the button to switch friends.",
            heard=text,
        )


def _generic(animal: str | None) -> str:
    """A line that works after anything, picked at random so it is not robotic."""
    return random.choice(GENERIC.get(animal or "cat", GENERIC["cat"]))


def _words(text: str) -> list[str]:
    """Lowercased words with punctuation stripped, so 'Cat!' matches 'cat'."""
    cleaned = "".join(c.lower() if c.isalnum() else " " for c in text)
    return cleaned.split()