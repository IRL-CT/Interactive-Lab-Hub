import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# read/create events and check availability.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
]


def get_credentials():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)

            creds = flow.run_local_server(
                host="localhost",
                port=8080,
                open_browser=False
            )

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def main():
    creds = get_credentials()

    service = build("calendar", "v3", credentials=creds)

    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found.")
        return

    print("\nUpcoming events:\n")

    for event in events:
        start = event["start"].get(
            "dateTime",
            event["start"].get("date")
        )

        summary = event.get("summary", "Untitled event")

        print(f"{start} - {summary}")


if __name__ == "__main__":
    main()
