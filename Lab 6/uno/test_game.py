"""Rule checks. Run with: python -m unittest test_game"""

import unittest

from game import UNO_WINDOW, Game, build_deck, is_legal
from hardware import classify_color


def game_with(hands, top='R5', seed=1):
    """A game with chosen hands. First player in the dict goes first."""
    game = Game(list(hands), seed=seed)
    game.hands = {p: list(cards) for p, cards in hands.items()}
    game.discard = [top]
    game.color = top[0]
    return game


class Rules(unittest.TestCase):
    def test_deck_has_108_cards(self):
        deck = build_deck()
        self.assertEqual(len(deck), 108)
        self.assertEqual(deck.count('W4'), 4)
        self.assertEqual(deck.count('R0'), 1)
        self.assertEqual(deck.count('R7'), 2)

    def test_deal(self):
        game = Game(['a', 'b', 'c', 'd'], seed=2)
        self.assertTrue(all(len(h) == 7 for h in game.hands.values()))
        self.assertTrue(game.top[1:].isdigit())
        self.assertEqual(len(game.deck) + len(game.discard) + 28, 108)

    def test_legal_cards(self):
        self.assertTrue(is_legal('R9', 'R5', 'R', []))
        self.assertTrue(is_legal('G5', 'R5', 'R', []))
        self.assertFalse(is_legal('G6', 'R5', 'R', []))
        self.assertTrue(is_legal('GS', 'RS', 'R', []))
        self.assertTrue(is_legal('W', 'R5', 'R', ['R1']))
        self.assertFalse(is_legal('W4', 'R5', 'R', ['W4', 'R1']))
        self.assertTrue(is_legal('W4', 'R5', 'R', ['W4', 'G1']))
        self.assertTrue(is_legal('B2', 'W', 'B', []))
        self.assertFalse(is_legal('R2', 'W', 'B', []))

    def test_out_of_turn_and_bad_cards_are_refused(self):
        game = game_with({'a': ['R1', 'G9', 'W'], 'b': ['R2', 'R3'], 'c': ['R4', 'R6']})
        self.assertEqual(game.play('b', 'R2'), 'Not your turn')
        self.assertEqual(game.play('a', 'R2'), 'Not in your hand')
        self.assertEqual(game.play('a', 'G9'), "Can't play that")
        self.assertEqual(game.play('a', 'W'), 'Pick a color')
        self.assertEqual(game.play('a', 'W', 'Z'), 'Pick a color')
        self.assertEqual(game.turn, 0)
        self.assertEqual(len(game.hands['a']), 3)

    def test_skip(self):
        game = game_with({'a': ['RS', 'R1'], 'b': ['R2', 'R3'], 'c': ['R4', 'R6']})
        game.uno = None
        self.assertIsNone(game.play('a', 'RS'))
        game.uno = None
        self.assertEqual(game.current_player, 'c')

    def test_reverse(self):
        game = game_with({'a': ['RR', 'R1', 'R7'], 'b': ['R2', 'R3'], 'c': ['R4', 'R6']})
        self.assertIsNone(game.play('a', 'RR'))
        self.assertEqual(game.current_player, 'c')
        self.assertEqual(game.direction, -1)

    def test_reverse_with_two_players_is_a_skip(self):
        game = game_with({'a': ['RR', 'R1', 'R7'], 'b': ['R2', 'R3']})
        self.assertIsNone(game.play('a', 'RR'))
        self.assertEqual(game.current_player, 'a')

    def test_draw_two_hits_next_player_and_skips_them(self):
        game = game_with({'a': ['RD', 'R1', 'R7'], 'b': ['R2'], 'c': ['R4']})
        self.assertIsNone(game.play('a', 'RD'))
        self.assertEqual(len(game.hands['b']), 3)
        self.assertEqual(game.current_player, 'c')

    def test_wild_four_sets_color(self):
        game = game_with({'a': ['W4', 'G1', 'G2'], 'b': ['R2'], 'c': ['R4']})
        self.assertIsNone(game.play('a', 'W4', 'B'))
        self.assertEqual(len(game.hands['b']), 5)
        self.assertEqual(game.current_player, 'c')
        self.assertEqual(game.color, 'B')
        self.assertEqual(game.play('c', 'R4'), "Can't play that")

    def test_draw_ends_turn(self):
        game = game_with({'a': ['G1'], 'b': ['R2'], 'c': ['R4']})
        self.assertIsNone(game.draw('a'))
        self.assertEqual(len(game.hands['a']), 2)
        self.assertEqual(game.current_player, 'b')

    def test_empty_deck_reshuffles_discard(self):
        game = game_with({'a': ['G1'], 'b': ['R2'], 'c': ['R4']})
        game.deck = []
        game.discard = ['G7', 'B3', 'R5']
        self.assertIsNone(game.draw('a'))
        self.assertEqual(game.discard, ['R5'])
        self.assertEqual(len(game.deck), 1)

    def test_no_cards_left_anywhere_does_not_crash(self):
        game = game_with({'a': ['G1'], 'b': ['R2'], 'c': ['R4']})
        game.deck = []
        game.discard = ['R5']
        self.assertIsNone(game.draw('a'))
        self.assertEqual(game.current_player, 'b')

    def test_winning(self):
        game = game_with({'a': ['R1'], 'b': ['R2'], 'c': ['R4']})
        self.assertIsNone(game.play('a', 'R1'))
        self.assertEqual(game.winner, 'a')
        self.assertEqual(game.play('b', 'R2'), 'Game over')
        self.assertEqual(game.public_state()['status'], 'over')


class UnoRace(unittest.TestCase):
    def setUp(self):
        self.game = game_with({'a': ['R1', 'G9'], 'b': ['R2'], 'c': ['R4']})
        self.game.play('a', 'R1', now=100.0)

    def test_window_opens_and_pauses_play(self):
        self.assertEqual(self.game.uno, {'player': 'a', 'deadline': 100.0 + UNO_WINDOW})
        self.assertEqual(self.game.play('b', 'R2'), 'Wait for UNO')
        self.assertEqual(self.game.draw('b'), 'Wait for UNO')

    def test_owner_first_is_safe(self):
        self.assertIsNone(self.game.call('a'))
        self.assertEqual(len(self.game.hands['a']), 1)
        self.assertIsNone(self.game.uno)

    def test_someone_else_first_means_two_cards(self):
        self.assertIsNone(self.game.call('c'))
        self.assertEqual(len(self.game.hands['a']), 3)

    def test_second_call_loses_the_race_harmlessly(self):
        self.game.call('c')
        self.assertEqual(self.game.call('a'), 'Too late')
        self.assertEqual(self.game.call('b'), 'Too late')
        self.assertEqual(len(self.game.hands['a']), 3)

    def test_nobody_calls(self):
        self.assertFalse(self.game.tick(100.0 + UNO_WINDOW - 0.1))
        self.assertTrue(self.game.tick(100.0 + UNO_WINDOW))
        self.assertEqual(len(self.game.hands['a']), 1)
        self.assertIsNone(self.game.play('b', 'R2'))


class WholeGames(unittest.TestCase):
    def test_random_games_finish_and_keep_every_card(self):
        for seed in range(300):
            players = ['a', 'b', 'c', 'd'][:3 + seed % 2]
            game = Game(players, seed=seed)
            for moves in range(5000):
                game.uno = None
                player = game.current_player
                hand = game.hands[player]
                legal = [c for c in hand if is_legal(c, game.top, game.color, hand)]
                if legal:
                    self.assertIsNone(game.play(player, legal[0], 'RYGB'[moves % 4]))
                else:
                    self.assertIsNone(game.draw(player))
                total = len(game.deck) + len(game.discard) + sum(map(len, game.hands.values()))
                self.assertEqual(total, 108)
                if game.winner:
                    break
            self.assertIsNotNone(game.winner, f'seed {seed} did not finish')


class ColorSensor(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify_color(900, 200, 150, 800), 'R')
        self.assertEqual(classify_color(200, 800, 150, 800), 'G')
        self.assertEqual(classify_color(150, 250, 800, 800), 'B')
        self.assertEqual(classify_color(800, 700, 150, 900), 'Y')
        self.assertIsNone(classify_color(1, 1, 1, 3))


if __name__ == '__main__':
    unittest.main()
