"""SIGTERM should leave Qt's event loop instead of killing device cleanup."""

import os
import signal
import subprocess
import sys

import pytest


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux signal handling')
def test_sigterm_exits_qt_event_loop():
    code = '''
from PyQt6.QtCore import QCoreApplication
from telemffb.shutdown_signal import install_shutdown_handler
app = QCoreApplication([])
timer = install_shutdown_handler(app)
print("ready", flush=True)
app.exec()
print("clean exit", flush=True)
'''
    process = subprocess.Popen([sys.executable, '-c', code], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    try:
        assert process.stdout.readline().strip() == 'ready'
        os.kill(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr
        assert 'clean exit' in stdout
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
