#!/usr/bin/env python3
"""Connect the existing Omarchy Falcon BMS menu entry to TelemFFB."""

import json
import os
from pathlib import Path
import re
import shlex
import shutil
import tempfile


def main():
    home = Path.home()
    menu = home / '.config/omarchy/extensions/omarchy-menu.jsonc'
    wrapper = home / 'bin/start-bms-telemffb.sh'
    launcher = home / 'bin/start-bms.sh'
    combined = Path(__file__).resolve().parent / 'start-bms-telemffb.sh'
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise SystemExit(f'BMS launcher is missing or not executable: {launcher}')
    text = menu.read_text()
    pattern = r'("games\.falcon-bms"\s*:\s*\{[^{}]*?"action"\s*:\s*)("(?:[^"\\]|\\.)*")'
    matches = list(re.finditer(pattern, text, re.DOTALL))
    if len(matches) != 1:
        raise SystemExit('Could not find exactly one games.falcon-bms action; menu unchanged.')
    match = matches[0]
    current = json.loads(match.group(2))
    if current == str(wrapper):
        raise SystemExit('The menu already points to the TelemFFB wrapper; no changes made.')
    if current != str(launcher):
        raise SystemExit(f'Unexpected BMS menu action: {current!r}; menu unchanged.')
    if wrapper.exists():
        raise SystemExit(f'Wrapper already exists: {wrapper}; menu unchanged.')
    command = (f'exec {shlex.quote(str(combined))} --bms-launcher '
               f'{shlex.quote(str(launcher))} --exit-with-bms')
    contents = ('#!/usr/bin/env bash\n'
                'export WINEPREFIX="$HOME/.wine"\n'
                'log_dir="$HOME/.local/state/VPForce-TelemFFB"\n'
                'mkdir -p "$log_dir"\n'
                f'{command} >>"$log_dir/bms-launcher.log" 2>&1\n')
    with wrapper.open('x') as output:
        output.write(contents)
    wrapper.chmod(0o755)
    # Keep a unique backup and replace the menu only after all checks pass.
    with tempfile.NamedTemporaryFile(prefix='omarchy-menu.', suffix='.bak',
                                     dir=menu.parent, delete=False) as backup:
        backup_path = Path(backup.name)
    shutil.copy2(menu, backup_path)
    updated = text[:match.start(2)] + json.dumps(str(wrapper)) + text[match.end(2):]
    menu.write_text(updated)
    print(f'Falcon BMS menu updated. Backup: {backup_path}')
    print(f'Launcher log: {home / ".local/state/VPForce-TelemFFB/bms-launcher.log"}')


if __name__ == '__main__':
    main()
