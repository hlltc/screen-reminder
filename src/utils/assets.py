"""Asset path resolution — works in dev and PyInstaller frozen mode."""

from __future__ import annotations

import sys
from pathlib import Path


def _get_base() -> Path:
    if getattr(sys, "frozen", False):
        # PyInstaller: assets are unpacked next to the exe
        return Path(sys._MEIPASS)
    # Dev mode
    return Path(__file__).resolve().parents[2]


def get_icon_path(name: str = "eye-protect.png") -> str:
    """Return absolute path to an icon in assets/icons/."""
    return str(_get_base() / "assets" / "icons" / name)
