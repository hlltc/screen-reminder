"""Application lifecycle — QApplication wrapper that owns all services."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from loguru import logger

from src.data.database import init_db
from src.engine.idle_detector import IdleDetector
from src.engine.scheduler import Scheduler
from src.modules.eye_care import EyeCareModule
from src.modules.hydration import HydrationModule
from src.modules.spine_care import SpineCareModule
from src.tray.tray_icon import TrayManager
from src.ui.settings import SettingsDialog
from src.utils.config import AppConfig
from src.utils.constants import APP_VERSION


class Application:
    """Top-level application controller."""

    def __init__(self, config_path: Path, demo_mode: bool = False) -> None:
        self._config = AppConfig.load(config_path)
        self._config._config_path = config_path
        self._demo_mode = demo_mode

        if demo_mode:
            self._apply_demo_overrides()

        # Init database
        init_db(self._config.db_path)
        logger.info("Database initialised at {}", self._config.db_path)

        # Qt application
        self._qapp = QApplication(sys.argv)
        self._qapp.setQuitOnLastWindowClosed(False)
        self._qapp.setApplicationName("Screen Reminder")

        # Core engines
        self._idle_detector = IdleDetector(
            threshold_seconds=self._config.idle_threshold_seconds
        )
        self._scheduler = Scheduler(self._config, self._idle_detector)

        # Health modules
        self._eye_module = EyeCareModule(self._config, self._scheduler)
        self._spine_module = SpineCareModule(self._config, self._scheduler)
        self._hydration_module = HydrationModule(self._config, self._scheduler)

        # Tray
        self._tray = TrayManager(
            self._config,
            self._hydration_module,
            self._scheduler,
        )
        self._tray.quit_requested.connect(self._on_quit)
        self._tray.settings_requested.connect(self._open_settings)
        self._tray.drink_requested.connect(self._hydration_module.record_drink)

        # Wire module signals → tray icon color changes
        self._eye_module.eye_break_triggered.connect(
            lambda: self._tray.set_status_color("#FFD93D")
        )
        self._spine_module.sedentary_break_triggered.connect(
            lambda: self._tray.set_status_color("#FF6B6B")
        )
        self._hydration_module.hydration_reminder_triggered.connect(
            lambda: self._tray.show_message("💧 喝水提醒", "该喝水了！打开左键弹窗点一下")
        )
        self._hydration_module.hydration_goal_reached.connect(
            lambda: self._tray.set_status_color("#4ECDC4")
        )
        self._eye_module.eye_break_finished.connect(
            lambda: self._tray.set_status_color("#4ECDC4")
        )
        self._spine_module.sedentary_break_finished.connect(
            lambda: self._tray.set_status_color("#4ECDC4")
        )

    def _apply_demo_overrides(self) -> None:
        """Set 24/7 work hours & disable idle detection for demo.

        Rest/lock durations keep user-configured values so the UI is
        representative of normal operation.
        """
        self._config.work_start_h = 0
        self._config.work_end_h = 23
        self._config.lunch_start_h = 3
        self._config.lunch_end_h = 3    # no lunch
        self._config.overlay_warning_timeout_seconds = 3
        self._config.idle_threshold_seconds = 9999
        logger.info("🎬 Demo mode: 24/7 hours, {}s eye / {}s sed rest",
                    self._config.eye_care_rest_seconds,
                    self._config.sedentary_lock_seconds)

    def run(self) -> int:
        """Start all services and enter the Qt event loop."""
        logger.info("Starting Screen Reminder v{}", APP_VERSION)

        self._idle_detector.set_callbacks(
            on_become_idle=self._on_idle,
            on_become_active=self._on_active,
        )
        self._idle_detector.start()

        self._eye_module.start()
        self._spine_module.start()
        self._hydration_module.start()
        self._scheduler.start()

        if self._demo_mode:
            self._start_demo_triggers()

        logger.info("All services started.")
        return self._qapp.exec()

    def _start_demo_triggers(self) -> None:
        """Fire each reminder with staggered delay so they don't overlap."""
        from PySide6.QtCore import QTimer
        logger.info("🎬 Demo: reminders will fire at +8s / +16s / +24s")
        QTimer.singleShot(8_000, self._eye_module._on_reminder)
        QTimer.singleShot(16_000, self._hydration_module._on_reminder)
        QTimer.singleShot(24_000, self._spine_module._on_reminder)

    def _open_settings(self) -> None:
        """Open the settings dialog and reconfigure services on save."""
        dialog = SettingsDialog(self._config, parent=None)
        dialog.config_changed.connect(self._on_config_changed)
        dialog.exec()

    def _on_config_changed(self) -> None:
        """Apply config changes at runtime."""
        logger.info("Config changed — reloading settings")
        logger.info(
            "New intervals: eye={}min sed={}min hyd={}min",
            self._config.eye_care_interval_min,
            self._config.sedentary_interval_min,
            self._config.hydration_interval_min,
        )

        # Update idle detector threshold
        self._idle_detector.threshold = self._config.idle_threshold_seconds

        # Eye care
        self._scheduler.remove_task("eye_care")
        if self._config.eye_care_enabled:
            from src.engine.scheduler import ReminderTask
            task = ReminderTask(
                name="eye_care",
                interval_minutes=self._config.eye_care_interval_min,
                callback=self._eye_module._on_reminder,
                enabled=True,
            )
            self._scheduler.add_task(task)

        # Sedentary
        self._scheduler.remove_task("sedentary")
        if self._config.sedentary_enabled:
            from src.engine.scheduler import ReminderTask
            task = ReminderTask(
                name="sedentary",
                interval_minutes=self._config.sedentary_interval_min,
                callback=self._spine_module._on_reminder,
                enabled=True,
            )
            self._scheduler.add_task(task)

        # Hydration
        self._scheduler.remove_task("hydration")
        if self._config.hydration_enabled:
            from src.engine.scheduler import ReminderTask
            task = ReminderTask(
                name="hydration",
                interval_minutes=self._config.hydration_interval_min,
                callback=self._hydration_module._on_reminder,
                enabled=True,
            )
            self._scheduler.add_task(task)

    def _on_quit(self) -> None:
        """Clean shutdown."""
        logger.info("Shutting down...")
        self._scheduler.stop()
        self._idle_detector.stop()
        self._tray.stop()
        self._config.save()
        self._qapp.quit()

    def _on_idle(self) -> None:
        logger.info("User is idle — pausing timers")

    def _on_active(self) -> None:
        logger.info("User is active — resuming timers")
        self._scheduler.reset_all()
