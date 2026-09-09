# VPforce TelemFFB

> This fork is Linux-only, targeting Arch Linux / Omarchy, Wayland, and
> VPforce Rhino/DIY HID hardware. It deliberately contains no Wine,
> DirectInput, Registry, or Windows shared-memory runtime path.

## Arch Linux / Omarchy quick start

```bash
sudo pacman -S --needed git python python-pyqt6 hidapi libusb
git clone <this-fork-url> VPforce-TelemFFB
cd VPforce-TelemFFB
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Qt 6 uses Wayland automatically under Hyprland. If a local Qt setup prefers
X11, launch with `QT_QPA_PLATFORM=wayland python main.py`.

The default Rhino USB id in this source tree is `ffff:2055`. Install the
included udev rule, unplug/replug the device, then verify it is accessible as
your normal user:

```bash
sudo install -Dm644 udev/99-vpforce-telemffb.rules /etc/udev/rules.d/99-vpforce-telemffb.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
lsusb -d ffff:2055
```

DIY firmware with a different product ID must use that exact id in a second
udev-rule line. Do not run TelemFFB as root.

Configuration is stored in `~/.config/VPForce-TelemFFB/`, application data in
`~/.local/share/VPForce-TelemFFB/`, and logs/state in
`~/.local/state/VPForce-TelemFFB/`.

### Proton telemetry

DCS's included Lua exporter already sends OS-independent UDP telemetry. Put
`export/TelemFFB.lua` in the DCS Saved Games export chain inside the Wine/Proton
prefix and enable DCS in TelemFFB; the native application listens on UDP 34380.
The game and TelemFFB do not need to share a Wine prefix.

Falcon BMS's original integration was a Win32 named shared-memory reader, so it
cannot cross from Wine into this native process. This fork listens on UDP 34382
when BMS is enabled. The included Wine-side forwarder sends the existing
TelemFFB semicolon-delimited frame format to `127.0.0.1:34382`; run it from
the Falcon BMS Wine prefix:

```bash
cd /path/to/VPforce-TelemFFB
wine python.exe wine/bms_udp_forwarder.py --host 127.0.0.1 --port 34382
```

The Wine Python environment must contain this checkout's runtime dependencies.
Start the forwarder before launching BMS, then enable BMS in the native
TelemFFB settings. It reuses the upstream BMS shared-memory parser unchanged
and forwards its already-normalized UDP frame bytes.

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
