#!/usr/bin/env python3
"""
UNO referee. Run this once, on any one Pi. It deals, checks every move and
tells everyone what happened, so all the players only have to display it.
"""

import argparse
import json
import queue
import random
import time

from common import Topics, connect, valid_name
from game import Game


class Referee:
    def __init__(self, args):
        self.args = args
        self.topics = Topics(args.team)
        self.game_id = random.randrange(1 << 30)  # lets players spot a new game
        self.lobby = []
        self.game = None
        self.turn_started = 0.0
        self.inbox = queue.Queue()  # the game is only touched from the main loop
        self.client = connect(self.on_message, [self.topics.join, self.topics.action('+')])

    def on_message(self, client, userdata, msg):
        try:
            self.inbox.put((msg.topic, json.loads(msg.payload.decode('UTF-8'))))
        except ValueError:
            print(f'[WARN] ignored bad message on {msg.topic}')

    def send(self, topic, payload):
        self.client.publish(topic, json.dumps(payload), qos=1)

    def publish_state(self):
        if self.game:
            state = self.game.public_state(time.monotonic())
        else:
            state = {'status': 'lobby', 'players': self.lobby, 'needed': self.args.players}
        state['game'] = self.game_id
        self.send(self.topics.state, state)

    def publish_hand(self, name):
        self.send(self.topics.hand(name), {'game': self.game_id, 'cards': self.game.hands[name]})

    def publish_all(self):
        self.publish_state()
        for name in self.game.players:
            self.publish_hand(name)
        print(f'  turn {self.game.turn}: {self.game.last} | top {self.game.top} '
              f'color {self.game.color} | {self.game.public_state()["counts"]}')

    def handle_join(self, name):
        if not isinstance(name, str) or not valid_name(name):
            print(f'[WARN] bad player name: {name!r}')
            return
        if self.game:
            if name in self.game.players:  # a player restarted or reconnected
                self.publish_state()
                self.publish_hand(name)
            return
        if name not in self.lobby:
            self.lobby.append(name)
            print(f'{name} joined ({len(self.lobby)}/{self.args.players})')
        if len(self.lobby) >= self.args.players:
            self.game = Game(self.lobby, seed=self.args.seed)
            self.turn_started = time.monotonic()
            print(f'Dealing to {", ".join(self.lobby)}')
            self.publish_all()
        else:
            self.publish_state()

    def handle_action(self, name, action):
        if not self.game or name not in self.game.players or not isinstance(action, dict):
            return
        kind = action.get('type')
        turn_before = self.game.turn
        if kind == 'call':
            error = self.game.call(name)
            self.turn_started = time.monotonic()
        elif action.get('turn') != self.game.turn:
            error = 'Too late'  # e.g. the same gesture read twice
        elif kind == 'play':
            error = self.game.play(name, action.get('card'), action.get('color'), time.monotonic())
        elif kind == 'draw':
            error = self.game.draw(name)
        else:
            error = 'Unknown action'

        if error:
            self.send(self.topics.notice(name), {'text': error})
            return
        if self.game.turn != turn_before:
            self.turn_started = time.monotonic()
        self.publish_all()

    def tick(self):
        now = time.monotonic()
        if self.game.tick(now):
            self.turn_started = now
            self.publish_all()
        elif (not self.game.uno and not self.game.winner
              and now - self.turn_started > self.args.turn_timeout):
            # Keeps the round going if a player walks off or their Pi dies
            player = self.game.current_player
            self.game.draw(player)
            self.game.last = f'{player} timed out'
            self.turn_started = now
            self.publish_all()

    def run(self):
        print(f'Referee on {self.topics.root}, waiting for {self.args.players} players')
        self.publish_state()
        while not (self.game and self.game.winner):
            try:
                topic, payload = self.inbox.get(timeout=0.1)
                if topic == self.topics.join:
                    self.handle_join(payload.get('name') if isinstance(payload, dict) else None)
                else:
                    self.handle_action(topic.rsplit('/', 1)[-1], payload)
            except queue.Empty:
                pass
            if self.game and not self.game.winner:
                self.tick()
        print(f'{self.game.winner} wins after {self.game.turn} turns')
        time.sleep(1)  # let the last messages go out
        self.client.loop_stop()
        self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--team', required=True, help='your team, used in the MQTT topics')
    parser.add_argument('--players', type=int, default=3, choices=[2, 3, 4])
    parser.add_argument('--turn-timeout', type=float, default=60, help='seconds before a turn is drawn for you')
    parser.add_argument('--seed', type=int, help='deal the same cards every time')
    args = parser.parse_args()
    try:
        Referee(args).run()
    except KeyboardInterrupt:
        print('\nReferee stopped')


if __name__ == '__main__':
    main()
