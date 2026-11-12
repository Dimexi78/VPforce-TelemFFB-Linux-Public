"""Linux startup must not load the unavailable Windows SimConnect runtime."""

import os
import subprocess
import sys

import pytest


@pytest.mark.skipif(sys.platform != "linux", reason="Linux startup regression")
def test_main_window_import_without_simconnect():
    result = subprocess.run(
        [sys.executable, "-c", (
            "import sys; import telemffb.MainWindow; "
            "assert 'telemffb.telem.SimConnectManager' not in sys.modules"
        )],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
