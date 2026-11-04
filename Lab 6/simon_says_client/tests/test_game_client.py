import unittest
from game_client import classify, GameState, event_topic, parse_message


class SensorTests(unittest.TestCase):
    def test_original_thresholds_and_proximity_priority(self):
        self.assertEqual(classify(201, (100, 0, 0, 100)), 'close')
        self.assertEqual(classify(200, (120, 60, 50, 51)), 'red')
        self.assertEqual(classify(0, (40, 100, 40, 100)), 'green')
        self.assertEqual(classify(0, (10, 10, 70, 100)), 'blue')
        self.assertIsNone(classify(0, (100, 50, 20, 50)))
        self.assertIsNone(classify(0, (100, 50, 20, 100)))

    def test_thresholds_are_tunable(self):
        self.assertEqual(classify(100, (0, 0, 0, 0), proximity=99), 'close')
        self.assertEqual(classify(0, (70, 50, 50, 25), clear=20, margin=10), 'red')


class ProtocolTests(unittest.TestCase):
    def test_topics_and_message_parsing(self):
        self.assertEqual(event_topic('pi2'), 'IDD/simon_says_team/simon/pi2/event')
        self.assertEqual(event_topic('pi1'), 'IDD/simon_says_team/simon/pi1/event')
        self.assertEqual(parse_message('display:SIMON SAYS: RED'), ('display', 'SIMON SAYS: RED'))
        self.assertEqual(parse_message('result:BOOM!'), ('result', 'BOOM!'))
        self.assertIsNone(parse_message('other:blah'))

    def test_one_action_per_round_and_none_between_rounds(self):
        state = GameState(settle_seconds=0.15)
        self.assertIsNone(state.sample('red', 0))
        state.sample(None, 0.1)
        state.message('display', 'SIMON SAYS: RED', 1)
        self.assertIsNone(state.sample('red', 1.05))
        self.assertEqual(state.sample('red', 1.16), 'red')
        self.assertIsNone(state.sample('red', 1.3))
        state.sample(None, 1.4)
        self.assertIsNone(state.sample('blue', 1.5))
        state.message('result', 'BOOM!', 2)
        state.sample(None, 2.1)
        self.assertIsNone(state.sample('green', 2.2))

    def test_fakeout_and_wrong_action_are_not_filtered(self):
        for text, action in [('FIRST TO SHOW [RED] WINS!', 'blue'),
                             ('SIMON SAYS: FIRST TO SHOW [RED] WINS!', 'green')]:
            state = GameState(settle_seconds=0)
            state.sample(None, 0)
            state.message('display', text, 1)
            self.assertEqual(state.sample(action, 1.1), action)

    def test_held_action_requires_release(self):
        state = GameState(settle_seconds=0)
        state.sample('red', 0)
        state.message('display', 'SIMON SAYS: RED', 1)
        self.assertIsNone(state.sample('red', 1.1))
        state.sample(None, 1.2)
        self.assertEqual(state.sample('red', 1.3), 'red')

    def test_result_cancels_pending_and_game_over_does_not_arm(self):
        state = GameState(settle_seconds=0.15)
        state.sample(None, 0)
        state.message('display', 'ROUND', 1)
        state.sample('red', 1.01)
        state.message('result', 'CAUGHT YOU!', 1.05)
        self.assertIsNone(state.sample('red', 1.2))
        state.sample(None, 2)
        state.message('display', 'GAME OVER! PLAYER 2 WINS THE MATCH!', 3)
        self.assertIsNone(state.sample('red', 3.2))

class PasswordTests(unittest.TestCase):
    def test_environment_password_skips_prompt(self):
        from unittest.mock import patch
        import game_client
        with patch.dict('os.environ', {'MQTT_PASSWORD': 'example-value'}), \
             patch('getpass.getpass') as prompt:
            self.assertEqual(game_client.mqtt_password(), 'example-value')
            prompt.assert_not_called()

    def test_password_prompt_when_environment_missing(self):
        from unittest.mock import patch
        import game_client
        with patch.dict('os.environ', {}, clear=True), \
             patch('getpass.getpass', return_value='example-value') as prompt:
            self.assertEqual(game_client.mqtt_password(), 'example-value')
            prompt.assert_called_once()


if __name__ == '__main__':
    unittest.main()
