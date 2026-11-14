import json
import unittest
from events import make_event, validate_event, decode_state
from pet_logic import PetGame

class EventTests(unittest.TestCase):
    def setUp(self):
        self.round = PetGame().round_id
        self.devices = dict(feed='pi1', play='pi2', rest='pi3')
        self.event = make_event('feed', 'pi1', self.round)
        self.event['timestamp'] = 100
    def check(self, value, action='feed', allow=False):
        return validate_event(json.dumps(value).encode(), action, self.round, self.devices, allow, now=100)
    def test_valid(self): self.assertEqual(self.check(self.event), self.event)
    def test_bad_json(self):
        for payload in (b'{', b'null', b'[]', b'"text"', b'\xff', b'x' * 4097):
            with self.subTest(payload=payload[:20]), self.assertRaises(ValueError):
                validate_event(payload, 'feed', self.round, self.devices, now=100)
    def test_fields(self):
        for key, value in [('event','play'), ('role','rest'), ('event_id','bad'), ('timestamp',True),
                           ('timestamp',1), ('timestamp',106), ('timestamp',float('nan')),
                           ('device_id','pi2'), ('round_id','old'), ('simulated','yes')]:
            with self.subTest(key=key), self.assertRaises(ValueError): self.check({**self.event,key:value})
    def test_simulation(self):
        e = {**self.event, 'device_id':'sim-feed', 'simulated':True}
        with self.assertRaises(ValueError): self.check(e)
        self.assertEqual(self.check(e, allow=True), e)
    def test_reset(self):
        e = make_event('reset','admin',self.round)
        e['timestamp'] = 100
        self.assertEqual(self.check(e,'reset'),e)
    def test_state(self):
        with self.assertRaises(ValueError): decode_state(b'{"fullness":999}')
