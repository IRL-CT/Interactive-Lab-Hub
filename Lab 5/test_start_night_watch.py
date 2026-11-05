import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest


class LauncherCleanupTests(unittest.TestCase):
    def test_wrapper_signal_stops_child_before_restoring_display(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lab = root / 'Lab 5'
            lab.mkdir()
            python_dir = root / 'Lab 3/.venv/bin'
            python_dir.mkdir(parents=True)
            (python_dir / 'python').symlink_to(sys.executable)
            shutil.copyfile(Path(__file__).with_name('start_night_watch.sh'), lab / 'start.sh')
            audit = root / 'audit.txt'
            pid_file = root / 'child.pid'
            (lab / 'night_handoff.py').write_text(
                'import os,signal,time\nfrom pathlib import Path\n'
                f'audit=Path({str(audit)!r})\n'
                'def stop(*args):\n'
                '    with audit.open("a") as out: out.write("child_stopped\\n")\n'
                '    raise SystemExit(0)\n'
                'signal.signal(signal.SIGTERM,stop)\n'
                f'Path({str(pid_file)!r}).write_text(str(os.getpid()))\n'
                'while True: time.sleep(.05)\n')
            binaries = root / 'bin'
            binaries.mkdir()
            (binaries / 'systemctl').write_text('#!/bin/sh\nexit 0\n')
            (binaries / 'sudo').write_text(
                '#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n'
                f'with Path({str(audit)!r}).open("a") as out: out.write(sys.argv[3]+"\\n")\n')
            for binary in binaries.iterdir():
                binary.chmod(0o755)
            environment = dict(os.environ, PATH=str(binaries)+os.pathsep+os.environ['PATH'])
            shell = subprocess.Popen(['bash', str(lab / 'start.sh')], env=environment)
            child_pid = None
            try:
                deadline = time.monotonic() + 3
                while not pid_file.exists() and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertTrue(pid_file.exists(), 'Launcher did not start child')
                child_pid = int(pid_file.read_text())
                shell.send_signal(signal.SIGTERM)
                shell.wait(timeout=3)
                self.assertEqual(audit.read_text().splitlines(),
                                 ['stop', 'child_stopped', 'start'])
            finally:
                if child_pid is not None:
                    try:
                        os.kill(child_pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                if shell.poll() is None:
                    shell.kill()
                    shell.wait(timeout=3)


if __name__ == '__main__':
    unittest.main()
