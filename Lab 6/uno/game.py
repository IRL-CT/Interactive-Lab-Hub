"""
UNO rules. No MQTT or hardware in here, so it can be tested on its own.

Cards are short strings: R5 (red 5), GS (green skip), BR (blue reverse),
YD (yellow draw two), W (wild), W4 (wild draw four).
"""

import random

COLORS = 'RYGB'
HAND_SIZE = 7
UNO_WINDOW = 4.0  # seconds everyone gets to race for the sensor


def build_deck():
    """The standard 108 cards"""
    deck = []
    for color in COLORS:
        deck.append(f'{color}0')
        for value in '123456789SRD':
            deck += [f'{color}{value}'] * 2
    return deck + ['W'] * 4 + ['W4'] * 4


def card_color(card):
    """R, Y, G or B. None for wilds, which have no color of their own."""
    return None if card.startswith('W') else card[0]


def card_value(card):
    return card if card.startswith('W') else card[1:]


def is_legal(card, top, color, hand):
    """Can this card go on the pile? color is the active color, which a wild may have changed."""
    if card == 'W':
        return True
    if card == 'W4':
        # Only allowed when you have nothing in the active color. No bluffing or challenges.
        return not any(card_color(c) == color for c in hand)
    return card_color(card) == color or card_value(card) == card_value(top)


class Game:
    def __init__(self, players, seed=None):
        self.players = list(players)
        self.rng = random.Random(seed)
        self.deck = build_deck()
        self.rng.shuffle(self.deck)
        self.hands = {p: [self.deck.pop() for _ in range(HAND_SIZE)] for p in self.players}

        # The first card has to be a number, so nothing happens to the first player
        while not card_value(self.deck[-1]).isdigit():
            self.deck.insert(0, self.deck.pop())
        self.discard = [self.deck.pop()]

        self.color = card_color(self.discard[-1])
        self.current = 0
        self.direction = 1
        self.turn = 0  # goes up every time the turn moves, so late actions can be spotted
        self.winner = None
        self.uno = None  # {'player', 'deadline'} while the table is racing to the sensor
        self.last = f'{self.players[0]} goes first'

    @property
    def top(self):
        return self.discard[-1]

    @property
    def current_player(self):
        return self.players[self.current]

    def _next_index(self, steps=1):
        return (self.current + self.direction * steps) % len(self.players)

    def _advance(self, steps=1):
        self.current = self._next_index(steps)
        self.turn += 1

    def _deal(self, player, count):
        """Give up to count cards. Returns how many there actually were."""
        dealt = 0
        for _ in range(count):
            if not self.deck:
                # Reshuffle everything under the top card
                self.deck = self.discard[:-1]
                self.discard = self.discard[-1:]
                self.rng.shuffle(self.deck)
            if not self.deck:
                break
            self.hands[player].append(self.deck.pop())
            dealt += 1
        return dealt

    def _turn_error(self, player):
        if self.winner:
            return 'Game over'
        if self.uno:
            return 'Wait for UNO'
        if player != self.current_player:
            return 'Not your turn'
        return None

    def play(self, player, card, color=None, now=0.0):
        """Play a card. Returns an error message, or None if it worked."""
        error = self._turn_error(player)
        if error:
            return error
        hand = self.hands[player]
        if card not in hand:
            return 'Not in your hand'
        if not is_legal(card, self.top, self.color, hand):
            return "Can't play that"
        wild = card_color(card) is None
        if wild and (color is None or color not in COLORS):
            return 'Pick a color'

        hand.remove(card)
        self.discard.append(card)
        self.color = color if wild else card_color(card)
        self.last = f'{player} played {card}'

        if not hand:
            self.winner = player
            self.last = f'{player} wins!'
            return None
        if len(hand) == 1:
            self.uno = {'player': player, 'deadline': now + UNO_WINDOW}

        value = card_value(card)
        steps = 1
        if value == 'S':
            steps = 2
        elif value == 'R':
            self.direction *= -1
            if len(self.players) == 2:
                steps = 2  # with two players a reverse acts as a skip
        elif value in ('D', 'W4'):
            victim = self.players[self._next_index()]
            self._deal(victim, 2 if value == 'D' else 4)
            steps = 2
        self._advance(steps)
        return None

    def draw(self, player):
        """Draw one card, which ends your turn. Returns an error message or None."""
        error = self._turn_error(player)
        if error:
            return error
        self._deal(player, 1)
        self.last = f'{player} drew'
        self._advance()
        return None

    def call(self, player):
        """Someone reached the sensor first. Returns an error message or None."""
        if not self.uno:
            return 'Too late'
        owner = self.uno['player']
        self.uno = None
        if player == owner:
            self.last = f'{owner} called UNO!'
        else:
            self._deal(owner, 2)
            self.last = f'{player} caught {owner}: +2'
        return None

    def tick(self, now):
        """Close the UNO window if time ran out (nobody noticed, so no penalty). True if it closed."""
        if self.uno and now >= self.uno['deadline']:
            self.last = f"{self.uno['player']} got away with it"
            self.uno = None
            return True
        return False

    def public_state(self, now=0.0):
        """What everyone is allowed to see"""
        uno = None
        if self.uno:
            uno = {'player': self.uno['player'], 'remaining': max(0.0, self.uno['deadline'] - now)}
        return {
            'status': 'over' if self.winner else 'playing',
            'players': self.players,
            'counts': {p: len(h) for p, h in self.hands.items()},
            'current': self.current_player,
            'direction': self.direction,
            'top': self.top,
            'color': self.color,
            'turn': self.turn,
            'winner': self.winner,
            'uno': uno,
            'last': self.last,
        }
