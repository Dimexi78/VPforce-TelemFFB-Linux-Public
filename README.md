# VPforce TelemFFB

This fork runs TelemFFB natively on Linux and targets Arch Linux / Omarchy,
Wayland, and VPforce Rhino/DIY HID hardware. Falcon BMS runs in Wine and uses
an additional Wine-side telemetry forwarder.

## Arch Linux / Omarchy setup

Install the native dependencies and clone the repository:

```bash
sudo pacman -S --needed git python python-pyqt6 hidapi libusb
git clone https://github.com/Dimexi78/VPforce-TelemFFB-Linux.git
cd VPforce-TelemFFB-Linux
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Access to this private repository requires GitHub authentication. On Python
3.14 the requirements select a newer NumPy, because the pinned 2.3.0 release
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

If the application stays at **Waiting**, check the forwarder's terminal for
`Connected to BMS shared memory`, verify both processes use the same Wine
prefix, and run `ss -lunp | grep 34382` to check the native listener. Recheck
the BMS enable setting and restart TelemFFB if no listener is present. Wine
`fixme` messages alone do not necessarily indicate a failure. Keep hold of
force-feedback controls during the first effect test.

### DCS telemetry

DCS's included Lua exporter sends UDP telemetry. Put `export/TelemFFB.lua` in
the DCS Saved Games export chain inside the Wine/Proton prefix and enable DCS
in TelemFFB; the native application listens on UDP 34380. The game and
TelemFFB do not need to share a Wine prefix.

TelemFFB is an open source, community-driven Python/Qt application that reads telemetry from a flight simulator and uses it to generate force feedback (FFB) effects. The goal is to make your stick more lively and increase immersion — not necessarily perfect realism.

> **Full documentation:** https://docs.vpforce.eu/telemffb/

## Supported Simulators

- **DCS World** — native FFB sim; TelemFFB adds supplemental haptic effects on top
- **Microsoft Flight Simulator (2020/2024)** — no native FFB; TelemFFB implements full dynamic FFB
- **X-Plane 11/12** — no native FFB; TelemFFB implements full dynamic FFB via an auto-installed plugin
- **IL-2 Sturmovik** — native FFB sim; TelemFFB adds supplemental haptic effects on top
- **Falcon BMS 4.38+** *(beta)* — limited native effects; TelemFFB adds haptic effects

For sims **with** native FFB (DCS, IL-2, BMS), TelemFFB primarily adds supplemental effects like engine rumble, gunfire, and helicopter ETL shaking while the sim manages the spring/trim system.

For sims **without** native FFB (MSFS, X-Plane), TelemFFB handles the **entire** FFB implementation, including dynamic spring forces based on calculated aerodynamic pressure throughout the aircraft's speed envelope.

## Legacy Windows quick start

Download the latest release, extract the zip, and run the exe — no installer needed.

- **Stable releases:** https://github.com/walmis/VPforce-TelemFFB/releases
- **Development builds** (auto-updated): https://vpforcecontrols.com/downloads/TelemFFB/?C=M;O=D

On first launch, you'll be guided through the system settings to configure your simulator(s) and device(s). See the [documentation](https://docs.vpforce.eu/telemffb/) for full setup details.

## Features

Not all features are available in all simulators.

**Haptic / Supplemental Effects**
- Engine rumble — piston, jet, and helicopter, including afterburner
- Angle of attack and stall buffeting
- Turbulence (dynamic, wind-data-driven gust simulation)
- Weapon release and countermeasure release effects
- Gunfire vibration
- Ground roll and touchdown effects
- Runway rumble and nosewheel shimmy
- Gear, flap, spoiler, speedbrake, and canopy motion effects
- Buffeting from deployed gear and spoilers
- Helicopter ETL (effective translational lift) effect
- Helicopter VRS (vortex ring state) effect
- Helicopter overspeed shaking
- Damage effect
- Uncoordinated turn effect

**Flight Control Forces (MSFS / X-Plane)**
- Dynamic spring force based on aerodynamic pressure across the aircraft's speed envelope
- Fly-By-Wire (FBW) static spring mode
- Spring-centered dynamic mode (minimum spring floor + dynamic forces)
- Advanced spring curve editor — custom per-axis gain mapping over a configurable airspeed range
- G-force effect with exponential or custom-curve configuration
- Deceleration effect (forward force when braking)
- Trim following
- Autopilot following (fixed-wing)
- Helicopter force trim emulation with trim-release button support
- Low hydraulic pressure effect (increased damper/friction/inertia on hyd loss)

**Special Implementations**
- HPG Airbus H145 / H160 (MSFS): Full AFCS integration — collective and cyclic follow the autopilot, force trim release, hands-on detection
- FlyInside helicopters (MSFS): Vibration-model integration
- FFB rudder pedals: Dynamic/fixed/unsprung spring modes, nose-wheel shimmy, trim following, autopilot following
- FFB collective: Configurable damper/friction/inertia, haptic effects playback, HPG AFCS integration

## Supported Devices

TelemFFB supports VPforce FFB devices:

- **VPforce Rhino** joystick base
- **DIY joystick bases** using VPforce motor kits
- **DIY FFB rudder pedals** using VPforce kits
- **DIY FFB collective** using VPforce kits
- **DIY FFB trim wheel** using VPforce kits (MSFS only)

Multiple devices can be run simultaneously. TelemFFB will auto-launch child instances for each additional device, all managed from a single master window.

## Configuration

TelemFFB 2.0 uses a delta-based XML configuration model. Only settings changed
from defaults are saved in `~/.config/VPForce-TelemFFB/`; system settings are
stored beside them in `settings.ini`, not in a Registry.

Settings can be modified in real time from the Settings tab while flying. Changes take effect almost immediately.

Aircraft profiles can be created, cloned, exported, and imported via the Profile Manager. Multiple profiles per aircraft are supported.

## Antivirus / False Positives

TelemFFB is packaged with PyInstaller, which can trigger false positives in Windows Defender and other antivirus tools. The application is safe — all source code is publicly auditable and dependencies are standard PyPI packages. If flagged, allow the app manually or submit it to your AV vendor for review.

## Installing and Running from Source

**Requirements:**
- Python 3.11+
- Git

**Steps:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

For DCS under Proton, install the Lua exporter manually as described in the
Arch Linux section.

**Updating from source:**
```bash
git pull
```

If local changes conflict:
```bash
git reset --hard origin/master
git pull
```

## Contributing and Development

Pull requests and issues are welcome on the [GitHub page](https://github.com/walmis/VPforce-TelemFFB).

The effects framework is designed to make it straightforward to add or customize aircraft-specific behavior. Per-aircraft logic lives in the `aircrafts_dcs.py`, `aircrafts_msfs.py`, and similar files. Effect lifecycles are managed automatically through the `effects[]` object. For example, adding a bump effect when a gun round is fired:

```python
if self.has_changed("Gun") or self.has_changed("CannonShells"):
    effects["cm"].stop()
    effects["cm"].periodic(10, self.gun_vibration_intensity, 45, duration=50).start()
```
