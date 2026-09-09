# Linux port audit and staged plan

This fork targets Linux only. The first implementation phase deliberately
changes bootstrap, persistent paths, device access, and the two requested
telemetry paths without changing aircraft effect calculations.

## Audit findings

| Area | Upstream implementation | Linux decision |
| --- | --- | --- |
| User configuration | `%LOCALAPPDATA%` in `main.py`; `QSettings` defaulted to the Windows Registry | Use `platformdirs`: config is `~/.config/VPForce-TelemFFB`; `settings.ini` replaces Registry storage. |
| Logs | `%LOCALAPPDATA%/.../log` | `~/.local/state/VPForce-TelemFFB/log`. |
| Master lock | Win32 named mutex | `flock` lock in `$XDG_RUNTIME_DIR` (or `/tmp`) with the same process-lifetime semantics. |
| VPforce hardware | `telemffb.hw.hid` already uses the cross-platform HIDAPI C ABI; `ffb_rhino.py` preloaded `hidapi.dll` | Keep HID protocol/effect code unchanged; use the Arch `hidapi` shared library and udev access. |
| DirectInput / tap bridge | `ffb_dinput.py`, `ffb_tap.py`, tap dialogs/installers, bridge DLL and game-folder `dinput8.dll` | Not a Linux capability. It is removed from startup; remaining UI/package cleanup is a later deletion pass. |
| DCS transport | Win32 shared-memory command channel plus UDP listener on 34380 | Retain native UDP receive. Do not load Win32 IPC or try automatic export installation into a Wine prefix. |
| Falcon BMS transport | Win32 shared-memory mappings through `BMSSharedMem.py` | Replace listener with UDP 34382. Wine-side forwarding is required because Wine mappings are not native Linux shared memory. |
| MSFS / SimConnect | Windows SimConnect DLL/custom package | Omitted from runtime requirements and disabled in this Linux bootstrap. |
| Updater/build | PyInstaller spec, `.exe`, `SelfUpdater_src`, bundled DLLs and batch resource script | Not part of source execution; remove with the final Windows-artifact cleanup phase. |

## Staged plan

1. **Bootstrap and paths — implemented.** XDG storage, INI settings,
   Linux process lock, system HIDAPI, and Arch/udev documentation.
2. **Native device validation — requires hardware.** Verify `hid.enumerate()`
   exposes the Rhino and that an effect can be created without root. The
   source confirms the default identity is `ffff:2055`; do not assume a DIY
   product id.
3. **DCS UDP validation — requires Proton DCS.** Enable DCS, run the Lua
   exporter, and confirm packets reach UDP 34380. The exporter already sends
   platform-neutral UDP, so no shared Wine prefix is needed.
4. **BMS forwarding — implemented, requires validation.**
   `wine/bms_udp_forwarder.py` runs in the BMS Wine prefix, reuses the existing
   shared-memory parser, and transmits normalized frames to UDP 34382. The
   native application never attaches to BMS's Win32 mappings.
5. **Deletion pass.** Remove DirectInput/tap, MSFS, updater, installer,
   `winpaths`, BMS shared-memory, and remaining Windows-only UI/imports;
   update tests to stop importing these modules.

## Verification performed in this workspace

`python -m compileall -q main.py telemffb` completed successfully using the
available Python 3.14 interpreter. There is no Linux/Arch runtime or VPforce
hardware attached to this workspace, so Qt launch, HID access, DCS, and BMS
are explicitly unverified.
