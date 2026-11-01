import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from night_handoff import is_start_command, wait_for_ready


class VoiceCommandTests(unittest.TestCase):
    def test_accepts_hello_with_case_punctuation_or_repetition(self):
        for phrase in ('Hello.', 'HELLO!', ' hello ', 'Hello, hello.'):
            with self.subTest(phrase=phrase):
                self.assertTrue(is_start_command(phrase))

    def test_rejects_negation_other_speech_and_silence(self):
        for phrase in ('', 'Hi, how are you?', 'Do not say hello',
                       "Don't say hello", 'hello there', 'Start night watch',
                       '不要hello', 'shelloworld'):
            with self.subTest(phrase=phrase):
                self.assertFalse(is_start_command(phrase))


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ready = Path(self.temp.name) / 'ready.json'
        self.children = []

    def tearDown(self):
        for child in self.children:
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=3)
        self.temp.cleanup()

    def start(self, code):
        child = subprocess.Popen([sys.executable, '-c', code, str(self.ready)])
        self.children.append(child)
        return child

    def test_waits_for_a_live_child_to_publish_readiness(self):
        child = self.start(
            'import json,os,sys,time; from pathlib import Path; '
            'time.sleep(.1); Path(sys.argv[1]).write_text('
            'json.dumps({"pid":os.getpid(),"t":"sample-time"})); time.sleep(3)')
        result = wait_for_ready(child, self.ready, timeout=2)
        self.assertEqual(result['pid'], child.pid)
        self.assertIsNone(child.poll())

    def test_never_accepts_a_stale_file_from_another_process(self):
        self.ready.write_text(json.dumps({'pid': -1}))
        child = self.start('import time; time.sleep(3)')
        with self.assertRaises(TimeoutError):
            wait_for_ready(child, self.ready, timeout=.15)

    def test_failed_start_is_not_reported_as_running(self):
        child = self.start('raise SystemExit(2)')
        with self.assertRaises(RuntimeError):
            wait_for_ready(child, self.ready, timeout=2)


if __name__ == '__main__':
    unittest.main()
