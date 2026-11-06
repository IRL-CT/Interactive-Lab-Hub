#!/usr/bin/env python3
"""
UNO player. Run one on each Pi: it shows the game on the screen and sends what
the sensor and buttons pick up to the referee.

  --keyboard  type commands instead of using the sensor and buttons
  --bot       play automatically, to fill a seat when you are short a Pi
"""

import argparse
import json
import random
import threading
import time

from common import Topics, connect, valid_name
from game import COLORS, card_color, is_legal

JOIN_EVERY = 3.0
MESSAGE_TIME = 2.0


def sort_hand(cards):
    order = COLORS + 'W'
    return sorted(cards, key=lambda c: (order.index(c[0]), c))


class Player:
    def __init__(self, team, name):
        self.name = name
        self.topics = Topics(team)
        self.lock = threading.Lock()
        self.state = None
        self.state_time = 0.0
        self.cards = []
        self.cards_game = None
        self.index = 0
        self.pick_card = None
        self.pick_color = 'R'
        self.called_for = None  # the UNO window we already answered
        self.message = ''
        self.message_until = 0.0
        self.last_join = 0.0
        self.sent_turn = None
        self.client = connect(self.on_message, [self.topics.state, self.topics.hand(name), self.topics.notice(name)])

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode('UTF-8'))
        except ValueError:
            return
        with self.lock:
            if msg.topic == self.topics.state:
                if self.state and self.state.get('game') != data.get('game'):
                    self.pick_card = None
                self.state = data
                self.state_time = time.monotonic()
            elif msg.topic == self.topics.hand(self.name):
                selected = self.selected()
                self.cards = sort_hand(data['cards'])
                self.cards_game = data['game']
                # Stay on the same card when the hand changes
                if selected in self.cards:
                    self.index = self.cards.index(selected)
                self.index = min(self.index, max(0, len(self.cards) - 1))
            elif msg.topic == self.topics.notice(self.name):
                self.flash(data.get('text', ''))

    def flash(self, text):
        self.message = text
        self.message_until = time.monotonic() + MESSAGE_TIME

    def selected(self):
        return self.cards[self.index] if self.index < len(self.cards) else None

    def send(self, kind, **fields):
        self.client.publish(self.topics.action(self.name), json.dumps({'type': kind, **fields}), qos=1)

    def keep_joining(self):
        """Ask to join until the referee has us. The referee may start before or after we do."""
        now = time.monotonic()
        with self.lock:
            joined = self.state and self.name in self.state.get('players', [])
        if not joined and now - self.last_join >= JOIN_EVERY:
            self.last_join = now
            self.client.publish(self.topics.join, json.dumps({'name': self.name}), qos=1)

    def my_turn(self):
        return bool(self.state and self.state.get('status') == 'playing' and not self.state.get('uno')
                    and self.state.get('current') == self.name)

    def uno_key(self):
        """Identifies one UNO window, so we only answer it once"""
        return (self.state['game'], self.state['turn'], self.state['uno']['player'])

    def mode(self):
        status = self.state.get('status') if self.state else None
        if status is None:
            return 'connecting'
        if status in ('lobby', 'over'):
            return status
        if self.cards_game != self.state['game']:
            return 'connecting'
        if self.state.get('uno'):
            return 'uno'
        if self.pick_card and self.my_turn():
            return 'pick'
        return 'turn'

    def selected_legal(self):
        card = self.selected()
        return bool(card and is_legal(card, self.state['top'], self.state['color'], self.cards))

    def handle(self, event):
        """Act on one input event"""
        with self.lock:
            mode = self.mode()
            if mode == 'turn':
                if event == 'next' and self.cards:
                    self.index = (self.index + 1) % len(self.cards)
                elif event == 'prev' and self.cards:
                    self.index = (self.index - 1) % len(self.cards)
                elif event in ('play', 'draw'):
                    self.act(event)
            elif mode == 'uno' and event == 'call':
                key = self.uno_key()
                if self.called_for != key:
                    self.called_for = key
                    self.send('call')
            elif mode == 'pick':
                if event == 'cycle':
                    self.pick_color = COLORS[(COLORS.index(self.pick_color) + 1) % 4]
                elif event == 'cancel':
                    self.pick_card = None
                elif event == 'confirm':
                    self.send('play', card=self.pick_card, color=self.pick_color, turn=self.state['turn'])
                    self.sent_turn = self.state['turn']
                    self.pick_card = None
                elif isinstance(event, tuple) and event[0] == 'pick':
                    self.pick_color = event[1]

    def act(self, event):
        if not self.my_turn():
            self.flash('Not your turn')
            return
        turn = self.state['turn']
        if self.sent_turn == turn:
            return  # already sent this turn, waiting to hear back
        if event == 'draw':
            self.sent_turn = turn
            self.send('draw', turn=turn)
            return
        card = self.selected()
        if not self.selected_legal():
            self.flash("Can't play that")
        elif card_color(card) is None:
            self.pick_card = card
            self.pick_color = self.best_color(card)
        else:
            self.sent_turn = turn
            self.send('play', card=card, turn=turn)

    def best_color(self, played):
        """The color we hold most of, as a starting suggestion"""
        rest = list(self.cards)
        rest.remove(played)
        colors = [card_color(c) for c in rest if card_color(c)]
        return max(COLORS, key=colors.count)

    def view(self):
        """Everything the screen needs, as plain values"""
        with self.lock:
            now = time.monotonic()
            mode = self.mode()
            message = self.message if now < self.message_until else ''
            view = {'mode': mode, 'name': self.name, 'message': message}
            state = self.state
            if mode == 'lobby':
                view.update(joined=len(state['players']), needed=state['needed'])
            elif mode == 'over':
                scores = '  '.join(f'{p} {n}' for p, n in state['counts'].items())
                view.update(winner=state['winner'], scores=scores)
            elif mode == 'uno':
                left = state['uno']['remaining'] - (now - self.state_time)
                view.update(uno_player=state['uno']['player'], mine=state['uno']['player'] == self.name,
                            called=self.called_for == self.uno_key(), remaining=max(0, int(left + 0.99)))
            elif mode == 'pick':
                view.update(pick_color=self.pick_color)
            elif mode == 'turn':
                view.update(my_turn=self.my_turn(), current=state['current'], direction=state['direction'],
                            top=state['top'], color=state['color'], last=state['last'],
                            counts=[(p, state['counts'][p]) for p in state['players']],
                            cards=list(self.cards), index=self.index, selected=self.selected(),
                            selected_legal=self.selected_legal())
            return view


def run_bot(player, delay):
    """Plays the first legal card. Sometimes it notices an UNO, sometimes it doesn't."""
    last_uno = None
    while True:
        player.keep_joining()
        time.sleep(delay)
        with player.lock:
            mode = player.mode()
            if mode == 'over':
                print(f"{player.name}: {player.state['winner']} won, I have {len(player.cards)} cards")
                return
            if mode == 'uno':
                key = player.uno_key()
                if key != last_uno:
                    last_uno = key
                    if random.random() < 0.5:
                        player.send('call')
            elif mode == 'turn' and player.my_turn() and player.sent_turn != player.state['turn']:
                turn = player.state['turn']
                player.sent_turn = turn
                legal = [c for c in player.cards
                         if is_legal(c, player.state['top'], player.state['color'], player.cards)]
                if not legal:
                    player.send('draw', turn=turn)
                elif card_color(legal[0]) is None:
                    player.send('play', card=legal[0], color=player.best_color(legal[0]), turn=turn)
                else:
                    player.send('play', card=legal[0], turn=turn)


def read_keyboard(player):
    commands = {'n': 'next', 'p': 'prev', 'u': 'play', 'd': 'draw', 'c': 'call', 'y': 'cycle', 'k': 'confirm', 'x': 'cancel'}
    while True:
        try:
            command = input().strip().lower()
        except EOFError:
            return
        if command in commands:
            player.handle(commands[command])


def describe(view):
    """One line for the terminal"""
    mode = view['mode']
    if mode == 'turn':
        cards = ' '.join(f'[{c}]' if i == view['index'] else c for i, c in enumerate(view['cards']))
        who = 'YOUR TURN' if view['my_turn'] else f"{view['current']}'s turn"
        return f"{who} | top {view['top']} color {view['color']} | {cards} | {view['message'] or view['last']}"
    if mode == 'uno':
        return f"UNO window for {view['uno_player']}: type c"
    if mode == 'pick':
        return f"Pick a color: {view['pick_color']} (y change, k choose, x cancel)"
    if mode == 'over':
        return f"{view['winner']} wins | {view['scores']}"
    if mode == 'lobby':
        return f"Waiting: {view['joined']}/{view['needed']}"
    return 'Finding the referee...'


def run_interactive(player, args):
    from screen import render

    display = controls = None
    if args.keyboard:
        print('n/p browse, u play, d draw, c call UNO, y/k/x color picker. Press Enter after each.')
        threading.Thread(target=read_keyboard, args=(player,), daemon=True).start()
    else:
        from hardware import Controls, Display
        display = Display()
        controls = Controls(proximity=args.proximity, rotation=args.rotate)

    last_view = None
    while True:
        player.keep_joining()
        with player.lock:
            mode = player.mode()
        if controls:
            controls.set_mode(mode)
            for event in controls.poll():
                player.handle(event)
        view = player.view()
        if view != last_view:
            last_view = view
            if display:
                display.show(render(view))
            else:
                print(describe(view))
        time.sleep(0.03)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--team', help='your team, same as the referee')
    parser.add_argument('--name', help='up to 10 letters or numbers, different on each Pi')
    parser.add_argument('--keyboard', action='store_true')
    parser.add_argument('--bot', action='store_true')
    parser.add_argument('--bot-delay', type=float, default=1.5, help='seconds a bot takes to move')
    parser.add_argument('--proximity', type=int, default=60, help='sensor reading (0-255) that counts as covered')
    parser.add_argument('--rotate', type=int, default=0, choices=[0, 90, 180, 270],
                        help='if swipes come out in the wrong direction')
    parser.add_argument('--sensor-test', action='store_true', help='print sensor readings and exit')
    parser.add_argument('--calibrate', action='store_true', help='teach this Pi your colored objects and exit')
    args = parser.parse_args()

    if args.calibrate:
        from hardware import calibrate
        try:
            calibrate()
        except KeyboardInterrupt:
            print()
        return

    if args.sensor_test:
        from hardware import sensor_test
        try:
            sensor_test()
        except KeyboardInterrupt:
            print()
        return

    if not args.team or not args.name:
        parser.error('--team and --name are required')
    if not valid_name(args.name):
        parser.error('--name must be 1-10 letters, numbers, - or _')

    player = Player(args.team, args.name)
    try:
        if args.bot:
            run_bot(player, args.bot_delay)
        else:
            run_interactive(player, args)
    except KeyboardInterrupt:
        print('\nPlayer stopped')
    finally:
        player.client.loop_stop()
        player.client.disconnect()


if __name__ == '__main__':
    main()
