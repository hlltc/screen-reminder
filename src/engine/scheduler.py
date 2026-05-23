"""Smart Scheduler — orchestrates all health reminder timers."""

from __future__ import annotations

import datetime as _dt
import threading
import time
from typing import Callable

from loguru import logger

from src.data.database import get_session
from src.data.models import RestEvent
from src.engine.idle_detector import IdleDetector
from src.utils.config import AppConfig


class ReminderTask:
    """A single recurring reminder task."""

    def __init__(
        self,
        name: str,
        interval_minutes: int,
        callback: Callable[[], None],
        enabled: bool = True,
    ) -> None:
        self.name = name
        self.interval_minutes = interval_minutes
        self.callback = callback
        self.enabled = enabled
        self.last_triggered: _dt.datetime | None = None
        self._seconds_accumulated: float = 0.0
        self._last_tick: float | None = None


class Scheduler:
    """Background scheduler.

    - Always advances timers while the user is active (keyboard/mouse input).
    - Only fires callbacks (reminders) during configured work hours.
    - Pauses timers when the user is idle (away from PC).
    """

    def __init__(self, config: AppConfig, idle_detector: IdleDetector) -> None:
        self._config = config
        self._idle_detector = idle_detector
        self._tasks: list[ReminderTask] = []
        self._stopping = threading.Event()
        self._thread: threading.Thread | None = None
        self._tick_interval = 1.0  # seconds
        self._paused: bool = False
        self._pause_until: _dt.datetime | None = None

    # ── Public API ─────────────────────────────────────

    def add_task(self, task: ReminderTask) -> None:
        self._tasks.append(task)
        task._last_tick = time.monotonic()
        logger.info("Scheduler: added task '{}' (every {} min)", task.name, task.interval_minutes)

    def remove_task(self, name: str) -> None:
        self._tasks = [t for t in self._tasks if t.name != name]

    def reset_task(self, name: str) -> None:
        """Reset accumulated time for a task."""
        for t in self._tasks:
            if t.name == name:
                t._seconds_accumulated = 0.0
                t._last_tick = time.monotonic()
                t.last_triggered = None
                logger.debug("Scheduler: reset task '{}'", name)
                return

    def reset_all(self) -> None:
        for t in self._tasks:
            t._seconds_accumulated = 0.0
            t._last_tick = time.monotonic()
            t.last_triggered = None
        logger.debug("Scheduler: reset all tasks")

    def get_remaining_seconds(self, name: str) -> float | None:
        """Get remaining seconds until the next reminder for a task.

        The returned value counts down in real-time even outside work hours,
        so the UI display always updates.
        """
        for t in self._tasks:
            if t.name == name:
                elapsed = t._seconds_accumulated
                # Live time since last tick — only when user is active
                if t._last_tick and not self._idle_detector.is_idle:
                    delta = time.monotonic() - t._last_tick
                    elapsed += delta
                return max(0.0, t.interval_minutes * 60 - elapsed)
        return None

    def pause(self, minutes: int) -> None:
        """Pause all reminders for `minutes` minutes."""
        self._paused = True
        self._pause_until = _dt.datetime.now() + _dt.timedelta(minutes=minutes)
        # Reset all task accumulators so timers start fresh after pause
        for t in self._tasks:
            t._seconds_accumulated = 0.0
            t._last_tick = time.monotonic()
        logger.info("Scheduler: paused for {} minutes", minutes)

    def resume(self) -> None:
        """Manually resume reminders."""
        self._paused = False
        self._pause_until = None
        self.reset_all()
        logger.info("Scheduler: resumed")

    def start(self) -> None:
        self._stopping.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        self._stopping.set()
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("Scheduler stopped")

    # ── Internals ──────────────────────────────────────

    def _is_active_hours(self) -> bool:
        """Whether reminders should fire (but timers always run)."""
        now = _dt.datetime.now()
        if self._paused:
            if self._pause_until and now < self._pause_until:
                return False
            self._paused = False  # pause expired
        return self._config.is_work_time(now) and not self._config.is_lunch_time(now)

    def _run(self) -> None:
        while not self._stopping.is_set():
            self._stopping.wait(self._tick_interval)
            if self._stopping.is_set():
                break

            # Always tick when user is active (time tracking always runs)
            if not self._idle_detector.is_idle:
                self._tick_tasks()
            else:
                # User away — reset _last_tick so idle time isn't counted
                for t in self._tasks:
                    t._last_tick = time.monotonic()

    def _tick_tasks(self) -> None:
        now = time.monotonic()
        active_hours = self._is_active_hours()

        for task in self._tasks:
            if not task.enabled:
                continue
            if task._last_tick is None:
                task._last_tick = now
                continue

            delta = now - task._last_tick
            task._last_tick = now
            task._seconds_accumulated += delta

            interval_s = task.interval_minutes * 60
            if task._seconds_accumulated >= interval_s:
                task._seconds_accumulated = 0.0
                # Only fire callbacks during active hours
                if active_hours:
                    logger.info("Scheduler: triggering '{}'", task.name)
                    task.last_triggered = _dt.datetime.now()
                    try:
                        task.callback()
                    except Exception:
                        logger.exception("Scheduler: task '{}' callback failed", task.name)
                else:
                    logger.debug(
                        "Scheduler: skipped '{}' — outside active hours", task.name
                    )
