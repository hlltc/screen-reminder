"""Fullscreen rest overlay window.

Displays a semi-transparent overlay with a countdown timer and gentle rest prompts.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.utils.config import AppConfig


class CountdownOverlay(QWidget):
    """A fullscreen, semi-transparent overlay that counts down rest time."""

    finished = Signal()
    skipped = Signal()

    def __init__(self, config: AppConfig, title: str = "", subtitle: str = "") -> None:
        super().__init__()
        self._config = config
        self._title = title
        self._subtitle = subtitle
        self._remaining: int = 0
        self._paused = False

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        screen = self.screen()
        if screen:
            self.setGeometry(screen.geometry())

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(80, 80, 80, 80)
        layout.setSpacing(28)

        # Title
        self._title_label = QLabel()
        self._title_label.setText(self._title)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet(
            "color: #FFFFFF; font-size: 64px; font-weight: bold;"
        )
        layout.addWidget(self._title_label)

        # Subtitle
        self._subtitle_label = QLabel()
        self._subtitle_label.setText(self._subtitle)
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle_label.setStyleSheet(
            "color: #CCCCCC; font-size: 30px;"
        )
        layout.addWidget(self._subtitle_label)

        # Countdown
        self._countdown_label = QLabel()
        self._countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._countdown_label.setStyleSheet(
            "color: #4ECDC4; font-size: 128px; font-weight: bold;"
        )
        layout.addWidget(self._countdown_label)

        layout.addSpacing(50)

        # Skip button
        self._skip_btn = QPushButton("按 Esc 跳过")
        self._skip_btn.setFixedSize(260, 58)
        self._skip_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255,255,255,0.12);
                color: #AAAAAA;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 10px;
                font-size: 20px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.22);
                color: #FFFFFF;
            }
            """
        )
        self._skip_btn.clicked.connect(self._on_skip)
        layout.addWidget(self._skip_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _setup_timer(self) -> None:
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(1000)

    # ── Public API ─────────────────────────────────────

    def start_countdown(self, seconds: int, title: str = "", subtitle: str = "") -> None:
        if title:
            self._title = title
            self._title_label.setText(title)
        if subtitle:
            self._subtitle = subtitle
            self._subtitle_label.setText(subtitle)
        self._remaining = seconds
        self._paused = False
        self._update_countdown_label()
        self._timer.start()
        self.showFullScreen()

    def hide_overlay(self) -> None:
        self._timer.stop()
        self.hide()

    # ── Internals ──────────────────────────────────────

    def _tick(self) -> None:
        if self._paused:
            return
        if self._remaining > 0:
            self._remaining -= 1
            self._update_countdown_label()
        if self._remaining <= 0:
            self._timer.stop()
            self.hide()
            self.finished.emit()

    def _update_countdown_label(self) -> None:
        m = self._remaining // 60
        s = self._remaining % 60
        self._countdown_label.setText(f"{m:02d}:{s:02d}")

    def _on_skip(self) -> None:
        self._timer.stop()
        self.hide()
        self.skipped.emit()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        opacity = int(self._config.overlay_opacity * 255)
        bg = QColor(18, 18, 22, opacity)
        painter.fillRect(self.rect(), bg)

        super().paintEvent(event)

    def keyPressEvent(self, event) -> None:
        # Allow Escape to skip
        if event.key() == Qt.Key.Key_Escape:
            self._on_skip()
        else:
            super().keyPressEvent(event)


# ────────────────────────────────────────────────────────
# Quick drink overlay — small centered card, no countdown
# ────────────────────────────────────────────────────────

class QuickDrinkOverlay(QWidget):
    """A small centered overlay prompting the user to drink, with drink/skip buttons."""

    drunk = Signal(int)
    skipped = Signal()

    _CARD_W, _CARD_H = 480, 260

    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        screen = self.screen()
        if screen:
            sg = screen.geometry()
            self.setGeometry(sg)

        self._setup_ui()
        self._setup_auto_dismiss()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # The visible card: we draw in paintEvent, children float on top
        inner = QWidget()
        inner.setFixedSize(self._CARD_W, self._CARD_H)
        inner.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        vbox = QVBoxLayout(inner)
        vbox.setContentsMargins(40, 28, 40, 28)
        vbox.setSpacing(14)

        title = QLabel("该喝水了！")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; font-size: 36px; font-weight: bold;")
        vbox.addWidget(title)

        sub = QLabel("建议喝 200ml，保持水分充足")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #CCCCCC; font-size: 18px;")
        vbox.addWidget(sub)

        vbox.addSpacing(20)

        # Buttons
        from PySide6.QtWidgets import QHBoxLayout
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        btn_style = """
            QPushButton {
                background: rgba(78, 205, 196, 0.20);
                color: #4ECDC4;
                border: 1px solid rgba(78, 205, 196, 0.4);
                border-radius: 10px;
                padding: 10px 28px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(78, 205, 196, 0.30);
            }
        """
        skip_style = """
            QPushButton {
                background: rgba(255,255,255,0.10);
                color: #999999;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 10px;
                padding: 10px 28px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.18);
                color: #CCCCCC;
            }
        """

        drink_btn = QPushButton("💧 喝了 200ml")
        drink_btn.setStyleSheet(btn_style)
        drink_btn.clicked.connect(lambda: self._on_drunk(200))
        btn_row.addWidget(drink_btn)

        skip_btn = QPushButton("跳过")
        skip_btn.setStyleSheet(skip_style)
        skip_btn.clicked.connect(self._on_skip)
        btn_row.addWidget(skip_btn)

        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addLayout(btn_row)

        layout.addWidget(inner, alignment=Qt.AlignmentFlag.AlignCenter)

    def _setup_auto_dismiss(self) -> None:
        from PySide6.QtCore import QTimer
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._on_skip)
        self._dismiss_timer.start(15_000)

    def _on_drunk(self, amount: int) -> None:
        self._dismiss_timer.stop()
        self.hide()
        self.drunk.emit(amount)

    def _on_skip(self) -> None:
        self._dismiss_timer.stop()
        self.hide()
        self.skipped.emit()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fullscreen dim
        opacity = int(self._config.overlay_opacity * 255)
        painter.fillRect(self.rect(), QColor(18, 18, 22, opacity))

        # Centered card
        cx = (self.width() - self._CARD_W) // 2
        cy = (self.height() - self._CARD_H) // 2
        path = QPainterPath()
        path.addRoundedRect(cx, cy, self._CARD_W, self._CARD_H, 20, 20)
        painter.fillPath(path, QColor(30, 30, 40, 220))

        super().paintEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._on_skip()
        else:
            super().keyPressEvent(event)
