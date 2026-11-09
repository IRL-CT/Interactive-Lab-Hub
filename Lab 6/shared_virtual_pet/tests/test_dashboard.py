import re
import unittest
from dashboard import create_app

class FakeStation:
    def snapshot(self): return dict(state=None, connected=False, fresh=False)
    def send(self, action, simulated=False): return {'event_id':'test'}

class DashboardTests(unittest.TestCase):
    def test_hidden_controls(self):
        c = create_app(FakeStation()).test_client()
        self.assertEqual(c.get('/').status_code,200)
        self.assertNotIn(b'data-action=',c.get('/').data)
        self.assertIsNone(c.get('/api/state').json['state'])
        self.assertEqual(c.post('/api/action/feed').status_code,403)
    def test_token(self):
        c = create_app(FakeStation(),True).test_client()
        self.assertEqual(c.post('/api/action/feed').status_code,403)
        token = re.search(r'name="pet-token" content="([^"]+)"',c.get('/').text)[1]
        h = {'X-Pet-Token':token}
        self.assertEqual(c.post('/api/action/feed',headers=h).status_code,200)
        self.assertEqual(c.post('/api/action/invalid',headers=h).status_code,400)
