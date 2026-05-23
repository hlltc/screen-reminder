"""Hydration module — water drinking reminder."""

from __future__ import annotations

import datetime as _dt

from PySide6.QtCore import QObject, Signal

from src.data.data_access import get_today_hydration_ml, log_hydration, log_event
from src.engine.notification import send_notification
from src.engine.scheduler import Scheduler
from src.utils.config import AppConfig


class HydrationModule(QObject):
    """Manages timed hydration reminders with quick-drink tracking."""

    hydration_updated = Signal()
    hydration_goal_reached = Signal()
    hydration_reminder_triggered = Signal()

    def __init__(self, config: AppConfig, scheduler: Scheduler) -> None:
        super().__init__()
        self._config = config
        self._scheduler = scheduler

    def start(self) -> None:
        from src.engine.scheduler import ReminderTask

        task = ReminderTask(
            name="hydration",
            interval_minutes=self._config.hydration_interval_min,
            callback=self._on_reminder,
            enabled=self._config.hydration_enabled,
        )
        self._scheduler.add_task(task)

    # ── Public API ─────────────────────────────────────

    def record_drink(self, amount_ml: int | None = None) -> int:
        """Record a drink event. Returns total ml drunk today."""
        if amount_ml is None:
            amount_ml = self._config.hydration_single_ml
        log_hydration(amount_ml)
        log_event("hydration", "completed")
        self.hydration_updated.emit()
        self._scheduler.reset_task("hydration")

        today_ml = get_today_hydration_ml()
        if today_ml >= self._config.hydration_daily_ml:
            self.hydration_goal_reached.emit()
        return today_ml

    def skip(self) -> None:
        log_event("hydration", "skipped")
        self._scheduler.reset_task("hydration")

    @property
    def today_ml(self) -> int:
        return get_today_hydration_ml()

    @property
    def daily_goal_ml(self) -> int:
        return self._config.hydration_daily_ml

    @property
    def progress_ratio(self) -> float:
        return min(1.0, self.today_ml / max(1, self.daily_goal_ml))

    # ── Internals ──────────────────────────────────────

    def _on_reminder(self) -> None:
        log_event("hydration", "reminded")
        send_notification(
            title="喝水提醒",
            message="该喝水了！建议喝 200ml",
            timeout=10,
        )
        self.hydration_reminder_triggered.emit()
        self.hydration_updated.emit()
