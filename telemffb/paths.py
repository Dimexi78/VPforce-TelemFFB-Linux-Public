"""XDG locations used by the Linux-only TelemFFB fork."""

from pathlib import Path

from platformdirs import PlatformDirs


_DIRS = PlatformDirs("VPForce-TelemFFB", roaming=False)


def config_dir() -> Path:
    """Return and create the user configuration directory."""
    path = Path(_DIRS.user_config_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir() -> Path:
    """Return and create the user data directory."""
    path = Path(_DIRS.user_data_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_dir() -> Path:
    """Return and create the user state directory."""
    path = Path(_DIRS.user_state_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path
