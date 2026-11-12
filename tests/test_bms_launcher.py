"""Exercise the combined launcher without Wine, BMS, or FFB hardware."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux launcher')
def test_launcher_starts_processes_and_stops_forwarder(tmp_path):
    root = tmp_path / 'checkout'
    (root / 'scripts').mkdir(parents=True)
    (root / '.venv/bin').mkdir(parents=True)
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    source = Path(__file__).resolve().parents[1] / 'scripts/start-bms-telemffb.sh'
    launcher = root / 'scripts/start-bms-telemffb.sh'
    shutil.copy(source, launcher)
    marker = tmp_path / 'events'

    def executable(path, code):
        path.write_text(f'#!{sys.executable}\n' + code)
        path.chmod(0o755)

    executable(root / '.venv/bin/python', 'import time\ntime.sleep(1)\n')
    executable(bin_dir / 'wine', '''import os, signal, sys, time
from pathlib import Path
p = Path(os.environ['TEST_EVENTS'])
p.write_text(os.environ['WINEPREFIX'] + '\\n' + ' '.join(sys.argv[1:]) + '\\n')
def stop(*args):
    with p.open('a') as f: f.write('stopped\\n')
    sys.exit(0)
signal.signal(signal.SIGTERM, stop)
while True: time.sleep(0.05)
''')
    bms = tmp_path / 'start bms'
    executable(bms, '''import os
from pathlib import Path
Path(os.environ['TEST_BMS']).write_text('started')
''')
    env = {**os.environ, 'PATH': f"{bin_dir}:{os.environ['PATH']}",
           'WINEPREFIX': str(tmp_path / 'prefix'), 'TEST_EVENTS': str(marker),
           'TEST_BMS': str(tmp_path / 'bms-started')}
    result = subprocess.run([str(launcher), '--bms-launcher', str(bms), '--port', '34383'],
                            env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert marker.read_text().splitlines() == [str(tmp_path / 'prefix'),
        'python.exe -m wine.bms_udp_forwarder --port 34383', 'stopped']
    assert (tmp_path / 'bms-started').read_text() == 'started'


def test_launcher_rejects_invalid_port():
    script = Path(__file__).resolve().parents[1] / 'scripts/start-bms-telemffb.sh'
    result = subprocess.run([str(script), '--port', '0'], capture_output=True, text=True)
    assert result.returncode == 2
    assert 'Port must be between' in result.stderr
