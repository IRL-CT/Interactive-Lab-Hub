"""Pure, deterministic game rules. All times are engine monotonic seconds."""
import uuid

ATTRIBUTES = {'feed': 'fullness', 'play': 'happiness', 'rest': 'energy'}


class PetGame:
    def __init__(self, now=0.0):
        self.version = 0
        self.seen = set()
        self.reset(now)

    def reset(self, now):
        self.round_id = str(uuid.uuid4())
        self.values = dict.fromkeys(ATTRIBUTES.values(), 40)
        self.status = 'playing'
        self.last_action = self.last_device = None
        self.last_event_id = None
        self.last_simulated = False
        self.happy_since = None
        self.next_decay = now + 15
        self.now = now
        self.seen.clear()
        self.last_device_action = {}
        self.contributors = set()
        self.version += 1

    @property
    def mood(self):
        if min(self.values.values()) < 30:
            return 'needs_care'
        return 'happy' if min(self.values.values()) >= 70 else 'normal'

    def tick(self, now):
        if now < self.now:
            raise ValueError('Clock must be monotonic')
        self.now = now
        while self.status == 'playing':
            win_at = self.happy_since + 10 if self.happy_since is not None else float('inf')
            # At an exact tie, decay happens first; all values must still meet target.
            if self.next_decay <= min(now, win_at):
                self.values = {k: max(0, v - 1) for k, v in self.values.items()}
                self.next_decay += 15
                self.version += 1
                if self.mood != 'happy':
                    self.happy_since = None
            elif win_at <= now:
                self.status = 'won'
                self.version += 1
            else:
                break

    def apply(self, event, now):
        self.tick(now)
        if event['round_id'] != self.round_id:
            return False, 'old round'
        if event['event_id'] in self.seen:
            return False, 'duplicate'
        self.seen.add(event['event_id'])
        action = event['event']
        if action == 'reset':
            self.reset(now)
            return True, 'new game'
        if self.status == 'won':
            return False, 'round already won'
        device = event['device_id']
        if now - self.last_device_action.get(device, -float('inf')) < 3:
            return False, 'cooldown'
        self.last_device_action[device] = now
        key = ATTRIBUTES[action]
        self.values[key] = min(100, self.values[key] + 20)
        self.contributors.add(action)
        self.last_action, self.last_device = action, device
        self.last_event_id = event['event_id']
        self.last_simulated = event.get('simulated', False)
        if self.mood == 'happy' and self.happy_since is None:
            self.happy_since = now
        self.version += 1
        return True, 'accepted'

    def snapshot(self):
        elapsed = 0 if self.happy_since is None else min(10, self.now - self.happy_since)
        return {**self.values, 'name': 'Longan', 'mood': self.mood,
                'status': self.status, 'round_id': self.round_id, 'version': self.version,
                'last_action': self.last_action, 'last_device': self.last_device,
                'last_event_id': self.last_event_id, 'last_simulated': self.last_simulated,
                'cooperation_seconds': round(elapsed, 1),
                'contributors': sorted(self.contributors)}
