"""System tray manager with popup health widget.

Uses PySide6 QSystemTrayIcon for cross-platform tray support.
Right-click context menu is shown manually (no setContextMenu)
with a Windows-specific foreground focus workaround.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QPoint, Qt, Signal, QTimer
from PySide6.QtGui import QAction, QColor, QCursor, QIcon, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from src.engine.scheduler import Scheduler
from src.modules.hydration import HydrationModule
from src.utils.assets import get_icon_path
from src.utils.config import AppConfig


# ── Helpers ────────────────────────────────────────────────


def _load_tray_icon() -> QIcon:
    """Load the application icon for the system tray."""
    path = get_icon_path("eye-protect.png")
    return QIcon(path)


def _format_time(minutes: int, seconds: int) -> str:
    if minutes > 0:
        return f"{minutes} 分 {seconds} 秒"
    return f"{seconds} 秒"


def _win_foreground_hack() -> None:
    """On Windows, call SetForegroundWindow so the popup menu receives input."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        app = QApplication.instance()
        if app is None:
            return
        widgets = app.topLevelWidgets()
        if widgets:
            ctypes.windll.user32.SetForegroundWindow(int(widgets[0].winId()))
        else:
            # Fallback: create a tiny hidden window just for focus
            dummy = QWidget()
            dummy.setWindowFlags(
                Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
            )
            dummy.setGeometry(-100, -100, 1, 1)
            dummy.show()
            ctypes.windll.user32.SetForegroundWindow(int(dummy.winId()))
            dummy.hide()
    except Exception:
        pass


# ── Popup widget ───────────────────────────────────────────


class TrayPopupWidget(QWidget):
    """Lightweight popup card that appears on left-click of the tray icon."""

    drink_requested = Signal(int)
    pause_requested = Signal(int)
    settings_requested = Signal()

    def __init__(
        self,
        config: AppConfig,
        hydration_module: HydrationModule | None,
        scheduler: Scheduler | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._hydration_module = hydration_module
        self._scheduler = scheduler

        self._setup_ui()
        self._start_refresh_timer()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(280, 350)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # ── Header ──
        header = QHBoxLayout()
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color: #4ECDC4; font-size: 14px;")
        header.addWidget(status_dot)
        self._greeting = QLabel("Screen Reminder")
        self._greeting.setStyleSheet(
            "color: #FFFFFF; font-size: 15px; font-weight: bold;"
        )
        header.addWidget(self._greeting)
        header.addStretch()
        layout.addLayout(header)

        # ── Status lines ──
        self._eye_time = QLabel("👁 下次护眼：计算中...")
        self._eye_time.setStyleSheet("color: #CCCCCC; font-size: 13px;")
        layout.addWidget(self._eye_time)

        self._sed_time = QLabel("🚶 下次站立：计算中...")
        self._sed_time.setStyleSheet("color: #CCCCCC; font-size: 13px;")
        layout.addWidget(self._sed_time)

        self._water_progress = QLabel("💧 饮水：-- / 2000ml")
        self._water_progress.setStyleSheet("color: #CCCCCC; font-size: 13px;")
        layout.addWidget(self._water_progress)

        layout.addSpacing(4)

        # ── Quick buttons ──
        btn_style = """
            QPushButton {
                background: rgba(78, 205, 196, 0.15);
                color: #4ECDC4;
                border: 1px solid rgba(78, 205, 196, 0.3);
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.25);
            }
        """

        # Pause row 1: 30min | 1h
        pause_row1 = QHBoxLayout()
        btn = QPushButton("⏸ 暂停 30min")
        btn.setStyleSheet(btn_style)
        btn.clicked.connect(lambda: self.pause_requested.emit(30))
        pause_row1.addWidget(btn)
        btn = QPushButton("⏸ 暂停 1h")
        btn.setStyleSheet(btn_style)
        btn.clicked.connect(lambda: self.pause_requested.emit(60))
        pause_row1.addWidget(btn)
        layout.addLayout(pause_row1)

        # Pause row 2: 2h | drink 100ml
        pause_row2 = QHBoxLayout()
        btn = QPushButton("⏸ 暂停 2h")
        btn.setStyleSheet(btn_style)
        btn.clicked.connect(lambda: self.pause_requested.emit(120))
        pause_row2.addWidget(btn)
        btn = QPushButton("💧 喝了 100ml")
        btn.setStyleSheet(btn_style)
        btn.clicked.connect(lambda: self.drink_requested.emit(100))
        pause_row2.addWidget(btn)
        layout.addLayout(pause_row2)

        # Drink row: 200ml | 300ml
        drink_row = QHBoxLayout()
        btn = QPushButton("💧 喝了 200ml")
        btn.setStyleSheet(btn_style)
        btn.clicked.connect(lambda: self.drink_requested.emit(200))
        drink_row.addWidget(btn)
        btn = QPushButton("💧 喝了 300ml")
        btn.setStyleSheet(btn_style)
        btn.clicked.connect(lambda: self.drink_requested.emit(300))
        drink_row.addWidget(btn)
        layout.addLayout(drink_row)

        layout.addStretch()

    def _start_refresh_timer(self) -> None:
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_status)
        self._refresh_timer.start(1000)

    # ── Public ─────────────────────────────────────────

    def show_at(self, global_pos: QPoint) -> None:
        x = global_pos.x() - self.width() + 10
        y = global_pos.y() - self.height() - 10
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            if x < sg.x():
                x = sg.x()
            if y < sg.y():
                y = sg.y()
        self.move(x, y)
        self._refresh_status()
        self.show()
        self.raise_()

    def _refresh_status(self) -> None:
        if self._scheduler:
            eye_rem = self._scheduler.get_remaining_seconds("eye_care")
            if eye_rem is not None and eye_rem > 0:
                m, s = int(eye_rem // 60), int(eye_rem % 60)
                self._eye_time.setText(f"👁 下次护眼：{_format_time(m, s)}")
            else:
                self._eye_time.setText("👁 护眼中...")

            sed_rem = self._scheduler.get_remaining_seconds("sedentary")
            if sed_rem is not None and sed_rem > 0:
                m, s = int(sed_rem // 60), int(sed_rem % 60)
                self._sed_time.setText(f"🚶 下次站立：{_format_time(m, s)}")
            else:
                self._sed_time.setText("🚶 站立中...")

        if self._hydration_module:
            ml = self._hydration_module.today_ml
            goal = self._hydration_module.daily_goal_ml
            pct = int(self._hydration_module.progress_ratio * 100)
            self._water_progress.setText(f"💧 饮水：{ml} / {goal}ml ({pct}%)")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 14, 14)
        painter.fillPath(path, QColor(28, 28, 36, 240))
        painter.setPen(QColor(60, 60, 72, 180))
        painter.drawPath(path)


# ── Tray Manager ────────────────────────────────────────────


class TrayManager(QObject):
    """Manages the system tray icon, context menu, and popup widget."""

    quit_requested = Signal()
    settings_requested = Signal()
    drink_requested = Signal(int)

    def __init__(
        self,
        config: AppConfig,
        hydration_module: HydrationModule,
        scheduler: Scheduler,
    ) -> None:
        super().__init__()
        self._config = config
        self._scheduler = scheduler
        self._hydration_module = hydration_module

        self._tray = QSystemTrayIcon()
        self._tray.setIcon(_load_tray_icon())
        self._tray.setToolTip("Screen Reminder")
        self._tray.setVisible(True)

        # Popup widget (left-click)
        self._popup = TrayPopupWidget(config, hydration_module, scheduler)
        self._popup.drink_requested.connect(self._on_popup_drink)
        self._popup.pause_requested.connect(self._on_popup_pause)
        self._popup.settings_requested.connect(self.settings_requested.emit)

        # Build context menu — NO submenus, flat list for Windows compat
        self._menu = self._build_menu()

        # Do NOT use setContextMenu — we pop it manually on right-click
        # setContextMenu + addMenu(submenu) is broken on Windows tray

        self._tray.activated.connect(self._on_tray_activated)

    # ── Menu builder (flat, no submenus) ───────────────

    def _build_menu(self) -> QMenu:
        m = QMenu()

        items = [
            ("⏸ 暂停 30 分钟", lambda: self._on_pause(30)),
            ("⏸ 暂停 1 小时",  lambda: self._on_pause(60)),
            ("🚫 今天禁用",     lambda: self._on_disable_today()),
            ("⏸ 暂停到明天",   lambda: self._on_pause_until_tomorrow()),
        ]
        for label, callback in items:
            act = QAction(label, m)
            act.triggered.connect(callback)
            m.addAction(act)

        m.addSeparator()

        items2 = [
            ("💧 记录喝水 (200ml)", lambda: self.drink_requested.emit(200)),
            ("⚙ 设置",              lambda: self.settings_requested.emit()),
        ]
        for label, callback in items2:
            act = QAction(label, m)
            act.triggered.connect(callback)
            m.addAction(act)

        m.addSeparator()

        act = QAction("❌ 退出程序", m)
        act.triggered.connect(self.quit_requested.emit)
        m.addAction(act)

        return m

    # ── Signal handlers ────────────────────────────────

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Context:
            _win_foreground_hack()
            self._menu.popup(QCursor.pos())
        elif reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self._popup and self._popup.isVisible():
                self._popup.hide()
            elif self._popup:
                geo = self._tray.geometry()
                center = geo.center()
                self._popup.show_at(center)

    def _on_pause(self, minutes: int) -> None:
        self._scheduler.pause(minutes)
        self._tray.showMessage(
            "Screen Reminder",
            f"已暂停 {minutes} 分钟",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def _on_pause_until_tomorrow(self) -> None:
        self._scheduler.pause(24 * 60)
        self._tray.showMessage(
            "Screen Reminder",
            "已暂停到明天",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def _on_disable_today(self) -> None:
        """Pause all reminders until midnight (start of tomorrow)."""
        import datetime as _dt
        now = _dt.datetime.now()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + _dt.timedelta(days=1)
        minutes = max(1, int((tomorrow - now).total_seconds() / 60) + 1)
        self._scheduler.pause(minutes)
        self._tray.showMessage(
            "Screen Reminder",
            "今天已禁用提醒",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def _on_popup_drink(self, amount: int) -> None:
        self._hydration_module.record_drink(amount)

    def _on_popup_pause(self, minutes: int) -> None:
        self._on_pause(minutes)

    # ── Public ─────────────────────────────────────────

    def set_status_color(self, _color: str = "") -> None:
        self._tray.setIcon(_load_tray_icon())

    def show_message(self, title: str, msg: str) -> None:
        self._tray.showMessage(
            title, msg, QSystemTrayIcon.MessageIcon.Information, 5000
        )

    def stop(self) -> None:
        self._tray.hide()
        if self._popup:
            self._popup.hide()
