import datetime

from calendar_client import (
    get_events_for_day,
    get_today_events,
    get_tomorrow_events,
    get_next_event,
    get_free_hours_this_week,
    get_free_intervals_for_day,
    is_free,
    create_event,
    format_events,
    format_location,
    friendly_title,
)

from intent_parser import parse_intent, parse_create_event, parse_availability, TIMEZONE
from speech import listen, speak
from ui import show_ready, show_listening, show_processing, show_speaking


pending_event = None
last_event = None
last_events = []
awaiting_location = False


# --------------------------------------------------
# Print AND speak assistant responses
# --------------------------------------------------
def reply(text):
    print("Assistant:", text)
    show_speaking(text)
    try:
        speak(text)
    finally:
        show_ready()


# --------------------------------------------------
# Opening
# --------------------------------------------------
opening = (
    "Hello! I am your personal calendar assistant. "
    "I can help you check your schedule, find free time, "
    "and create new events. How can I help you today?"
)

reply(opening)


while True:

    # --------------------------------------------------
    # Listen to the user
    # --------------------------------------------------
    raw_question = listen(
        on_listening=show_listening,
        on_processing=show_processing,
    ).strip()
    
    # Show the transcript after speech.py's "Listening..." message.
    print("You:", raw_question)

    # Normalize it
    question = raw_question.lower().rstrip(".?!,")

    if not question:
        reply("Sorry, I didn't hear anything.")
        continue

    # --------------------------------------------------
    # Resolve a location clarification against the events just discussed.
    if awaiting_location:
        if question in ["cancel", "never mind", "no"]:
            awaiting_location = False
            reply("Okay.")
            continue
        if parse_intent(question)["intent"] == "exit":
            reply("Goodbye!")
            break
        matches = [e for e in last_events if
                   friendly_title(e.get("summary", "Untitled event")).lower() in question
                   or question in friendly_title(e.get("summary", "Untitled event")).lower()]
        if len(matches) == 1:
            last_event = matches[0]
            awaiting_location = False
            reply(f"{friendly_title(last_event.get('summary', 'Untitled event'))}: {format_location(last_event)}")
        else:
            reply("Please say one of these event names: " + ", ".join(
                friendly_title(e.get("summary", "Untitled event")) for e in last_events) + ". Or say cancel.")
        continue

    # 1. Handle confirmation for a pending event
    # --------------------------------------------------
    if pending_event is not None:

        if question in [
            "yes", "yeah", "yep", "sure", "ok", "okay"
        ]:
            if pending_event["start"] <= datetime.datetime.now(TIMEZONE):
                pending_event = None
                reply("That time has already passed. Please choose a future time.")
                continue
            if not is_free(pending_event["start"], pending_event["end"]):
                pending_event = None
                reply("That time is now busy. Please choose another time.")
                continue
            create_event(
                pending_event["title"],
                pending_event["start"],
                pending_event["end"],
            )

            reply(
                f"Done. I created {pending_event['title']}."
            )

            pending_event = None
            continue

        elif question in [
            "no", "nope", "cancel", "never mind"
        ]:
            reply("Okay, I won't create it.")

            pending_event = None
            continue

        else:
            reply("Please say yes or no.")
            continue

    # --------------------------------------------------
    # 2. Understand what the user wants
    # --------------------------------------------------
    result = parse_intent(question)
    intent = result["intent"]

    # --------------------------------------------------
    # Today's schedule
    # --------------------------------------------------
    if intent == "today_events":
        events = get_today_events()

        last_events = events
        reply(format_events(events))

        if len(events) == 1:
            last_event = events[0]
        else:
            last_event = None

    # --------------------------------------------------
    # Tomorrow's schedule
    # --------------------------------------------------
    elif intent == "tomorrow_events":
        events = get_tomorrow_events()

        last_events = events
        reply(format_events(events))

        if len(events) == 1:
            last_event = events[0]
        else:
            last_event = None

    # --------------------------------------------------
    # Schedule for a named weekday
    # --------------------------------------------------
    elif intent == "day_events":
        day = result["day"]
        events = get_events_for_day(day)
        last_events = events
        last_event = events[0] if len(events) == 1 else None
        date_label = day.strftime("%A, %B %-d")
        reply(f"On {date_label}, {format_events(events)}")

    # --------------------------------------------------
    # Next event
    # --------------------------------------------------
    elif intent == "next_event":
        event = get_next_event()

        last_events = [event] if event else []
        if event:
            reply(
                format_events(
                    [event],
                    include_date=True,
                    include_location=True
                )
            )

            last_event = event

        else:
            reply(
                "You don't have any upcoming events."
            )

            last_event = None

    # --------------------------------------------------
    # Location
    # --------------------------------------------------
    elif intent == "event_location":

        if "next" in question:
            last_event = get_next_event()
            last_events = [last_event] if last_event else []
        else:
            matches = [e for e in last_events if
                       friendly_title(e.get("summary", "Untitled event")).lower() in question]
            if len(matches) == 1:
                last_event = matches[0]
            elif question not in ["where is it", "where is that", "where is that event", "what is its location"]:
                last_event = None

        if last_event:
            reply(f"{friendly_title(last_event.get('summary', 'Untitled event'))}: {format_location(last_event)}")
        elif last_events:
            awaiting_location = True
            reply("Which event do you mean? Say its name: " + ", ".join(
                friendly_title(e.get("summary", "Untitled event")) for e in last_events) + ".")
        else:
            reply("Which event do you mean? Ask about today's schedule, tomorrow's schedule, or your next event first, then ask for its location.")

    elif intent == "check_availability":
        interval = parse_availability(question)
        if interval.get("error"):
            reply("Please choose a future time, such as: Am I free tomorrow after 6 PM?")
            continue
        start, end = interval["start"], interval["end"]
        window = f"{start.strftime('%A at %-I:%M %p')} until {end.strftime('%A at %-I:%M %p')}"
        if is_free(start, end):
            reply(f"Yes, you are free from {window}.")
        else:
            reply(f"You have something scheduled between {window}.")

    # --------------------------------------------------
    # Free hours this week
    # --------------------------------------------------
    elif intent == "free_hours_week":
        hours = get_free_hours_this_week()

        reply(
            f"You have approximately {hours:.1f} "
            "free hours this week between 9 AM and 9 PM."
        )

    # --------------------------------------------------
    # When am I free today/tomorrow?
    # --------------------------------------------------
    elif intent == "free_intervals_day":

        if result["day"] == "tomorrow":
            day = (
                datetime.datetime.now(TIMEZONE).date()
                + datetime.timedelta(days=1)
            )
            day_name = "tomorrow"

        else:
            day = datetime.datetime.now(TIMEZONE).date()
            day_name = "today"

        free_intervals = get_free_intervals_for_day(day)

        if not free_intervals:
            reply(
                f"You don't have any free time {day_name} "
                "between 9 AM and 9 PM."
            )

        else:
            formatted_intervals = []

            for start, end in free_intervals:
                formatted_intervals.append(
                    f"{start.strftime('%-I:%M %p')} "
                    f"to {end.strftime('%-I:%M %p')}"
                )

            response = (
                f"You are free {day_name} from "
                + ", ".join(formatted_intervals)
                + "."
            )

            reply(response)

    # --------------------------------------------------
    # Create event
    # --------------------------------------------------
    elif intent == "create_event":

        event_data = parse_create_event(question)

        if event_data is None:
            reply(
                "Please include a duration, event name, today or tomorrow, and a time with AM or PM. "
                "For example: Schedule a two-hour study session tomorrow at 6 PM."
            )
            continue

        if event_data.get("error") == "past_time":
            reply(
                "That time has already passed."
            )
            continue

        if event_data.get("error"):
            reply("Please use a valid time from 1 to 12 AM or PM, and a duration between 1 and 24 hours.")
            continue

        start = event_data["start"]
        end = event_data["end"]

        if is_free(start, end):

            # Do NOT create it yet.
            # Wait until the user confirms.
            pending_event = event_data

            reply(
                f"You're free on {start.strftime('%A, %B %-d')} from "
                f"{start.strftime('%-I:%M %p')} to "
                f"{end.strftime('%-I:%M %p')}. "
                f"Would you like me to create "
                f"{event_data['title']}?"
            )

        else:
            reply(
                "You already have something scheduled "
                "during that time."
            )

    # --------------------------------------------------
    # Exit
    # --------------------------------------------------
    elif intent == "exit":
        reply("Goodbye!")
        break

    # --------------------------------------------------
    # Unknown
    # --------------------------------------------------
    else:
        reply(
            "Sorry, I didn't understand that."
        )
