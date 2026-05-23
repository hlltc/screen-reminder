"""Spine Care module — sedentary / standing reminder."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from src.data.data_access import log_event
from src.engine.notification import send_notification
from src.engine.scheduler import Scheduler
from src.ui.overlay import CountdownOverlay
from src.utils.config import AppConfig


class SpineCareModule(QObject):
    """Manages sedentary (久坐) reminders.

    After configured interval, notifies user to stand up; shows overlay countdown.
    """

    sedentary_break_triggered = Signal()
    sedentary_break_finished = Signal()

    def __init__(self, config: AppConfig, scheduler: Scheduler) -> None:
        super().__init__()
        self._config = config
        self._scheduler = scheduler
        self._overlay: CountdownOverlay | None = None

    def start(self) -> None:
        from src.engine.scheduler import ReminderTask

        task = ReminderTask(
            name="sedentary",
            interval_minutes=self._config.sedentary_interval_min,
            callback=self._on_reminder,
            enabled=self._config.sedentary_enabled,
        )
        self._scheduler.add_task(task)

    def _on_reminder(self) -> None:
        log_event("sedentary", "reminded")
        self.sedentary_break_triggered.emit()

        send_notification(
            title="久坐提醒",
            message="该站起来活动一下了！走一走，伸个懒腰 🚶",
            timeout=10,
        )

        from PySide6.QtCore import QTimer
        QTimer.singleShot(
            self._config.overlay_warning_timeout_seconds * 1000,
            self._show_overlay,
        )

    def _show_overlay(self) -> None:
        if self._overlay is not None:
            self._overlay.close()
        self._overlay = CountdownOverlay(self._config)
        self._overlay.finished.connect(self._on_finished)
        self._overlay.skipped.connect(self._on_skipped)
        self._overlay.start_countdown(
            seconds=self._config.sedentary_lock_seconds,
            title="该站起来了！",
            subtitle="离开座位走动 3 分钟，保护腰椎",
        )

    def _on_finished(self) -> None:
        log_event("sedentary", "completed")
        self._scheduler.reset_task("sedentary")
        self.sedentary_break_finished.emit()

    def _on_skipped(self) -> None:
        log_event("sedentary", "skipped")
        self._scheduler.reset_task("sedentary")
        self.sedentary_break_finished.emit()
