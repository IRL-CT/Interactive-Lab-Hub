# pomodoro_logic.py
# Pure state machine for the Color Pomodoro Timer (no hardware imports),
# so it can be unit tested without a Pi/display attached, and so new
# phases/rules can be added here without touching the display loop.

import math

SESSION_CONFIG = {
    30: {"focus": 10, "wrap": 2, "break": 3},
    60: {"focus": 22, "wrap": 3, "break": 5},
}
FOCUS_DURATION = SESSION_CONFIG[30]["focus"]
BREAK_DURATION = SESSION_CONFIG[30]["break"]
WRAP_DURATION = SESSION_CONFIG[30]["wrap"]
HOLD_DURATION = 2  # seconds to hold Button B to reset to idle, for A to show counter
WRAP_BREATH_PERIOD = 2.0  # seconds for one full bright -> dim -> bright breath
WRAP_BREATH_MIN = 0.7     # dimmest brightness during the breath (1.0 = full)
RAINBOW_COLORS = (
    (220, 40, 40),
    (245, 130, 30),
    (245, 210, 40),
    (0, 170, 80),
    (0, 80, 220),
    (70, 40, 170),
    (150, 50, 180),
)

PHASE_COLORS = {
    "IDLE": (245, 245, 245), # light gray
    "FOCUS": (0, 80, 220),   # blue
    "BREAK": (0, 170, 80),   # green
    "WRAP": (255, 165, 0),     # amber
    "PAUSED": (90, 90, 90),  # dark gray
    "COUNTER": (35, 35, 35),  # counter screen
}


class PomodoroState:
    def __init__(self, session_minutes=30):
        if session_minutes not in SESSION_CONFIG:
            raise ValueError("session_minutes must be 30 or 60")

        config = SESSION_CONFIG[session_minutes]
        self.counter = 0
        self.session_minutes = session_minutes
        self.focus_duration = config["focus"]
        self.break_duration = config["break"]
        self.wrap_duration = config["wrap"]

        self.phase = "IDLE"  # "IDLE", "FOCUS", "WRAP", or "BREAK"
        self.paused = False
        self.phase_started_at = None
        self.paused_remaining = None

        self._prev_a_pressed = False
        self._a_pressed_at = None
        self._a_hold_handled = False
        self.show_summary = False
        self.colors_awarded = False  # this cycle's colors were already added
        self._rainbow_just_completed = False
        self._b_pressed_at = None
        self._b_hold_handled = False
        self._prev_b_pressed = False
        self.skipped_breaks = 0
        self.skipped_focus_sessions = 0

    @property
    def phase_duration(self):
        if self.phase == "FOCUS":
            return self.focus_duration
        if self.phase == "WRAP":
            return self.wrap_duration
        return self.break_duration

    def display_phase(self):
        if self.show_summary:
            return "SUMMARY"
        return "PAUSED" if self.paused else self.phase

    def display_text(self):
        if self.show_summary:
            return self.summary_lines()[0]
        if self.phase == "IDLE":
            return f"{self.session_minutes} MIN"
        return self.display_phase()

    def color(self, now=None):
        phase = self.display_phase()
        if phase == "SUMMARY":
            return PHASE_COLORS["COUNTER"]
        base = PHASE_COLORS[phase]
        if phase != "WRAP" or now is None or self.phase_started_at is None:
            return base
        # Wrap-up "breathes": full brightness at the start of each breath,
        # dimmest halfway through.
        angle = 2 * math.pi * (now - self.phase_started_at) / WRAP_BREATH_PERIOD
        level = WRAP_BREATH_MIN + (1 - WRAP_BREATH_MIN) * (0.5 + 0.5 * math.cos(angle))
        return tuple(round(channel * level) for channel in base)

    def summary_lines(self):
        lines = []
        if self.counter >= len(RAINBOW_COLORS):
            lines.append("NICE! SAME PLAN TOMORROW?")
        elif self.skipped_breaks >= 2:
            lines.append("TRY TAKING YOUR BREAKS")
        elif self.skipped_focus_sessions >= 2:
            lines.append("TRY SHORTER SESSIONS")
        else:
            lines.append("KEEP GOING TOMORROW")
        return lines

    def rainbow_colors(self):
        return RAINBOW_COLORS[:self.counter]

    def start_focus(self, now):
        self.phase = "FOCUS"
        self.phase_started_at = now
        self.paused = False
        self.colors_awarded = False

    def award_colors(self):
        """Add this cycle's rainbow colors once (30 MIN: 1, 60 MIN: 2)."""
        if self.colors_awarded:
            return
        self.colors_awarded = True
        full = len(RAINBOW_COLORS)
        before = self.counter
        colors_earned = 2 if self.session_minutes == 60 else 1
        self.counter = min(full, self.counter + colors_earned)
        if before < full and self.counter == full:
            self._rainbow_just_completed = True

    def return_to_idle(self):
        self.phase = "IDLE"
        self.phase_started_at = None
        self.paused = False
        self.paused_remaining = None
        if self._rainbow_just_completed:
            # Rainbow finished this cycle: open the summary once back at idle.
            self._rainbow_just_completed = False
            self.show_summary = True

    def finish_cycle(self):
        self.award_colors()
        self.return_to_idle()


def handle_button_a(state, now, a_pressed):
    """Tap A to toggle; hold A on idle for two seconds to show the summary."""
    if a_pressed:
        if state._a_pressed_at is None:
            state._a_pressed_at = now
        elif (
            not state._a_hold_handled
            and state.phase == "IDLE"
            and now - state._a_pressed_at >= HOLD_DURATION
        ):
            state.show_summary = True
            state._a_hold_handled = True
    elif state._prev_a_pressed:
        if not state._a_hold_handled:
            print("Button A pressed: toggling session")
            if state.show_summary:
                state.show_summary = False
            elif state.phase == "IDLE":
                state.start_focus(now)
            elif state.paused:
                elapsed_before_pause = state.phase_duration - state.paused_remaining
                state.phase_started_at = now - elapsed_before_pause
                state.paused = False
            else:
                state.paused_remaining = max(0, state.phase_duration - (now - state.phase_started_at))
                state.paused = True
        if not state._a_hold_handled:
            state.show_summary = False
        state._a_pressed_at = None
        state._a_hold_handled = False
    state._prev_a_pressed = a_pressed



def handle_button_b(state, now, b_pressed, hold_duration=HOLD_DURATION):
    """Tap B on idle to switch length; hold B to skip the current phase."""
    if b_pressed:
        if state._b_pressed_at is None:
            state._b_pressed_at = now
        elif not state._b_hold_handled and now - state._b_pressed_at >= hold_duration:
            print("Button B held for", hold_duration, "seconds")
            state.show_summary = False
            if state.phase == "FOCUS":
                # Skipped before wrap-up: no color.
                state.skipped_focus_sessions += 1
                state.return_to_idle()
            elif state.phase == "WRAP":
                # Focus is basically done, so the color counts now.
                state.award_colors()
                state.phase = "BREAK"
                state.phase_started_at = now
                state.paused = False
                state.paused_remaining = None
            elif state.phase == "BREAK":
                # Keeps any color already earned by skipping wrap-up.
                state.skipped_breaks += 1
                state.return_to_idle()
            state._b_hold_handled = True
    elif state._prev_b_pressed:
        if not state._b_hold_handled and state.phase == "IDLE":
            state.session_minutes = 60 if state.session_minutes == 30 else 30
            config = SESSION_CONFIG[state.session_minutes]
            state.focus_duration = config["focus"]
            state.wrap_duration = config["wrap"]
            state.break_duration = config["break"]
            print("Selected", state.session_minutes, "minute session")
        state._b_pressed_at = None
        state._b_hold_handled = False
    state._prev_b_pressed = b_pressed


def advance_phase(state, now):
    """Advance through FOCUS, WRAP, BREAK, then return to IDLE."""
    if state.phase in ("FOCUS", "WRAP", "BREAK") and not state.paused:
        if now - state.phase_started_at >= state.phase_duration:
            if state.phase == "FOCUS":
                state.phase = "WRAP"
                state.phase_started_at = now
            elif state.phase == "WRAP":
                state.phase = "BREAK"
                state.phase_started_at = now
            else:
                state.finish_cycle()


def tick(state, now, a_pressed, b_pressed):
    """One full update for a display frame: buttons, then phase advance."""
    handle_button_a(state, now, a_pressed)
    handle_button_b(state, now, b_pressed)
    advance_phase(state, now)
    return state
