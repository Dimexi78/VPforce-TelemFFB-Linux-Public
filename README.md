# VPforce TelemFFB

This fork runs TelemFFB natively on Linux and targets Arch Linux / Omarchy,
Wayland, and VPforce Rhino/DIY HID hardware. Falcon BMS runs in Wine and uses
an additional Wine-side telemetry forwarder.

This is an experimental Linux port of [VPforce TelemFFB](https://github.com/walmis/VPforce-TelemFFB).
Falcon BMS 4.38 telemetry and effects were tested with a Rhino on Omarchy.
DCS support is included but has not yet been tested in this Linux port.
Feedback and test reports from other setups are welcome.

## Arch Linux / Omarchy setup

These instructions target Arch Linux / Omarchy. Other distributions need equivalent
packages; they have not been tested. For BMS, install Wine and verify that BMS
runs in its Wine prefix before starting.

Install the native dependencies and clone the repository:

```bash
sudo pacman -S --needed git python python-pyqt6 hidapi libusb usbutils
git clone https://github.com/Dimexi78/VPforce-TelemFFB-Linux-Public.git VPforce-TelemFFB-Linux
cd VPforce-TelemFFB-Linux
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

On Python 3.14 the requirements select a newer NumPy, because the pinned 2.3.0 release
has no Python 3.14 wheel. The system Python and Wine Python environments are
separate; installing packages in one does not install them in the other.

### Rhino USB access

Install the included rule before systemd's seat access rule, then unplug and
reconnect the Rhino:

```bash
sudo install -Dm644 udev/70-vpforce-telemffb.rules /etc/udev/rules.d/70-vpforce-telemffb.rules
sudo udevadm control --reload-rules
```

The stock Rhino USB ID is `ffff:2055`. Verify detection with
`lsusb -d ffff:2055`. The rule grants the active local desktop user access
through `uaccess`; it does not change the permissions shown by `ls -l` alone
when an ACL is used. DIY firmware with another product ID needs a matching
rule. Do not run TelemFFB as root.

Start the native application from the repository:

```bash
.venv/bin/python main.py
```

Qt normally selects Wayland automatically under Hyprland. Configuration is
stored in `~/.config/VPForce-TelemFFB/`, application data in
`~/.local/share/VPForce-TelemFFB/`, and logs/state in
`~/.local/state/VPForce-TelemFFB/`.

### Falcon BMS with Wine

Tested with Falcon BMS 4.38, a Wine prefix, and a Rhino on Omarchy. BMS uses
Win32 shared memory, which the native Linux process cannot read directly. A
Windows Python process in **the same Wine prefix as BMS** reads the telemetry
and sends it to TelemFFB over UDP on `127.0.0.1:34382`.

1. Find the prefix used to launch BMS. For example, if its launch script sets
   `WINEPREFIX="$HOME/.wine"`, use that value in the commands below. Replace it
   with your own prefix if different. BMS must already work in that prefix.
2. Install Windows Python 3.12 into that prefix using the official
   [Python for Windows installer](https://www.python.org/downloads/windows/).
   Select **Add python.exe to PATH** during installation. Verify it in a new
   terminal:

   ```bash
   WINEPREFIX="$HOME/.wine" wine python.exe --version
   ```

3. Install the Wine-side dependencies from the repository. This uses Windows
   Python and does not modify the Linux virtual environment:

   ```bash
   cd ~/VPforce-TelemFFB-Linux
   WINEPREFIX="$HOME/.wine" wine python.exe -m pip install -r requirements.txt
   ```

4. Start TelemFFB with `.venv/bin/python main.py`. Under **System → System
   Settings**, enable **Falcon BMS UDP**, select the Rhino, leave the default
   port `34382`, and save. Restart TelemFFB after changing these settings so
   the listener starts with the new configuration.
5. In a second terminal, start the forwarder from the repository root. The
   module form ensures the repository is on Python's import path:

   ```bash
   cd ~/VPforce-TelemFFB-Linux
   WINEPREFIX="$HOME/.wine" wine python.exe -m wine.bms_udp_forwarder
   ```

   Keep the terminal open. Before BMS starts, a message that shared memory
   could not be found is expected; the forwarder retries. Use `--port` if you
   configured a different port in TelemFFB.
6. Launch BMS normally, enter the cockpit and start the engine. TelemFFB
   should detect BMS and show telemetry and active effects. Stop the forwarder
   with Ctrl+C when finished.

### One-command BMS startup

After completing the setup above, start TelemFFB and the forwarder together:

```bash
cd ~/VPforce-TelemFFB-Linux
WINEPREFIX="$HOME/.wine" ./scripts/start-bms-telemffb.sh
```

To also start BMS, pass the path of your existing executable BMS launcher
script. For example:

```bash
WINEPREFIX="$HOME/.wine" ./scripts/start-bms-telemffb.sh --bms-launcher "$HOME/bin/start-bms.sh"
```

To shut down TelemFFB and the forwarder when BMS exits, add
`--exit-with-bms`:

```bash
WINEPREFIX="$HOME/.wine" ./scripts/start-bms-telemffb.sh --bms-launcher "$HOME/bin/start-bms.sh" --exit-with-bms
```

This requires a BMS launcher script that stays running for the entire BMS
session and exits when the simulator closes. A launcher that only starts BMS
and immediately exits cannot be used with `--exit-with-bms`. TelemFFB shuts
down through its normal cleanup so its active effects are released.

For an Omarchy Super+Space menu entry named `games.falcon-bms` that currently
launches `~/bin/start-bms.sh` and uses `~/.wine`, the following optional setup
connects that existing entry to the combined launcher:

```bash
python scripts/install-omarchy-bms-menu.py
```

The installer checks the existing entry, creates
`~/bin/start-bms-telemffb.sh`, and saves a backup of the menu file before
updating it. The existing `start-bms.sh` must remain running until BMS exits.
The wrapper logs to `~/.local/state/VPForce-TelemFFB/bms-launcher.log`. If the
menu or Wine setup differs, use the manual command above instead.

Use the same Wine prefix in the forwarder and the BMS launcher; check the
launcher script if it sets its own `WINEPREFIX`. Keep the terminal open to see
diagnostics. Closing TelemFFB stops the forwarder; BMS remains open and can be
closed normally. Use `--port 34382` to specify the UDP port if needed: it must
match the BMS UDP port configured in TelemFFB. This script does not install
dependencies or change the BMS launcher.

If the application stays at **Waiting**, check the forwarder's terminal for
`Connected to BMS shared memory`, verify both processes use the same Wine
prefix, and run `ss -lunp | grep 34382` to check the native listener. Recheck
the BMS enable setting and restart TelemFFB if no listener is present. Wine
`fixme` messages alone do not necessarily indicate a failure. Keep hold of
force-feedback controls during the first effect test.

### DCS telemetry

**Status:** not yet tested in this Linux port.

DCS's included Lua exporter sends UDP telemetry. Put `export/TelemFFB.lua` in
the DCS Saved Games export chain inside the Wine/Proton prefix and enable DCS
in TelemFFB; the native application listens on UDP 34380. The game and
TelemFFB do not need to share a Wine prefix.

TelemFFB is an open source, community-driven Python/Qt application that reads telemetry from a flight simulator and uses it to generate force feedback (FFB) effects. The goal is to make your stick more lively and increase immersion — not necessarily perfect realism.

> **Full documentation:** https://docs.vpforce.eu/telemffb/

## Simulator and device support

- **Falcon BMS 4.38:** telemetry and engine effects tested on Omarchy with a
  VPforce Rhino and BMS running under Wine. Other aircraft and effects need
  wider testing.
- **DCS World:** a UDP telemetry path is included, but it has not yet been
  tested in this Linux port. The DCS setup above is preliminary.
- **Other simulators:** this fork is not yet validated for them. Windows-only
  SimConnect and DirectInput integrations are disabled in the Linux build;
  do not assume the upstream Windows documentation applies here.
- **Devices:** the tested device is a VPforce Rhino. DIY VPforce hardware,
  other product IDs, and multi-device setups need further testing.

The upstream project's documentation describes additional features and
simulators; their presence upstream does not mean they work in this Linux fork.

## Configuration

TelemFFB 2.0 uses a delta-based XML configuration model. Only settings changed
from defaults are saved in `~/.config/VPForce-TelemFFB/`; system settings are
stored beside them in `settings.ini`, not in a Registry.

Settings can be modified in real time from the Settings tab while flying. Changes take effect almost immediately.

Aircraft profiles can be created, cloned, exported, and imported via the Profile Manager. Multiple profiles per aircraft are supported.

## Updating

From the repository directory, use `git pull --ff-only` to update a clean
checkout. If Git reports local changes or a conflict, review or save those
changes before updating.

## Contributing and Development

Linux-specific test reports and contributions are welcome in this repository.
The upstream project is [VPforce TelemFFB](https://github.com/walmis/VPforce-TelemFFB).

The effects framework is designed to make it straightforward to add or customize aircraft-specific behavior. Per-aircraft logic lives in the `aircrafts_dcs.py`, `aircrafts_msfs.py`, and similar files. Effect lifecycles are managed automatically through the `effects[]` object. For example, adding a bump effect when a gun round is fired:

```python
if self.has_changed("Gun") or self.has_changed("CannonShells"):
    effects["cm"].stop()
    effects["cm"].periodic(10, self.gun_vibration_intensity, 45, duration=50).start()
```
