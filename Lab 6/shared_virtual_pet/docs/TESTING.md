# Verification record

Software verification performed on macOS / Python 3.14.7 with Paho MQTT 1.6.1 and Flask 3.1.3. This is developer testing, not the course's required user study.

## Passed

`python -m unittest discover -s tests -v`: **22 tests passed**.

- Attribute changes, 0–100 clamping, exact decay boundaries.
- Normal / Needs Care / Happy mood transitions.
- Continuous 10-second victory, interrupted happiness, exact decay/win tie and freeze after winning.
- Duplicate rejection, per-device cooldown, reset and old-round rejection.
- Malformed JSON, wrong types, topic/role mismatch, stale/future timestamps, wrong device identity and simulation opt-in.
- RGB normalization, low-light filtering, stable activation/release, darkness hold/hysteresis, gesture cooldown.
- Flask waiting page, default-hidden controls, disabled action endpoints, developer control token.

`python tests/integration_mqtt.py`: **all checks passed**, using a real loopback TCP MQTT broker (aMQTT 0.12.1), separate engine and Flask processes, and actual simulator CLI subprocesses.

- Initial retained state and all three simulated role actions.
- Unified `sensor_client.py --simulate --no-display` path without hardware imports.
- Duplicate QoS event rejection and malformed MQTT input without engine crash.
- Full round reaches Happy, wins and freezes; subsequent action cannot increase stats.
- Late subscriber and Flask dashboard API agree with authoritative MQTT state.
- Reset creates a fresh round; real 15-second timer decays 40 to 39.
- Broker shutdown/restart triggers disconnect, automatic reconnect, resubscription and successful new action.
- Same-machine duplicate engine is rejected by the namespace file lock.

Python compilation also passed. CLI help was checked for engine, dashboard, simulator and station.

## Not yet verified

- Course broker availability/authentication from each participant's network. No credentials were saved or committed here.
- Actual Raspberry Pi 5 dependency installation and I2C/SPI operation.
- Real color thresholds under the user's lighting/card material; gesture direction/distance; proximity fallback thresholds; ambient-light baseline drift.
- Actual Mini PiTFT pin ownership, display orientation/legibility and accepted-action feedback.
- Visual browser QA and mobile viewport behavior (browser automation was unavailable); Flask HTML/API tests passed, but these do not substitute for rendered-browser inspection.
- Three real Pis cooperating across separate networks.
- Testing with two non-team participants, photos/videos and observations.

The core keeps state in memory and starts a new round on engine restart. MQTT reconnect is tested; restart persistence is deliberately not implemented. Same-host engine locking does not prevent a teammate from starting a second engine on another host. Assign one engine host for the demonstration.
