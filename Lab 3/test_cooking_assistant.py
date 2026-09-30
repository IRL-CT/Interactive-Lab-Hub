import unittest

from cooking_assistant import SharedSession, create_app


class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.session = SharedSession()
        self.client = create_app(self.session, simulate=True).test_client()

    def test_state_endpoint(self):
        response = self.client.get("/api/state")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "Starting")

    def test_reply_is_queued(self):
        self.session.update(status="Waiting for wizard")
        response = self.client.post("/api/reply", json={"text": "  Next step.  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.replies.get_nowait(), "Next step.")

    def test_blank_reply_is_rejected(self):
        self.assertEqual(self.client.post("/api/reply", json={"text": " "}).status_code, 400)

    def test_early_reply_is_rejected(self):
        self.assertEqual(
            self.client.post("/api/reply", json={"text": "Too early"}).status_code,
            409,
        )

    def test_simulated_speech_is_queued(self):
        self.client.post("/api/simulate-speech", json={"text": "repeat that"})
        self.assertEqual(self.session.simulated_speech.get_nowait(), "repeat that")


if __name__ == "__main__":
    unittest.main()
