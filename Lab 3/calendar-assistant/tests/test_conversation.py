import datetime
import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from intent_parser import TIMEZONE, parse_intent, parse_create_event, parse_availability, parse_weekday_date


class ParserTests(unittest.TestCase):
    now = datetime.datetime(2026, 10, 3, 10, tzinfo=TIMEZONE)

    def test_weekday_resolution(self):
        monday = datetime.datetime(2026, 10, 5, 10, tzinfo=TIMEZONE)
        self.assertEqual(parse_weekday_date("on Monday", monday), datetime.date(2026, 10, 5))
        self.assertEqual(parse_weekday_date("next Monday", monday), datetime.date(2026, 10, 12))
        self.assertEqual(parse_weekday_date("on Thursday", monday), datetime.date(2026, 10, 8))
        self.assertEqual(parse_weekday_date("on Sunday", monday), datetime.date(2026, 10, 11))
        sunday = monday + datetime.timedelta(days=6)
        self.assertEqual(parse_weekday_date("Monday", sunday), datetime.date(2026, 10, 12))
        year_end = datetime.datetime(2026, 12, 31, 10, tzinfo=TIMEZONE)
        self.assertEqual(parse_weekday_date("Friday", year_end), datetime.date(2027, 1, 1))
        for weekday in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            self.assertEqual(parse_intent(f"What's my schedule on {weekday}?", monday)["intent"], "day_events")
        self.assertEqual(parse_intent("Schedule a meeting on Monday", monday)["intent"], "create_event")


    def test_schedule_queries_and_commands(self):
        for phrase in ["What's my schedule today?", "Show my schedule today", "What is on my schedule today"]:
            self.assertEqual(parse_intent(phrase)["intent"], "today_events")
        self.assertEqual(parse_intent("What's my schedule tomorrow?")["intent"], "tomorrow_events")
        self.assertEqual(parse_intent("Help me schedule a two-hour study session tomorrow at 6 PM")["intent"], "create_event")

    def test_invalid_and_past_creation(self):
        for time in ["0 PM", "13 PM", "6:75 PM"]:
            self.assertEqual(parse_create_event(f"Add a 2 hour meeting tomorrow at {time}", self.now)["error"], "invalid_time")
        self.assertEqual(parse_create_event("Add a 0 hour meeting tomorrow at 6 PM", self.now)["error"], "invalid_duration")
        self.assertEqual(parse_create_event("Add a 2 hour meeting today at 9 AM", self.now)["error"], "past_time")
        event = parse_create_event("Schedule a two-hour study session tomorrow at 6 PM", self.now)
        self.assertEqual(event["start"].hour, 18)
        self.assertEqual(event["end"] - event["start"], datetime.timedelta(hours=2))

    def test_availability_windows(self):
        interval = parse_availability("Am I free after 6?", self.now)
        self.assertEqual(interval["start"].hour, 18)
        self.assertEqual(interval["end"].date(), self.now.date() + datetime.timedelta(days=1))
        interval = parse_availability("Am I free tomorrow at 6:30 AM?", self.now)
        self.assertEqual(interval["start"].hour, 6)
        self.assertEqual(interval["end"] - interval["start"], datetime.timedelta(hours=1))
        self.assertEqual(parse_availability("Am I free at 9 AM today?", self.now)["error"], "past_time")
        self.assertEqual(parse_availability("Am I free tomorrow after 13 PM?", self.now)["error"], "invalid_time")


class ConversationTests(unittest.TestCase):
    def run_dialogue(self, questions, events):
        calendar = ModuleType("calendar_client")
        for name in ["get_events_for_day", "get_today_events", "get_tomorrow_events", "get_next_event", "get_free_hours_this_week", "get_free_intervals_for_day", "is_free", "create_event", "format_events", "format_location", "friendly_title"]:
            setattr(calendar, name, Mock())
        calendar.get_today_events.return_value = events
        calendar.get_events_for_day.return_value = events
        calendar.get_next_event.return_value = events[0] if events else None
        calendar.format_events.return_value = "Your schedule."
        calendar.friendly_title.side_effect = lambda title: title
        calendar.format_location.side_effect = lambda event: event.get("location", "No location listed.")
        calendar.is_free.return_value = True
        speech = ModuleType("speech")
        speech.listen = Mock(side_effect=questions)
        speech.speak = Mock()
        ui = ModuleType("ui")
        for name in ["show_ready", "show_listening", "show_processing", "show_speaking"]:
            setattr(ui, name, Mock())
        with patch.dict(sys.modules, calendar_client=calendar, speech=speech, ui=ui):
            runpy.run_path(str(ROOT / "app.py"))
        return calendar, [call.args[0] for call in speech.speak.call_args_list]

    def test_weekday_schedule_and_location(self):
        calendar, replies = self.run_dialogue(
            ["What do I have on Thursday?", "Where is it?", "Goodbye"],
            [{"summary": "Meeting", "location": "Library"}],
        )
        calendar.get_events_for_day.assert_called_once()
        day = calendar.get_events_for_day.call_args.args[0]
        self.assertEqual(day.weekday(), 3)
        self.assertIn(f"On {day.strftime('%A, %B %-d')}, Your schedule.", replies)
        self.assertIn("Meeting: Library", replies)

    def test_location_clarification(self):
        events = [{"summary": "Study session", "location": "Library"}, {"summary": "Team meeting", "location": "Room 141"}]
        _, replies = self.run_dialogue(["What's my schedule today?", "Where is it?", "Team meeting", "Goodbye"], events)
        self.assertTrue(any("Which event" in reply for reply in replies))
        self.assertIn("Team meeting: Room 141", replies)

    def test_direct_next_location(self):
        calendar, replies = self.run_dialogue(["Where is my next event?", "Goodbye"], [{"summary": "Meeting", "location": "Library"}])
        calendar.get_next_event.assert_called_once()
        self.assertIn("Meeting: Library", replies)

    def test_availability_and_invalid_creation(self):
        calendar, replies = self.run_dialogue(["Am I free tomorrow after 6?", "Add a 2 hour meeting tomorrow at 13 PM", "Goodbye"], [])
        calendar.is_free.assert_called_once()
        calendar.create_event.assert_not_called()
        self.assertTrue(any("Yes, you are free" in reply for reply in replies))
        self.assertTrue(any("valid time" in reply for reply in replies))


if __name__ == "__main__":
    unittest.main()
