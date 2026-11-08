"""Local browser dashboard. Each remote player may run their own MQTT subscriber."""
import argparse
import secrets
from flask import Flask, jsonify, render_template, request
import config
from station import Station


def create_app(station, developer=False):
    app = Flask(__name__)
    token = secrets.token_urlsafe(24)

    @app.get('/')
    def index():
        return render_template('index.html', developer=developer, token=token)

    @app.get('/api/state')
    def state():
        response = jsonify(station.snapshot())
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.post('/api/action/<action>')
    def action(action):
        if not developer:
            return jsonify(error='Developer controls disabled'), 403
        if not secrets.compare_digest(request.headers.get('X-Pet-Token', ''), token):
            return jsonify(error='Invalid local control token'), 403
        if action not in ('feed', 'play', 'rest', 'reset'):
            return jsonify(error='Invalid action'), 400
        try:
            # Per-role IDs match simulator behavior; preserve stable ID during request.
            with control_lock:
                station.device_id = 'sim-' + action
                event = station.send(action, simulated=action != 'reset')
            return jsonify(message='Sent to broker; awaiting engine acceptance', event_id=event['event_id'])
        except (ConnectionError, TimeoutError) as exc:
            return jsonify(error=str(exc)), 503

    import threading
    control_lock = threading.Lock()
    return app


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--developer', action='store_true')
    p.add_argument('--port', type=int, default=5000)
    p.add_argument('--debug', action='store_true', help='Verbose logs, NOT Flask debugger')
    args = p.parse_args()
    config.logging_setup(args.debug)
    station = Station('dashboard')
    station.mqtt.start()
    try:
        create_app(station, args.developer).run(host='127.0.0.1', port=args.port, use_reloader=False, threaded=True)
    finally:
        station.mqtt.close()


if __name__ == '__main__':
    main()
