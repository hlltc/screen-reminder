"""Screen Reminder — Main entry point."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger

from src.app.application import Application
from src.app.single_instance import SingleInstance


def _get_user_dir() -> Path:
    """Get user config directory robustly (works in PyInstaller too)."""
    # PyInstaller may mess with env; try HOME/USERPROFILE first
    for var in ("HOME", "USERPROFILE"):
        val = os.environ.get(var)
        if val:
            return Path(val).resolve()
    # fallback: expand ~
    try:
        return Path(os.path.expanduser("~")).resolve()
    except Exception:
        # ultimate fallback
        return Path(sys.executable).parent


def _setup_logging() -> None:
    """Configure loguru handlers. Never crash on logging setup failure."""
    logger.remove()
    # Always log to stderr at INFO level
    logger.add(sys.stderr, level="INFO",
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    try:
        log_dir = _get_user_dir() / ".screen-reminder" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_dir / "app.log",
            rotation="5 MB",
            retention="7 days",
            level="DEBUG",
            backtrace=True,
            diagnose=True,
        )
    except Exception:
        logger.warning("Cannot create log file — logging to stderr only")


_setup_logging()


def main() -> int:
    """Start Screen Reminder. Returns exit code."""
    logger.info("Screen Reminder starting...")

    # Ensure only one instance
    si = SingleInstance()
    if not si.acquire():
        logger.error("Another instance is already running.")
        return 1

    try:
        config_dir = _get_user_dir() / ".screen-reminder"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.json"

        app = Application(config_path)
        exit_code = app.run()
        return exit_code
    except Exception:
        logger.exception("Fatal error")
        return 1
    finally:
        si.release()


if __name__ == "__main__":
    sys.exit(main())
