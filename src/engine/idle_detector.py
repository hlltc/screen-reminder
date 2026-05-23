"""Idle detection via pynput — monitors keyboard / mouse inactivity."""

from __future__ import annotations

import time
import threading
from typing import Callable

from pynput.keyboard import Key, Listener as KbListener
from pynput.mouse import Listener as MsListener

from loguru import logger


class IdleDetector:
    """Tracks user input to determine if the user is idle (away from PC)."""

    def __init__(self, threshold_seconds: float = 120) -> None:
        self._threshold = threshold_seconds
        self._last_activity: float = time.monotonic()
        self._active = False
        self._lock = threading.Lock()
        self._kb_listener: KbListener | None = None
        self._ms_listener: MsListener | None = None
        self._on_become_idle: Callable[[], None] | None = None
        self._on_become_active: Callable[[], None] | None = None
        self._monitor_thread: threading.Thread | None = None
        self._stopping = threading.Event()

    # ── Public API ─────────────────────────────────────

    def start(self) -> None:
        self._start_listeners()
        self._stopping.clear()
        self._monitor_thread = threading.Thread(target=self._idle_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("IdleDetector started (threshold={}s)", self._threshold)

    def stop(self) -> None:
        self._stopping.set()
        self._stop_listeners()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=3)
        logger.info("IdleDetector stopped")

    @property
    def is_idle(self) -> bool:
        with self._lock:
            return (time.monotonic() - self._last_activity) >= self._threshold

    @property
    def idle_seconds(self) -> float:
        with self._lock:
            return max(0.0, time.monotonic() - self._last_activity)

    @property
    def threshold(self) -> float:
        return self._threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        self._threshold = value

    def reset(self) -> None:
        with self._lock:
            self._last_activity = time.monotonic()

    def set_callbacks(
        self,
        on_become_idle: Callable[[], None] | None = None,
        on_become_active: Callable[[], None] | None = None,
    ) -> None:
        self._on_become_idle = on_become_idle
        self._on_become_active = on_become_active

    # ── Internals ──────────────────────────────────────

    def _on_activity(self, *args) -> None:
        previously_idle = self.is_idle
        with self._lock:
            self._last_activity = time.monotonic()
        if previously_idle and self._on_become_active:
            logger.debug("User became active after idle")
            self._on_become_active()

    def _start_listeners(self) -> None:
        try:
            self._kb_listener = KbListener(on_press=self._on_activity, on_release=self._on_activity)
            self._kb_listener.start()
        except Exception:
            logger.warning("Keyboard listener unavailable")

        try:
            self._ms_listener = MsListener(
                on_move=self._on_activity,
                on_click=self._on_activity,
                on_scroll=self._on_activity,
            )
            self._ms_listener.start()
        except Exception:
            logger.warning("Mouse listener unavailable")

    def _stop_listeners(self) -> None:
        for ln in (self._kb_listener, self._ms_listener):
            if ln is not None:
                try:
                    ln.stop()
                except Exception:
                    pass

    def _idle_loop(self) -> None:
        """Continuously check idle state in the background."""
        was_idle = False
        while not self._stopping.is_set():
            self._stopping.wait(2.0)  # check every 2s
            now_idle = self.is_idle
            if now_idle and not was_idle and self._on_become_idle:
                logger.info("User became idle")
                self._on_become_idle()
            was_idle = now_idle
