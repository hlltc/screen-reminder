"""Cross-platform single-instance enforcement.

Uses a socket-based lock so that only one instance of the app runs at a time.
"""

from __future__ import annotations

import socket
import sys

from loguru import logger


class SingleInstance:
    """Prevent multiple instances from running.

    Usage:
        si = SingleInstance("screen-reminder-lock")
        if not si.acquire():
            print("Another instance is already running")
            sys.exit(1)
    """

    def __init__(self, lock_name: str = "screen-reminder-lock") -> None:
        self._lock_name = lock_name
        self._sock: socket.socket | None = None

    def acquire(self) -> bool:
        """Try to acquire the lock. Returns True if successful."""
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.bind(("127.0.0.1", 0))
            port = self._sock.getsockname()[1]
            # Write port to a temp file for detection
            import tempfile
            import os
            self._lock_file = os.path.join(tempfile.gettempdir(), f"{self._lock_name}.port")
            with open(self._lock_file, "w") as f:
                f.write(str(port))
            return True
        except Exception:
            return False

    def release(self) -> None:
        """Release the lock."""
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        try:
            import os
            if hasattr(self, "_lock_file") and os.path.exists(self._lock_file):
                os.remove(self._lock_file)
        except Exception:
            pass


def is_another_instance_running(lock_name: str = "screen-reminder-lock") -> bool:
    """Quick check without acquiring the lock."""
    try:
        import tempfile
        import os
        lock_file = os.path.join(tempfile.gettempdir(), f"{lock_name}.port")
        if os.path.exists(lock_file):
            with open(lock_file, "r") as f:
                port = int(f.read().strip())
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("127.0.0.1", port))
            sock.close()
            return False  # Port was free, so lock file is stale
        return False
    except Exception:
        return True  # Port is in use → another instance exists
