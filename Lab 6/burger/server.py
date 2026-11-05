"""
Pan Burger: game server for the laptop.

The laptop is the only referee. The two pan-shaped Pis only report what happened
(a mode change, a card held to the colour sensor, a flip / chop / toss) over MQTT,
and this server decides what it means, keeps the whole game state and draws it on
the big screen (templates/index.html) through Socket.IO.

Run:
    python server.py                 # with MQTT (farlab broker)
    python server.py --no-mqtt       # offline, play with the keyboard simulator
    python server.py --team team7    # topics become IDD/team7/burger/...

Open http://localhost:5050
"""

import argparse
import json
import random
import threading
import time

from flask import Flask, render_template
from flask_socketio import SocketIO

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None


# ---------------------------------------------------------------- settings --

MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

MODES = ['grill', 'board', 'assembly']
CARDS = ['plate', 'bun', 'cheese', 'lettuce', 'meat']
FILLINGS = ['cheese', 'lettuce', 'meat']

ROUND_SECONDS = 180
TICK = 0.1

COOK_RATE = 12       # doneness per second on the side facing down
COOKED = 60          # a side is cooked at 60
BURNT = 100          # and burnt at 100
CHOPS_NEEDED = 5

LEVELS = {
    1: dict(name='First Day', max_fill=1, fillings=['cheese', 'meat'],
            max_customers=2, spawn=(14, 20), patience=(75, 95)),
    2: dict(name='Lunch Rush', max_fill=3, fillings=FILLINGS,
            max_customers=3, spawn=(11, 16), patience=(65, 85)),
    3: dict(name='Peak Hour', max_fill=5, fillings=FILLINGS,
            max_customers=4, spawn=(8, 12), patience=(55, 75)),
}

# Single player gets more time per customer and a shorter queue.
SOLO_SLOWDOWN = 1.4


# -------------------------------------------------------------------- game --

class Game:
    def __init__(self, emit_event, emit_feedback):
        self.lock = threading.RLock()
        self.emit_event = emit_event          # (event dict) -> big screen
        self.emit_feedback = emit_feedback    # (pid, dict) -> that Pi
        self.phase = 'lobby'
        self.num_players = 2
        self.level = 1
        self.last_seen = {}       # pid -> time of the last MQTT message from that pan
        self.reset_round()

    # ---- setup

    def reset_round(self):
        self.time_left = ROUND_SECONDS
        self.score = 0
        self.served = 0
        self.missed = 0
        self.customers = []
        self.next_customer_id = 1
        self.spawn_timer = 0
        self.players = {pid: self.new_player() for pid in self.pids()}

    def pids(self):
        return ['p1', 'p2'][:self.num_players]

    @staticmethod
    def new_player():
        return {
            'mode': 'grill',
            'patty': None,      # {'A': 0, 'B': 0, 'down': 'A'}
            'lettuce': None,    # {'chops': 0}
            'stack': None,      # None = no plate, [] = empty plate (auto), ['bun', ...]
            'tray': [],         # ready items: 'meat' (cooked), 'lettuce' (chopped)
        }

    def start(self, num_players, level):
        with self.lock:
            self.num_players = 1 if num_players == 1 else 2
            self.level = level if level in LEVELS else 1
            self.reset_round()
            self.phase = 'playing'
            self.spawn_customer()
            self.spawn_timer = self.next_spawn_delay()
        for pid in self.pids():
            self.feedback(pid, 'start')

    def to_lobby(self):
        with self.lock:
            self.phase = 'lobby'
            self.reset_round()

    # ---- customers

    def settings(self):
        s = dict(LEVELS[self.level])
        if self.num_players == 1:
            s['spawn'] = tuple(x * SOLO_SLOWDOWN for x in s['spawn'])
            s['patience'] = tuple(x * SOLO_SLOWDOWN for x in s['patience'])
            s['max_customers'] = max(2, s['max_customers'] - 1)
        return s

    def next_spawn_delay(self):
        return random.uniform(*self.settings()['spawn'])

    def spawn_customer(self):
        s = self.settings()
        if len(self.customers) >= s['max_customers']:
            return False
        n = random.randint(1, s['max_fill'])
        fillings = [random.choice(s['fillings']) for _ in range(n)]
        patience = random.uniform(*s['patience']) + 6 * n
        self.customers.append({
            'id': self.next_customer_id,
            'order': ['bun'] + fillings + ['bun'],
            'patience': patience,
            'left': patience,
            'look': random.randrange(6),
        })
        self.next_customer_id += 1
        return True

    # ---- the clock

    def tick(self, dt):
        with self.lock:
            if self.phase != 'playing':
                return
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.phase = 'over'
                self.event(None, 'over', f'Closing time! {self.served} burgers, {self.score} points')
                return

            self.spawn_timer -= dt
            if self.spawn_timer <= 0 or not self.customers:
                self.spawn_customer()
                self.spawn_timer = self.next_spawn_delay()

            for c in list(self.customers):
                c['left'] -= dt
                if c['left'] <= 0:
                    self.customers.remove(c)
                    self.missed += 1
                    self.score = max(0, self.score - 5)
                    self.event(None, 'angry', 'A customer got tired of waiting and left  -5')

            for pid, p in self.players.items():
                patty = p['patty']
                if patty is None:
                    continue
                side = patty['down']
                patty[side] += COOK_RATE * dt
                if patty[side] >= BURNT:
                    p['patty'] = None
                    self.score = max(0, self.score - 3)
                    self.event(pid, 'burn', 'The patty burnt!  -3')
                elif patty['A'] >= COOKED and patty['B'] >= COOKED:
                    p['patty'] = None
                    p['tray'].append('meat')
                    self.event(pid, 'ding', 'Patty done!')

    # ---- inputs (from MQTT or the simulator)

    def seen(self, pid):
        self.last_seen[pid] = time.time()

    def handle(self, pid, kind, value):
        with self.lock:
            if self.phase != 'playing' or pid not in self.players:
                return
            p = self.players[pid]
            if kind == 'mode':
                self.set_mode(pid, p, value)
            elif kind == 'button':
                if value == 'A':
                    self.set_mode(pid, p, MODES[(MODES.index(p['mode']) + 1) % len(MODES)])
                elif value == 'B':
                    self.trash(pid, p)
            elif kind == 'card':
                self.card(pid, p, value)
            elif kind == 'gesture':
                self.gesture(pid, p, value)

    def set_mode(self, pid, p, mode):
        if mode not in MODES or mode == p['mode']:
            return
        p['mode'] = mode
        if mode == 'assembly' and p['stack'] is None:
            p['stack'] = []           # a plate appears when the pan is put down
        self.event(pid, 'mode', {'grill': '🍳 Grill', 'board': '🔪 Board', 'assembly': '🍔 Assembly'}[mode])

    def trash(self, pid, p):
        mode = p['mode']
        if mode == 'grill' and p['patty']:
            p['patty'] = None
        elif mode == 'board' and p['lettuce']:
            p['lettuce'] = None
        elif mode == 'assembly' and p['stack']:
            p['stack'] = []           # throw the burger away, keep a clean plate
        else:
            return self.event(pid, 'error', 'Nothing to throw away')
        self.event(pid, 'trash', 'Thrown away')

    def card(self, pid, p, card):
        if card not in CARDS:
            return
        mode = p['mode']
        if mode == 'grill':
            if card != 'meat':
                return self.event(pid, 'error', 'Only patties go on the grill')
            if p['patty']:
                return self.event(pid, 'error', 'There is already a patty in the pan')
            p['patty'] = {'A': 0.0, 'B': 0.0, 'down': 'A'}
            self.event(pid, 'ok', 'Patty on, sizzle~')
        elif mode == 'board':
            if card != 'lettuce':
                return self.event(pid, 'error', 'Only lettuce goes on the board')
            if p['lettuce']:
                return self.event(pid, 'error', 'There is already lettuce on the board')
            p['lettuce'] = {'chops': 0}
            self.event(pid, 'ok', 'Lettuce on the board')
        else:
            self.assemble(pid, p, card)

    def assemble(self, pid, p, card):
        # No plate card: putting the pan down on the table (assembly mode)
        # sets out a plate by itself.
        if p['stack'] is None:
            p['stack'] = []
        if card == 'plate':
            return

        candidate = p['stack'] + [card]
        wanted = [c for c in self.customers if c['order'][:len(candidate)] == candidate]
        if not wanted:
            return self.event(pid, 'error', 'No customer wants it stacked like that')
        if card in ('meat', 'lettuce'):
            if card not in p['tray']:
                return self.event(pid, 'error',
                                  'No cooked patty yet!' if card == 'meat' else 'No chopped lettuce yet!')
            p['tray'].remove(card)

        p['stack'] = candidate
        done = [c for c in wanted if c['order'] == candidate]
        if done:
            self.serve(pid, p, done[0])
        else:
            self.event(pid, 'ok', {'bun': 'Bun', 'cheese': 'Cheese',
                                   'lettuce': 'Lettuce', 'meat': 'Patty'}[card])

    def serve(self, pid, p, customer):
        fillings = len(customer['order']) - 2
        tip = int(5 * customer['left'] / customer['patience'])
        points = 10 + 5 * fillings + tip
        self.score += points
        self.served += 1
        self.customers.remove(customer)
        p['stack'] = [] if p['mode'] == 'assembly' else None   # next plate
        self.event(pid, 'serve', f'Order up! +{points}', customer=customer['id'])

    def gesture(self, pid, p, gesture):
        mode = p['mode']
        if gesture == 'flip':
            if mode != 'grill':
                return
            if not p['patty']:
                return self.event(pid, 'error', 'No patty in the pan')
            p['patty']['down'] = 'B' if p['patty']['down'] == 'A' else 'A'
            self.event(pid, 'flip', 'Flip!')
        elif gesture == 'chop':
            if mode != 'board':
                return
            if not p['lettuce']:
                return self.event(pid, 'error', 'No lettuce on the board')
            p['lettuce']['chops'] += 1
            if p['lettuce']['chops'] >= CHOPS_NEEDED:
                p['lettuce'] = None
                p['tray'].append('lettuce')
                self.event(pid, 'ding', 'Lettuce chopped!')
            else:
                self.event(pid, 'chop', f'Chop {p["lettuce"]["chops"]}/{CHOPS_NEEDED}')
        elif gesture == 'toss':
            if mode != 'assembly':
                return
            other = 'p2' if pid == 'p1' else 'p1'
            if other not in self.players:
                return self.event(pid, 'error', 'No partner in single player')
            if not p['tray']:
                return self.event(pid, 'error', 'Nothing ready to throw')
            item = p['tray'].pop(0)
            self.players[other]['tray'].append(item)
            name = 'patty' if item == 'meat' else 'lettuce'
            self.event(pid, 'toss', f'Threw the {name} to your partner', to=other, item=item)
            self.event(other, 'catch', f'Caught the {name}!')

    # ---- output

    def event(self, pid, kind, msg, **extra):
        e = {'pid': pid, 'kind': kind, 'msg': msg, **extra}
        self.emit_event(e)
        if pid:
            self.feedback(pid, kind, msg)
        else:
            for p in self.pids():
                self.feedback(p, kind, msg)

    def feedback(self, pid, sound, msg=''):
        p = self.players.get(pid)
        self.emit_feedback(pid, {'sound': sound, 'msg': msg,
                                 'mode': p['mode'] if p else None})

    def snapshot(self):
        with self.lock:
            return {
                'phase': self.phase,
                'num_players': self.num_players,
                'level': self.level,
                'level_name': LEVELS[self.level]['name'],
                'levels': {k: v['name'] for k, v in LEVELS.items()},
                'time_left': self.time_left,
                'round_seconds': ROUND_SECONDS,
                'score': self.score,
                'served': self.served,
                'missed': self.missed,
                'customers': self.customers,
                'players': self.players,
                'cooked': COOKED,
                'burnt': BURNT,
                'chops_needed': CHOPS_NEEDED,
                # pans re-announce their mode every 5 s, so 8 s of silence = gone
                'connected': {pid: time.time() - t < 8 for pid, t in self.last_seen.items()},
            }


# -------------------------------------------------------------------- mqtt --

class Bridge:
    """MQTT in: IDD/<team>/burger/<p1|p2>/<mode|card|gesture|button>
       MQTT out: IDD/<team>/burger/<p1|p2>/feedback and IDD/<team>/burger/game"""

    INPUTS = ('mode', 'card', 'gesture', 'button')

    def __init__(self, team):
        self.base = f'IDD/{team}/burger'
        self.client = None
        self.game = None

    def start(self, game):
        self.game = game
        if mqtt is None:
            print('  paho-mqtt not installed: running without MQTT')
            return
        try:  # paho-mqtt 2.x
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except AttributeError:  # paho-mqtt 1.x
            self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        # rc is an int in paho 1.x and a ReasonCode (== 0 on success) in 2.x
        if rc == 0:
            client.subscribe(f'{self.base}/+/+')
            print(f'  MQTT connected, listening on {self.base}/+/+')
        else:
            print(f'  MQTT connection failed: {rc}')

    def on_message(self, client, userdata, msg):
        parts = msg.topic.split('/')
        if len(parts) != 5 or parts[3] not in ('p1', 'p2') or parts[4] not in self.INPUTS:
            return
        pid, kind = parts[3], parts[4]
        raw = msg.payload.decode('utf-8', 'replace').strip()
        # Accept JSON ({"card": "meat"}, {"type": "flip"}, ...) or a plain word,
        # so testing with mosquitto_pub -m meat works too.
        value = raw
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                value = (data.get(kind) or data.get('type') or data.get('ingredient')
                         or data.get('value'))
            elif isinstance(data, str):
                value = data
        except ValueError:
            pass
        if isinstance(value, str):
            self.game.seen(pid)
            if not (kind == 'mode' and self.game.players.get(pid, {}).get('mode') == value.strip()):
                print(f'  [{pid}] {kind}: {value.strip()}'
                      + ('' if self.game.phase == 'playing' else f'  (ignored: game is {self.game.phase})'))
            self.game.handle(pid, kind, value.strip())

    def publish(self, topic, payload, retain=False):
        if self.client is not None and self.client.is_connected():
            self.client.publish(f'{self.base}/{topic}', json.dumps(payload), retain=retain)


# ---------------------------------------------------------------- web app --

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--team', default='panburger', help='MQTT topic space IDD/<team>/burger')
    ap.add_argument('--port', type=int, default=5050)
    ap.add_argument('--no-mqtt', action='store_true')
    args = ap.parse_args()

    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')
    bridge = Bridge(args.team)

    game = Game(
        emit_event=lambda e: socketio.emit('event', e),
        emit_feedback=lambda pid, fb: bridge.publish(f'{pid}/feedback', fb),
    )

    @app.route('/')
    def index():
        return render_template('index.html')

    @socketio.on('start')
    def on_start(data):
        game.start(int(data.get('players', 2)), int(data.get('level', 1)))

    @socketio.on('lobby')
    def on_lobby():
        game.to_lobby()

    @socketio.on('sim')
    def on_sim(data):
        # The keyboard simulator in the web page speaks the same language as the Pis.
        game.handle(data.get('pid'), data.get('kind'), data.get('value'))

    def loop():
        last_pub = 0
        last = time.time()
        while True:
            socketio.sleep(TICK)
            now = time.time()
            game.tick(now - last)
            last = now
            state = game.snapshot()
            socketio.emit('state', state)
            if now - last_pub > 1:
                last_pub = now
                bridge.publish('game', {k: state[k] for k in
                                        ('phase', 'num_players', 'level', 'score', 'served')}
                               | {'time_left': int(state['time_left'])}, retain=True)

    print('=' * 56)
    print('  Pan Burger server')
    print(f'  Big screen:  http://localhost:{args.port}')
    if not args.no_mqtt:
        print(f'  MQTT topics: IDD/{args.team}/burger/<p1|p2>/<mode|card|gesture|button>')
        bridge.start(game)
    else:
        print('  MQTT off (keyboard simulator only)')
    print('=' * 56)

    socketio.start_background_task(loop)
    socketio.run(app, host='0.0.0.0', port=args.port, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
