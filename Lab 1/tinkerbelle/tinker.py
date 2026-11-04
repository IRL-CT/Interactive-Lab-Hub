from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import socket
import sys

port = 5001

app = Flask(__name__)
socketio = SocketIO(app)

# ---------------------------------------------------------------------------
# Firefly state
#
# The server does NOT run the flash oscillators. Each phone runs its own, and
# phones nudge each other by relaying 'pulse' events. The server only holds the
# shared simulation parameters so that a phone joining late (or reloading
# mid-shoot) inherits the settings the controller has already dialled in
# instead of snapping back to defaults.
# ---------------------------------------------------------------------------

DEFAULT_PARAMS = {
	# coupling: how strongly a heard flash shifts our own timing. Deliberately
	# low so that two fireflies take roughly 40-55s to come together, which
	# gives the camera many visible rounds of adjustment. Raising it to 0.10
	# collapses that to about 10s. Below ~0.03 they often never lock at all.
	'coupling': 0.05,
	# periodCoupling: how much a firefly adapts its *intrinsic* rhythm toward
	# the rhythm it hears. Phase coupling alone cannot fully sync oscillators
	# with different natural periods; this is what lets them truly converge.
	'periodCoupling': 0.06,
	# the range the fireflies' starting rhythms are spread across, in seconds.
	# Firefly 1 takes the fast end and the last one the slow end, rather than
	# each drawing at random, so every take opens with the same clear contrast.
	'periodMin': 0.7,
	'periodMax': 2.5,
	'flashColor': '#ffe83d',
	'femaleColor': '#ff9e2c',
	'nightColor': '#050b05',
	'flashDuration': 260,
	# how long a female waits before answering a male flash, in ms
	'responseDelay': 2000,
	# manual: fireflies stop free-running and flash only when tapped or when
	# the controller fires them. Off by default, because the whole point is
	# that synchrony emerges with nobody in charge.
	'manual': False,
	'sound': True,
	'running': True,
	'decor': True,
	'showLabels': True,
	# text pushed onto every firefly screen as a title card ('' = none)
	'card': '',
}

params = dict(DEFAULT_PARAMS)

# sid -> {'id': int, 'role': 'male'|'female'|'controller'|'idle'}
devices = {}


def next_device_id():
	"""Smallest unused positive integer, so labels stay small as phones join
	and leave over the course of a shoot."""
	taken = {d['id'] for d in devices.values()}
	i = 1
	while i in taken:
		i += 1
	return i


def roster():
	"""Every device, with a per-role number so the two males are always
	'Male Firefly 1' and 'Male Firefly 2' no matter what order the phones
	connected in or where the controller landed in the id sequence."""
	seen = {}
	out = []
	for d in sorted(devices.values(), key=lambda x: x['id']):
		seen[d['role']] = seen.get(d['role'], 0) + 1
		out.append({'id': d['id'], 'role': d['role'], 'num': seen[d['role']]})
	return out


def push_roster():
	socketio.emit('roster', roster())


def broadcast(name, value):
	emit(name, value, broadcast=True, include_self=False)


def get_ip_address():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# use a public address to bypass the need to connect
	s.connect(("8.8.8.8", 80))
	ip_address = s.getsockname()[0]
	s.close()
	return ip_address


@socketio.on('connect')
def test_connect():
	device = {'id': next_device_id(), 'role': 'idle'}
	devices[request.sid] = device
	print(f"connected: firefly {device['id']}")
	# tell this client who it is and hand it the current simulation state
	emit('identity', {'id': device['id'], 'role': device['role'], 'params': params})
	emit('after connect', {'data': 'Lets dance'})
	push_roster()


@socketio.on('disconnect')
def handle_disconnect():
	device = devices.pop(request.sid, None)
	if device:
		print(f"disconnected: firefly {device['id']}")
	push_roster()


# --- firefly events --------------------------------------------------------

@socketio.on('pulse')
def handle_pulse(val):
	"""A firefly flashed. Relay it to every other firefly so they can adjust."""
	broadcast('pulse', val)


@socketio.on('params')
def handle_params(val):
	"""Controller changed one or more settings. Merge into the authoritative
	state, then fan the change out."""
	if isinstance(val, dict):
		params.update(val)
		broadcast('params', val)


@socketio.on('scatter')
def handle_scatter(val):
	"""Re-randomize every firefly's period and phase, on camera."""
	broadcast('scatter', val or {})


@socketio.on('flashNow')
def handle_flash_now(val):
	"""Manual flash: either fire one firefly by id, or all of them at once.
	A backup for when the automatic coupling needs a helping hand on set."""
	target = (val or {}).get('id')
	if target is None:
		broadcast('flashNow', {})
		return
	for sid, device in devices.items():
		if device['id'] == target:
			socketio.emit('flashNow', {}, to=sid)
			break


@socketio.on('setRole')
def handle_set_role(val):
	"""Either a phone announcing its own role, or the controller reassigning
	another device's role by firefly id."""
	if not isinstance(val, dict):
		return
	role = val.get('role')
	if role not in ('male', 'female', 'controller', 'idle'):
		return

	target_id = val.get('id')
	if target_id is None:
		# a device declaring its own role
		device = devices.get(request.sid)
		if device:
			device['role'] = role
	else:
		# controller reassigning someone else
		for sid, device in devices.items():
			if device['id'] == target_id:
				device['role'] = role
				socketio.emit('role', {'role': role}, to=sid)
				break
	push_roster()


# --- original tinkerbelle events (unchanged) -------------------------------

@socketio.on('message')
def handle_message(data):
	print('received message: ' + data)


@socketio.on('hex')
def handle_hex(val):
	broadcast('hex', val)


@socketio.on('audio')
def handle_audio(val):
	broadcast('audio', val)


@socketio.on('pauseAudio')
def handle_pause(val):
	broadcast('pauseAudio', val)


@app.route('/')
def index():
	return render_template('index.html')


if __name__ == '__main__':

	ip = get_ip_address()
	if ip:
		print(f"access at http://{ip}:{port}")
	else:
		print(f"No non-local IP found. Access may be available at http://127.0.0.1:{port}")
	socketio.run(app, host='0.0.0.0', debug=True, port=port)
