import json
import unittest

from desk_morning import validate_answer


class ModelValidationTests(unittest.TestCase):
    def setUp(self):
        self.facts = {
            'valid_samples': 3, 'samples_with_people': 2, 'max_people': 1,
            'last_person_detection': '2026-11-01T15:40:40.066-05:00',
            'last_sample_time': '2026-11-01T15:40:50.381-05:00',
            'last_sample_people': 0, 'error_samples': 0, 'long_gap_count': 0,
            'observation_seconds': 30.026, 'session_closed': True,
        }

    def test_accepts_only_the_recorded_facts(self):
        self.assertEqual(validate_answer(json.dumps(self.facts), self.facts), [])

    def test_rejects_people_sum_and_invented_hour(self):
        answer = dict(self.facts, max_people=2, observation_seconds=3600)
        errors = validate_answer(json.dumps(answer), self.facts)
        self.assertTrue(any('max_people' in e for e in errors))
        self.assertTrue(any('observation_seconds' in e for e in errors))

    def test_rejects_added_sleep_claim_and_missing_final_sample(self):
        answer = dict(self.facts, everyone_asleep=True)
        del answer['last_sample_people']
        errors = validate_answer(json.dumps(answer), self.facts)
        self.assertTrue(any('everyone_asleep' in e for e in errors))
        self.assertTrue(any('last_sample_people' in e for e in errors))

    def test_boolean_is_not_a_person_count(self):
        answer = dict(self.facts, max_people=True)
        self.assertTrue(validate_answer(json.dumps(answer), self.facts))

    def test_rejects_prose_non_objects_and_non_finite_numbers(self):
        for raw in ('There were two people.', '[]', 'null',
                    json.dumps(dict(self.facts, observation_seconds=float('nan')))):
            with self.subTest(raw=raw):
                self.assertTrue(validate_answer(raw, self.facts))


if __name__ == '__main__':
    unittest.main()
