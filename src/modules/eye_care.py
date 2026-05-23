"""Eye Care module — 20-20-20 rule reminder."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from src.data.data_access import log_event
from src.engine.notification import send_notification
from src.engine.scheduler import Scheduler
from src.ui.overlay import CountdownOverlay
from src.utils.config import AppConfig


class EyeCareModule(QObject):
    """Manages 20-20-20 eye care reminders.

    Soft notification at interval → countdown overlay for rest duration.
    """

    eye_break_triggered = Signal()
    eye_break_finished = Signal()

    def __init__(self, config: AppConfig, scheduler: Scheduler) -> None:
        super().__init__()
        self._config = config
        self._scheduler = scheduler
        self._overlay: CountdownOverlay | None = None

    def start(self) -> None:
        from src.engine.scheduler import ReminderTask

        task = ReminderTask(
            name="eye_care",
            interval_minutes=self._config.eye_care_interval_min,
            callback=self._on_reminder,
            enabled=self._config.eye_care_enabled,
        )
        self._scheduler.add_task(task)

    def _on_reminder(self) -> None:
        log_event("eye_care", "reminded")
        self.eye_break_triggered.emit()

        # Stage 1: soft notification
        send_notification(
            title="眼睛休息一下",
            message="请看向 6 米外的物体，持续 20 秒 👁",
            timeout=8,
        )

        # Stage 2: overlay countdown (after short delay to allow user to respond)
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
            seconds=self._config.eye_care_rest_seconds,
            title="眼睛休息",
            subtitle="看向 6 米外，保持 20 秒",
        )

    def _on_finished(self) -> None:
        log_event("eye_care", "completed")
        self._scheduler.reset_task("eye_care")
        self.eye_break_finished.emit()

    def _on_skipped(self) -> None:
        log_event("eye_care", "skipped")
        self._scheduler.reset_task("eye_care")
        self.eye_break_finished.emit()
