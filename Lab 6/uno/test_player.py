"""Input and player logic, with the MQTT client and sensor faked. Run with: python -m unittest test_player"""

import json
import os
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest import mock

import hardware
import player as player_module
from hardware import Controls, classify_color, load_references
from player import Player


class FakeClient:
    def __init__(self):
        self.sent = []

    def publish(self, topic, payload, qos=0):
        self.sent.append((topic, json.loads(payload)))


def make_player(cards, **state):
    with mock.patch.object(player_module, 'connect', lambda *a: FakeClient()):
        player = Player('t', 'ana')
    full = {'game': 1, 'status': 'playing', 'players': ['ana', 'bea', 'cam'], 'current': 'ana', 'direction': 1,
            'top': 'R5', 'color': 'R', 'turn': 3, 'uno': None, 'last': '', 'winner': None,
            'counts': {'ana': len(cards), 'bea': 7, 'cam': 7}}
    full.update(state)
    deliver(player, player.topics.state, full)
    deliver(player, player.topics.hand('ana'), {'game': 1, 'cards': cards})
    return player


def deliver(player, topic, data):
    player.on_message(None, None, SimpleNamespace(topic=topic, payload=json.dumps(data).encode()))


class PlayerLogic(unittest.TestCase):
    def test_browse_wraps_around(self):
        player = make_player(['R1', 'G2', 'B3'])
        player.handle('prev')
        self.assertEqual(player.selected(), 'B3')
        player.handle('next')
        self.assertEqual(player.selected(), 'R1')

    def test_play_sends_once(self):
        player = make_player(['R1', 'G2'])
        player.handle('play')
        player.handle('play')  # a gesture read twice
        self.assertEqual(player.client.sent, [('IDD/t/uno/action/ana', {'type': 'play', 'card': 'R1', 'turn': 3})])

    def test_illegal_card_stays_on_this_pi(self):
        player = make_player(['G2'])
        player.handle('play')
        self.assertEqual(player.client.sent, [])
        self.assertEqual(player.view()['message'], "Can't play that")

    def test_not_your_turn(self):
        player = make_player(['R1'], current='bea')
        player.handle('play')
        player.handle('draw')
        self.assertEqual(player.client.sent, [])
        self.assertEqual(player.view()['message'], 'Not your turn')

    def test_wild_goes_through_color_picker(self):
        player = make_player(['G1', 'G2', 'W'])
        player.index = 2
        player.handle('play')
        self.assertEqual(player.mode(), 'pick')
        self.assertEqual(player.pick_color, 'G')  # most of the hand
        self.assertEqual(player.client.sent, [])
        player.handle(('pick', 'B'))
        self.assertEqual(player.view()['pick_color'], 'B')
        player.handle('confirm')
        self.assertEqual(player.client.sent[-1][1], {'type': 'play', 'card': 'W', 'color': 'B', 'turn': 3})
        self.assertEqual(player.mode(), 'turn')

    def test_wild_can_be_cancelled(self):
        player = make_player(['W'])
        player.handle('play')
        player.handle('cancel')
        self.assertEqual(player.mode(), 'turn')
        self.assertEqual(player.client.sent, [])

    def test_uno_call_sent_once_per_window(self):
        player = make_player(['R1'], uno={'player': 'bea', 'remaining': 4.0}, current='cam')
        self.assertEqual(player.mode(), 'uno')
        self.assertFalse(player.view()['mine'])
        player.handle('call')
        player.handle('call')
        self.assertEqual(player.client.sent, [('IDD/t/uno/action/ana', {'type': 'call'})])
        self.assertTrue(player.view()['called'])

    def test_selection_follows_card_when_hand_changes(self):
        player = make_player(['R1', 'R7'])
        player.index = 1
        deliver(player, player.topics.hand('ana'), {'game': 1, 'cards': ['R7', 'R1', 'R0', 'B9']})
        self.assertEqual(player.selected(), 'R7')

    def test_new_game_waits_for_new_hand(self):
        player = make_player(['R1'])
        deliver(player, player.topics.state, {'game': 2, 'status': 'playing', 'players': ['ana'], 'uno': None})
        self.assertEqual(player.mode(), 'connecting')


class ControlsLogic(unittest.TestCase):
    def setUp(self):
        self.controls = Controls.__new__(Controls)
        self.controls.sensor = SimpleNamespace(enable_gesture=False, proximity=0, color_data_ready=True,
                                               color_data=(0, 0, 0, 0), gesture=lambda: 0)
        self.controls.button_a = SimpleNamespace(value=True)
        self.controls.button_b = SimpleNamespace(value=True)
        self.controls.a_down = self.controls.b_down = None
        self.controls.proximity = 60
        self.controls.mode = None
        self.controls.covered_since = None
        self.controls.seen_color = None
        self.controls.seen_since = 0.0
        self.controls.warned = False
        self.controls.references = None

    def test_gesture_engine_only_runs_on_the_turn_screen(self):
        self.controls.set_mode('turn')
        self.assertTrue(self.controls.sensor.enable_gesture)
        self.controls.set_mode('uno')
        self.assertFalse(self.controls.sensor.enable_gesture)

    def test_swipes(self):
        self.controls.set_mode('turn')
        for code, event in {1: 'play', 2: 'draw', 3: 'prev', 4: 'next'}.items():
            self.controls.sensor.gesture = lambda code=code: code
            self.assertEqual(self.controls.poll(), [event])

    def test_a_passing_hand_does_not_call_uno(self):
        self.controls.set_mode('uno')
        self.controls.sensor.proximity = 200
        self.assertEqual(self.controls.poll(), [])
        self.controls.sensor.proximity = 0
        self.assertEqual(self.controls.poll(), [])
        self.controls.sensor.proximity = 200
        self.assertEqual(self.controls.poll(), [])

    def test_holding_a_hand_calls_uno(self):
        self.controls.set_mode('uno')
        self.controls.sensor.proximity = 200
        self.controls.poll()
        with mock.patch.object(hardware, 'HOLD_TO_CALL', 0):
            self.assertEqual(self.controls.poll(), ['call'])

    def test_holding_a_color_previews_then_confirms(self):
        self.controls.set_mode('pick')
        self.controls.sensor.proximity = 200
        self.controls.sensor.color_data = (150, 250, 800, 800)
        self.assertEqual(self.controls.poll(), [('pick', 'B')])
        self.assertEqual(self.controls.poll(), [])
        with mock.patch.object(hardware, 'HOLD_TO_PICK', 0):
            self.assertEqual(self.controls.poll(), ['confirm'])

    def test_buttons(self):
        self.controls.set_mode('turn')
        self.controls.button_a.value = False
        self.assertEqual(self.controls.poll(), [])
        self.controls.button_a.value = True
        self.assertEqual(self.controls.poll(), ['next'])
        self.controls.button_b.value = False
        self.controls.poll()
        self.controls.button_b.value = True
        self.assertEqual(self.controls.poll(), ['play'])
        self.controls.button_b.value = False
        self.controls.poll()
        self.controls.b_down = time.monotonic() - 1
        self.controls.button_b.value = True
        self.assertEqual(self.controls.poll(), ['draw'])

    def test_any_button_calls_uno(self):
        self.controls.set_mode('uno')
        self.controls.button_b.value = False
        self.controls.poll()
        self.controls.button_b.value = True
        self.assertEqual(self.controls.poll(), ['call'])

    def test_sensor_error_falls_back_to_buttons(self):
        def broken():
            raise OSError('i2c gone')
        self.controls.set_mode('turn')
        self.controls.sensor.gesture = broken
        self.assertEqual(self.controls.poll(), [])
        self.assertTrue(self.controls.warned)


class Calibration(unittest.TestCase):
    # Made up so that fixed thresholds get blue wrong: a blue object under warm light with lots of green in it
    READINGS = {'R': (900, 300, 200, 1000), 'Y': (800, 700, 200, 1200),
                'G': (250, 800, 300, 900), 'B': (300, 700, 450, 900)}

    def calibrated(self):
        sensor = SimpleNamespace(proximity=200, color_data=None)
        readings = iter(self.READINGS.values())

        def next_color(prompt):
            sensor.color_data = next(readings)
            return ''

        controls = SimpleNamespace(sensor=sensor, proximity=60)
        path = os.path.join(tempfile.mkdtemp(), 'colors.json')
        with mock.patch.object(hardware, 'Controls', lambda: controls), \
                mock.patch('builtins.input', next_color), mock.patch('builtins.print'), \
                mock.patch.object(hardware.time, 'sleep'):
            hardware.calibrate(path=path, check_seconds=0)
        return load_references(path)

    def test_fixed_thresholds_miss_this_blue(self):
        self.assertEqual(classify_color(*self.READINGS['B']), 'G')

    def test_calibration_recognises_every_object(self):
        references = self.calibrated()
        for color, reading in self.READINGS.items():
            self.assertEqual(classify_color(*reading, references=references), color)

    def test_nearer_and_farther_read_the_same(self):
        references = self.calibrated()
        r, g, b, c = self.READINGS['B']
        self.assertEqual(classify_color(r // 3, g // 3, b // 3, c // 3, references=references), 'B')

    def test_too_dark_is_no_color(self):
        self.assertIsNone(classify_color(1, 1, 1, 3, references=self.calibrated()))

    def run_with_answers(self, answers):
        sensor = SimpleNamespace(proximity=200, color_data=self.READINGS['R'])
        replies = iter(answers)

        def answer(prompt):
            reply, sensor.color_data = next(replies)
            return reply

        path = os.path.join(tempfile.mkdtemp(), 'colors.json')
        with mock.patch.object(hardware, 'Controls', lambda: SimpleNamespace(sensor=sensor, proximity=60)), \
                mock.patch('builtins.input', answer), mock.patch('builtins.print'), \
                mock.patch.object(hardware.time, 'sleep'):
            hardware.calibrate(path=path, check_seconds=0)
        return load_references(path)

    def test_yellow_can_be_skipped(self):
        references = self.run_with_answers([('', self.READINGS['R']), ('s', None), ('', self.READINGS['G']),
                                            ('', self.READINGS['B'])])
        self.assertEqual(sorted(references), ['B', 'G', 'R'])
        for color in 'RGB':
            self.assertEqual(classify_color(*self.READINGS[color], references=references), color)

    def test_one_color_is_not_enough(self):
        references = self.run_with_answers([('', self.READINGS['R']), ('s', None), ('s', None), ('s', None)])
        self.assertIsNone(references)

    def test_too_far_asks_again_instead_of_saving_room_light(self):
        room_light = (5090, 3000, 2450, 10360)
        steps = iter([(1, room_light), (200, self.READINGS['R']), (200, self.READINGS['Y']),
                      (200, self.READINGS['G']), (200, self.READINGS['B'])])
        sensor = SimpleNamespace(proximity=0, color_data=None)

        def answer(prompt):
            sensor.proximity, sensor.color_data = next(steps)
            return ''

        path = os.path.join(tempfile.mkdtemp(), 'colors.json')
        with mock.patch.object(hardware, 'Controls', lambda: SimpleNamespace(sensor=sensor, proximity=60)), \
                mock.patch('builtins.input', answer), mock.patch('builtins.print'), \
                mock.patch.object(hardware.time, 'sleep'):
            hardware.calibrate(path=path, check_seconds=0)
        references = load_references(path)
        self.assertEqual(classify_color(*self.READINGS['R'], references=references), 'R')
        self.assertGreater(references['R'][0], 0.55)  # the red object, not the room's 0.48

    def test_no_calibration_file(self):
        self.assertIsNone(load_references('/nonexistent/colors.json'))


if __name__ == '__main__':
    unittest.main()
