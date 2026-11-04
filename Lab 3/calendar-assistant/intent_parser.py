import datetime
import re
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("America/New_York")
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def parse_weekday_date(text, now=None):
    """Bare weekdays include today; 'next' weekdays are strictly in the future."""
    match = re.search(r"\b(?:(next|this)\s+)?(" + "|".join(WEEKDAYS) + r")\b", text.lower())
    if not match:
        return None
    now = now or datetime.datetime.now(TIMEZONE)
    today = now.astimezone(TIMEZONE).date()
    days_ahead = (WEEKDAYS.index(match.group(2)) - today.weekday()) % 7
    if match.group(1) == "next" and days_ahead == 0:
        days_ahead = 7
    return today + datetime.timedelta(days=days_ahead)

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
}


def normalize_time_text(text):
    """Accept Whisper's dotted or spaced AM/PM spellings."""
    text = text.lower().strip()
    text = re.sub(r"\b([ap])\s*\.?\s*m\b\.?", r"\1m", text)
    return text.rstrip(".?!,")


def parse_intent(text, now=None):
    text = text.lower().strip().rstrip(".?!,")

    # Exit
    if text in ["quit", "exit", "bye", "goodbye", "that's all", "thats all"]:
        return {
            "intent": "exit"
        }

    # Location questions should come before "next"
    # because "Where is my next event?" contains both.
    if "where" in text or "location" in text:
        return {
            "intent": "event_location"
        }

    # Creating an event should come before today/tomorrow,
    # because "schedule something tomorrow" contains "tomorrow".
    if re.match(r"^(?:(?:please|can you|could you|help me)\s+)*(?:schedule|create|add)\b", text):
        return {
            "intent": "create_event"
        }

    if "free" in text and re.search(r"\b(?:after|at)\b", text):
        return {"intent": "check_availability", "text": text}

    # Weekly free time
    if ("free" in text and "week" in text
        and (
            "how many hours" in text
            or "how much time" in text
        )
    ):
        return {
            "intent": "free_hours_week"
        }

    # Ask when free during a particular day
    if "free" in text and (
        "when" in text
        or "what time" in text
        or "what times" in text
    ):
        if "tomorrow" in text:
            return {
                "intent": "free_intervals_day",
                "day": "tomorrow"
            }

        if "today" in text:
            return {
                "intent": "free_intervals_day",
                "day": "today"
            }

    # Next event/class
    if (
        "next event" in text
        or "next class" in text
        or "what's next" in text
        or "whats next" in text
    ):
        return {
            "intent": "next_event"
        }

    # Weekday schedule requests. Availability and creation keep their own intents.
    if "free" not in text:
        day = parse_weekday_date(text, now)
        if day is not None:
            return {"intent": "day_events", "day": day}

    # Tomorrow
    if "tomorrow" in text:
        return {
            "intent": "tomorrow_events"
        }

    # Today
    if "today" in text:
        return {
            "intent": "today_events"
        }

    return {
        "intent": "unknown"
    }


def parse_create_event(text, now=None):
    """
    Example supported input:

    Schedule a two-hour study session tomorrow at 6 PM
    Create a one hour gym session tomorrow at 7:30 PM
    Add a 2 hour meeting today at 4 PM
    """

    text = normalize_time_text(text)

    pattern = (
        r"(?:schedule|create|add)"
        r"(?: me)?"
        r"(?: a| an)?\s+"
        r"(?P<duration>\d+|one|two|three|four|five|six)"
        r"[- ]?hour(?:s)?"
        r"[- ]*"
        r"(?P<title>.+?)\s+"
        r"(?P<day>today|tomorrow)\s+"
        r"(?:at|after)\s+"
        r"(?P<hour>\d{1,2})"
        r"(?::(?P<minute>\d{2}))?\s*"
        r"(?P<ampm>am|pm)"
    )

    match = re.search(pattern, text)

    if not match:
        return None

    # Duration
    duration_text = match.group("duration")

    if duration_text.isdigit():
        duration_hours = int(duration_text)
    else:
        duration_hours = NUMBER_WORDS[duration_text]

    # Day
    now = now or datetime.datetime.now(TIMEZONE)
    today = now.astimezone(TIMEZONE).date()

    if match.group("day") == "tomorrow":
        day = today + datetime.timedelta(days=1)
    else:
        day = today

    # Time
    hour = int(match.group("hour"))
    minute = int(match.group("minute") or 0)
    ampm = match.group("ampm")

    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        return {"error": "invalid_time"}
    if not 1 <= duration_hours <= 24:
        return {"error": "invalid_duration"}

    if ampm == "pm" and hour != 12:
        hour += 12

    if ampm == "am" and hour == 12:
        hour = 0

    start = datetime.datetime.combine(
        day,
        datetime.time(hour, minute),
        tzinfo=TIMEZONE
    )

    if start <= now:
        return {"error": "past_time"}

    end = start + datetime.timedelta(hours=duration_hours)

    return {
        "title": match.group("title").strip().title(),
        "start": start,
        "end": end,
    }


def parse_availability(text, now=None):
    """Bare times mean PM; 'after' checks until midnight, 'at' for one hour."""
    text = normalize_time_text(text)
    match = re.search(
        r"\b(?P<mode>after|at)\s+(?P<hour>\d{1,2}|one|two|three|four|five|six)"
        r"(?::(?P<minute>\d{2}))?\s*(?P<ampm>am|pm)?\b", text
    )
    if not match:
        return {"error": "missing_time"}
    raw_hour = match.group("hour")
    hour = int(raw_hour) if raw_hour.isdigit() else NUMBER_WORDS[raw_hour]
    minute = int(match.group("minute") or 0)
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        return {"error": "invalid_time"}
    ampm = match.group("ampm") or "pm"
    hour = hour % 12 + (12 if ampm == "pm" else 0)
    now = now or datetime.datetime.now(TIMEZONE)
    day = now.astimezone(TIMEZONE).date()
    if "tomorrow" in text:
        day += datetime.timedelta(days=1)
    start = datetime.datetime.combine(day, datetime.time(hour, minute), tzinfo=TIMEZONE)
    if start <= now:
        return {"error": "past_time"}
    end = (datetime.datetime.combine(day + datetime.timedelta(days=1), datetime.time.min, tzinfo=TIMEZONE)
           if match.group("mode") == "after" else start + datetime.timedelta(hours=1))
    return {"start": start, "end": end, "mode": match.group("mode")}
