"""Screen Reminder — Main entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from src.app.application import Application
from src.app.single_instance import SingleInstance

# Remove default stderr handler, add a rotating file handler
logger.remove()
logger.add(
    Path.home() / ".screen-reminder" / "logs" / "app.log",
    rotation="5 MB",
    retention="7 days",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
)
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")


def main() -> int:
    """Start Screen Reminder. Returns exit code."""
    logger.info("Screen Reminder starting...")

    # Ensure only one instance
    si = SingleInstance()
    if not si.acquire():
        logger.error("Another instance is already running.")
        return 1

    try:
        config_dir = Path.home() / ".screen-reminder"
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
