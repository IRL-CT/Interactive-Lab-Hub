import unittest
from pet_logic import PetGame
from events import make_event

class GameTests(unittest.TestCase):
    def setUp(self): self.g = PetGame(0)
    def act(self, role, now): return self.g.apply(make_event(role, role, self.g.round_id), now)
    def fill(self):
        for now in (0, 3):
            for role in ('feed', 'play', 'rest'): self.act(role, now)
    def test_clamp(self):
        for n in range(7): self.act('feed', n * 3)
        self.assertEqual(self.g.values['fullness'], 100)
        self.assertEqual(self.g.values['energy'], 39)
        self.g.tick(2000)
        self.assertEqual(min(self.g.values.values()), 0)
    def test_decay(self):
        self.g.tick(14.99)
        self.assertEqual(self.g.values['energy'], 40)
        self.g.tick(45)
        self.assertEqual(self.g.values['energy'], 37)
    def test_mood(self):
        self.g.tick(150)
        self.assertEqual(self.g.mood, 'normal')
        self.g.tick(165)
        self.assertEqual(self.g.mood, 'needs_care')
    def test_win_and_freeze(self):
        self.fill()
        self.assertEqual(self.g.mood, 'happy')
        self.g.tick(12.99)
        self.assertEqual(self.g.status, 'playing')
        self.g.tick(1000)
        self.assertEqual(self.g.status, 'won')
        self.assertEqual(self.g.values['energy'], 80)
        self.assertFalse(self.act('feed', 1001)[0])
    def test_interrupted_happiness(self):
        self.g.values = dict.fromkeys(self.g.values, 70)
        self.g.happy_since = 6
        self.g.tick(16)
        self.assertEqual(self.g.status, 'playing')
        self.assertIsNone(self.g.happy_since)
    def test_decay_win_tie(self):
        self.g.values = dict.fromkeys(self.g.values, 70)
        self.g.happy_since = 5
        self.g.tick(15)
        self.assertEqual(self.g.status, 'playing')
    def test_duplicate_and_cooldown(self):
        e = make_event('feed', 'pi1', self.g.round_id)
        self.assertTrue(self.g.apply(e, 0)[0])
        self.assertEqual(self.g.apply(e, 4), (False, 'duplicate'))
        e2 = make_event('feed', 'pi1', self.g.round_id)
        self.assertTrue(self.g.apply(e2, 4)[0])
        e3 = make_event('feed', 'pi1', self.g.round_id)
        self.assertEqual(self.g.apply(e3, 5), (False, 'cooldown'))
        self.assertFalse(self.g.apply(e3, 10)[0])
    def test_reset(self):
        self.fill()
        old = make_event('feed', 'feed', self.g.round_id)
        reset = make_event('reset', 'admin', self.g.round_id)
        self.assertTrue(self.g.apply(reset, 4)[0])
        self.assertEqual(list(self.g.values.values()), [40, 40, 40])
        self.assertFalse(self.g.apply(old, 5)[0])
        self.assertFalse(self.g.apply(reset, 5)[0])
        self.assertIsNone(self.g.last_action)
    def test_one_role_cannot_win(self):
        for now in range(0, 100, 3): self.act('feed', now)
        self.assertEqual(self.g.status, 'playing')
