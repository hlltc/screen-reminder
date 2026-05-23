"""Cross-platform build script using PyInstaller.

Usage:
    uv run python build.py          # build for current platform
    uv run python build.py --clean  # clean and rebuild
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent
APP_NAME = "Screen Reminder"
ENTRY = str(ROOT / "src" / "__main__.py")
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def get_platform_config() -> dict:
    """Return PyInstaller args for the current platform."""
    is_mac = sys.platform == "darwin"
    is_win = sys.platform == "win32"

    common = [
        ENTRY,
        "--name", "ScreenReminder",
        "--onefile",
        "--windowed",                    # no console window
        "--clean",
        "--noconfirm",
        f"--distpath={DIST}",
        f"--workpath={BUILD}",
        "--add-data", f"{ROOT / 'assets'}{';' if is_win else ':'}assets",
        # Hidden imports that PyInstaller might miss
        "--hidden-import", "pystray._win32",
        "--hidden-import", "pystray._xorg",
        "--hidden-import", "pystray._darwin",
        "--hidden-import", "plyer.platforms.win.notification",
        "--hidden-import", "plyer.platforms.macosx.notification",
        "--hidden-import", "plyer.platforms.linux.notification",
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.keyboard._darwin",
        "--hidden-import", "pynput.keyboard._xorg",
        "--hidden-import", "pynput.mouse._win32",
        "--hidden-import", "pynput.mouse._darwin",
        "--hidden-import", "pynput.mouse._xorg",
        "--hidden-import", "darkdetect._windows_detect",
        "--hidden-import", "darkdetect._mac_detect",
        "--hidden-import", "darkdetect._linux_detect",
    ]

    if is_mac:
        common += [
            "--osx-bundle-identifier", "com.screenreminder.app",
            "--codesign-identity", "-",   # ad-hoc signing for local dev
        ]
    elif is_win:
        common += [
            "--uac-admin",
        ]

    return {
        "args": common,
        "output_name": f"ScreenReminder{'.exe' if is_win else ''}",
    }


def clean() -> None:
    """Remove previous build artifacts."""
    for d in (DIST, BUILD):
        if d.exists():
            shutil.rmtree(d)
    print(f"[clean] Removed {DIST} & {BUILD}")


def build() -> Path:
    """Run PyInstaller and return the output binary path."""
    config = get_platform_config()
    print(f"[build] Platform: {sys.platform}")
    print(f"[build] Running PyInstaller with {len(config['args'])} args ...")

    PyInstaller.__main__.run(config["args"])

    output = DIST / config["output_name"]
    if output.exists():
        size_mb = output.stat().st_size / (1024 * 1024)
        print(f"[build] SUCCESS → {output} ({size_mb:.1f} MB)")
    else:
        print(f"[build] ERROR: output not found at {output}")
        sys.exit(1)

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Screen Reminder")
    parser.add_argument("--clean", action="store_true", help="Clean before building")
    args = parser.parse_args()

    if args.clean:
        clean()

    build()


if __name__ == "__main__":
    main()
