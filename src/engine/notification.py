"""Cross-platform desktop notifications via plyer."""

from __future__ import annotations

from loguru import logger
from plyer import notification


def send_notification(
    title: str,
    message: str,
    timeout: int = 10,
    app_name: str = "Screen Reminder",
    app_icon: str = "",
) -> bool:
    """Send a desktop notification.

    Returns True on success, False (silently) on failure so callers don't crash.
    """
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=timeout,
            app_name=app_name,
            app_icon=app_icon,
        )
        logger.debug("Notification sent: {} – {}", title, message[:40])
        return True
    except Exception:
        logger.warning("Failed to send notification: {} – {}", title, message[:40])
        return False
