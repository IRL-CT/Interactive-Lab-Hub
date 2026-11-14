"""Hardware-free debouncing, hysteresis and cooldown state machines."""


class CycleTrigger:
    def __init__(self, stable=3, hold=0, cooldown=3, release_samples=3):
        self.stable, self.hold, self.cooldown = stable, hold, cooldown
        self.release_samples = release_samples
        self.armed = True
        self.count = self.release_count = 0
        self.since = None
        self.last = -float('inf')

    def update(self, active, released, now):
        if released:
            self.release_count += 1
            self.count, self.since = 0, None
            if self.release_count >= self.release_samples:
                self.armed = True
        else:
            self.release_count = 0
        if not active:
            self.count, self.since = 0, None
            return False
        self.count += 1
        if self.since is None:
            self.since = now
        if self.armed and self.count >= self.stable and now - self.since >= self.hold:
            # Consume this cycle even inside cooldown; require a new release.
            self.armed = False
            if now - self.last >= self.cooldown:
                self.last = now
                return True
        return False


def is_food(r, g, b, clear, red_min=.46, blue_max=.25, clear_min=10):
    total = r + g + b
    if total <= 0 or clear < clear_min:
        return False
    return r / total >= red_min and b / total <= blue_max and r > g


class GestureTrigger:
    def __init__(self, cooldown=3):
        self.cooldown = cooldown
        self.last = -float('inf')

    def update(self, gesture, now):
        if gesture in (3, 4) and now - self.last >= self.cooldown:
            self.last = now
            return True
        return False
