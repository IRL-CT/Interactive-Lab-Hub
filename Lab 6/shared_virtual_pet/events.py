"""Wire protocol validation shared by hardware, simulator and engine."""
import json
import math
import time
import uuid

ROLES = ('feed', 'play', 'rest')


def make_event(action, device_id, round_id, simulated=False):
    return dict(event_id=str(uuid.uuid4()), device_id=device_id,
                role=action if action in ROLES else 'admin', event=action,
                timestamp=time.time(), round_id=round_id, simulated=simulated)


def validate_event(payload, action, round_id, devices, allow_simulation=False, now=None):
    if len(payload) > 4096:
        raise ValueError('Event too large')
    try:
        e = json.loads(payload)
        if not isinstance(e, dict):
            raise ValueError('Expected JSON object')
        if action not in (*ROLES, 'reset') or e.get('event') != action:
            raise ValueError('Topic/action mismatch')
        if e.get('role') != (action if action in ROLES else 'admin'):
            raise ValueError('Role mismatch')
        uuid.UUID(e['event_id'])
        if e.get('round_id') != round_id:
            raise ValueError('Wrong round; wait for latest state')
        stamp = e.get('timestamp')
        if type(stamp) not in (int, float) or not math.isfinite(stamp):
            raise ValueError('Invalid timestamp')
        if not -5 <= (time.time() if now is None else now) - stamp <= 30:
            raise ValueError('Expired event / clock mismatch')
        device = e.get('device_id')
        if not isinstance(device, str) or not 1 <= len(device) <= 80:
            raise ValueError('Invalid device ID')
        simulated = e.get('simulated', False)
        if type(simulated) is not bool:
            raise ValueError('Invalid simulation flag')
        if simulated and not allow_simulation:
            raise ValueError('Engine simulation mode is disabled')
        if action in ROLES and not simulated and devices[action] != device:
            raise ValueError('Device is not assigned to this role')
        return e
    except (KeyError, TypeError, AttributeError, UnicodeError) as exc:
        raise ValueError('Malformed event') from exc


def decode_state(payload):
    """Reject malformed broker data before it reaches displays."""
    if len(payload) > 16384:
        raise ValueError('State too large')
    s = json.loads(payload)
    if not isinstance(s, dict):
        raise ValueError('Invalid state')
    for key in ('fullness', 'happiness', 'energy'):
        if type(s.get(key)) is not int or not 0 <= s[key] <= 100:
            raise ValueError('Invalid attribute')
    if s.get('status') not in ('playing', 'won') or s.get('mood') not in ('normal', 'happy', 'needs_care'):
        raise ValueError('Invalid status')
    try:
        uuid.UUID(s['round_id'])
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('Invalid round') from exc
    if type(s.get('version')) is not int:
        raise ValueError('Invalid version')
    stamp = s.get('published_at')
    if type(stamp) not in (int, float) or not math.isfinite(stamp):
        raise ValueError('Invalid state timestamp')
    elapsed = s.get('cooperation_seconds', 0)
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not 0 <= elapsed <= 10:
        raise ValueError('Invalid cooperation progress')
    if not isinstance(s.get('contributors', []), list):
        raise ValueError('Invalid contributors')
    return s
