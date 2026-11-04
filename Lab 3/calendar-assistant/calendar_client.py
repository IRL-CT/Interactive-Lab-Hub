import datetime
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
]

COURSE_NAMES = {
    "CS 5424": "Interactive Device Design",
    "CS 5854": "Networks and Markets",
    "TECH 5900": "Product Studio",
    "TECHIE 5310": "Business Fundamentals",
    "CS 5650": "Virtual and Augmented Reality",
}

TIMEZONE = ZoneInfo("America/New_York")

DAY_START_HOUR = 9
DAY_END_HOUR = 21


def get_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("calendar", "v3", credentials=creds)

# Returns the events you have scheduled for a particular day
def get_events_for_day(day):
    service = get_service()

    # Beginning of requested day in local timezone
    start = datetime.datetime.combine(day, datetime.time.min).astimezone()
    
    # Beginning of following day
    end = start + datetime.timedelta(days=1)

    result = service.events().list(
        calendarId="primary",
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    return result.get("items", [])

def get_today_events():
    today = datetime.date.today()
    return get_events_for_day(today)

def get_tomorrow_events():
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    return get_events_for_day(tomorrow)

def get_next_event():
    service = get_service()
    now = datetime.datetime.now().astimezone()

    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        maxResults=1,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = result.get("items", [])
    return events[0] if events else None

# def find_event(name):


def get_event_location(event):
    return event.get("location", "No location specified")

def get_busy_intervals(start, end):
    service = get_service()

    body = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "items": [
            {"id": "primary"}
        ]
    }

    result = service.freebusy().query(body=body).execute()
    busy = result["calendars"]["primary"]["busy"]
    intervals = []

    for period in busy:
        busy_start = datetime.datetime.fromisoformat(
            period["start"].replace("Z", "+00:00")
        ).astimezone(TIMEZONE)

        busy_end = datetime.datetime.fromisoformat(
            period["end"].replace("Z", "+00:00")
        ).astimezone(TIMEZONE)

        intervals.append((busy_start, busy_end))

    return intervals

# Am I free for this whole interval?
def is_free(start, end):
    busy = get_busy_intervals(start, end)
    return len(busy) == 0

# Starting at this time, am I free for at least 60 minutes
def is_free_at(start, duration_minutes=60):
    end = start + datetime.timedelta(minutes=duration_minutes)
    return is_free(start, end)

# When am I free tomorrow?
def get_free_intervals_for_day(day):
    day_start = datetime.datetime.combine(
        day,
        datetime.time(DAY_START_HOUR, 0),
        tzinfo=TIMEZONE
    )

    day_end = datetime.datetime.combine(
        day,
        datetime.time(DAY_END_HOUR, 0),
        tzinfo=TIMEZONE
    )

    busy = get_busy_intervals(day_start, day_end)
    # Sort busy periods
    busy.sort(key=lambda x: x[0])

    free = []
    current = day_start

    for busy_start, busy_end in busy:
        # Ignore portions outside our allowed window
        busy_start = max(busy_start, day_start)
        busy_end = min(busy_end, day_end)

        if busy_start > current:
            free.append((current, busy_start))
        current = max(current, busy_end)

    if current < day_end:
        free.append((current, day_end))

    return free

# How many hours am I free this week?
def get_free_hours_this_week():
    today = datetime.date.today()

    # Monday of the current week
    monday = today - datetime.timedelta(days=today.weekday())

    total_seconds = 0

    for i in range(7):
        day = monday + datetime.timedelta(days=i)
        free_intervals = get_free_intervals_for_day(day)
        for start, end in free_intervals:
            total_seconds += (end - start).total_seconds()

    return total_seconds / 3600

# Event creation
def create_event(title, start, end, location=None):
    service = get_service()

    event = {
        "summary": title,
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": "America/New_York",
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": "America/New_York",
        },
    }

    if location:
        event["location"] = location

    created_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    return created_event


# Convert the course code into the course name
def friendly_title(title):
    for code, name in COURSE_NAMES.items():
        if code in title:
            return name
    return title

# Formats the information of an event
def format_events(events, include_location=False, include_date=False):
    if not events:
        return "You don't have anything scheduled."

    parts = []

    for event in events:
        title = friendly_title(event.get("summary", "Untitled event"))
        start = event["start"]

        if "dateTime" in start:
            dt = datetime.datetime.fromisoformat(start["dateTime"])
            time_string = dt.strftime("%-I:%M %p")
            day_string = dt.strftime("%A")

            if include_date:
                text = f"{title} on {day_string} at {time_string}"
            else:
                text = f"{title} at {time_string}"

        else:
            if include_date:
                day = datetime.date.fromisoformat(start["date"])
                text = f"{title} on {day.strftime('%A')}, all day"
            else:
                text = f"{title}, all day"

        if include_location:
            location = event.get("location")
            if location:
                text += f" in {location}"
        parts.append(text)
    
    return ", ".join(parts)

# Formats the location of a given event
def format_location(event):
    location = event.get("location")
    if location:
        return location
    return "There is no location listed for that event."

if __name__ == "__main__":
    # print("TODAY:")
    # print(format_events(get_today_events()))

    # print("\nTOMORROW:")
    # print(format_events(get_tomorrow_events()))        

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    start = datetime.datetime.combine(
        tomorrow,
        datetime.time(18, 0),
        tzinfo=TIMEZONE
    )

    end = start + datetime.timedelta(hours=2)

    event = create_event(
        "Test Study Session",
        start,
        end
    )

    print("Created:", event["summary"])