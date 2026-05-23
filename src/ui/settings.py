"""Settings window — tabbed configuration for all health modules."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from loguru import logger

from src.utils.config import AppConfig


class SettingsDialog(QDialog):
    """Modal settings dialog with tabs for each module."""

    config_changed = Signal()

    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Screen Reminder — 设置")
        self.setMinimumSize(460, 420)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._setup_ui()
        self._load_values()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_general_tab(), "通用")
        self._tabs.addTab(self._build_eye_tab(), "护眼")
        self._tabs.addTab(self._build_sedentary_tab(), "久坐")
        self._tabs.addTab(self._build_hydration_tab(), "补水")
        main_layout.addWidget(self._tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(
            "QPushButton { background: #4ECDC4; color: #1a1a1a; border: none; "
            "border-radius: 6px; padding: 8px 24px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background: #45b7aa; }"
        )
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(
            "QPushButton { background: #333; color: #ccc; border: none; "
            "border-radius: 6px; padding: 8px 24px; font-size: 14px; }"
            "QPushButton:hover { background: #444; }"
        )
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

    # ── General tab ────────────────────────────────────

    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        gb = QGroupBox("工作时间")
        form = QFormLayout(gb)

        self._work_start = QTimeEdit()
        self._work_start.setDisplayFormat("HH:mm")
        form.addRow("开始时间：", self._work_start)

        self._work_end = QTimeEdit()
        self._work_end.setDisplayFormat("HH:mm")
        form.addRow("结束时间：", self._work_end)

        self._lunch_start = QTimeEdit()
        self._lunch_start.setDisplayFormat("HH:mm")
        form.addRow("午休开始：", self._lunch_start)

        self._lunch_end = QTimeEdit()
        self._lunch_end.setDisplayFormat("HH:mm")
        form.addRow("午休结束：", self._lunch_end)
        layout.addWidget(gb)

        gb2 = QGroupBox("其他")
        form2 = QFormLayout(gb2)
        self._launch_at_startup = QCheckBox("开机自启")
        form2.addRow("", self._launch_at_startup)

        self._idle_threshold = QSpinBox()
        self._idle_threshold.setRange(30, 600)
        self._idle_threshold.setSuffix(" 秒")
        form2.addRow("空闲检测阈值：", self._idle_threshold)
        layout.addWidget(gb2)

        layout.addStretch()
        return w

    # ── Eye care tab ───────────────────────────────────

    def _build_eye_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        self._eye_enabled = QCheckBox("启用护眼提醒 (20-20-20)")
        layout.addWidget(self._eye_enabled)

        gb = QGroupBox()
        form = QFormLayout(gb)

        self._eye_interval = QSpinBox()
        self._eye_interval.setRange(5, 60)
        self._eye_interval.setSuffix(" 分钟")
        form.addRow("提醒间隔：", self._eye_interval)

        self._eye_rest = QSpinBox()
        self._eye_rest.setRange(10, 120)
        self._eye_rest.setSuffix(" 秒")
        form.addRow("休息时长：", self._eye_rest)

        self._eye_strength = QComboBox()
        self._eye_strength.addItems(["温和", "中等", "严格"])
        form.addRow("提醒强度：", self._eye_strength)
        layout.addWidget(gb)

        gb2 = QGroupBox("遮罩透明度")
        h = QHBoxLayout(gb2)
        self._overlay_opacity = QSlider(Qt.Orientation.Horizontal)
        self._overlay_opacity.setRange(30, 100)
        self._overlay_opacity.setTickInterval(10)
        h.addWidget(self._overlay_opacity)
        self._opacity_label = QLabel("85%")
        h.addWidget(self._opacity_label)
        self._overlay_opacity.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{v}%")
        )
        layout.addWidget(gb2)

        layout.addStretch()
        return w

    # ── Sedentary tab ──────────────────────────────────

    def _build_sedentary_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        self._sed_enabled = QCheckBox("启用久坐提醒")
        layout.addWidget(self._sed_enabled)

        gb = QGroupBox()
        form = QFormLayout(gb)

        self._sed_interval = QSpinBox()
        self._sed_interval.setRange(20, 120)
        self._sed_interval.setSuffix(" 分钟")
        form.addRow("提醒间隔：", self._sed_interval)

        self._sed_lock = QSpinBox()
        self._sed_lock.setRange(30, 600)
        self._sed_lock.setSuffix(" 秒")
        form.addRow("站立时长：", self._sed_lock)

        self._sed_strength = QComboBox()
        self._sed_strength.addItems(["温和", "中等", "严格"])
        form.addRow("提醒强度：", self._sed_strength)
        layout.addWidget(gb)

        layout.addStretch()
        return w

    # ── Hydration tab ──────────────────────────────────

    def _build_hydration_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        self._hyd_enabled = QCheckBox("启用补水提醒")
        layout.addWidget(self._hyd_enabled)

        gb = QGroupBox()
        form = QFormLayout(gb)

        self._hyd_interval = QSpinBox()
        self._hyd_interval.setRange(15, 120)
        self._hyd_interval.setSuffix(" 分钟")
        form.addRow("提醒间隔：", self._hyd_interval)

        self._hyd_single = QSpinBox()
        self._hyd_single.setRange(50, 500)
        self._hyd_single.setSingleStep(50)
        self._hyd_single.setSuffix(" ml")
        form.addRow("单次水量：", self._hyd_single)

        self._hyd_daily = QSpinBox()
        self._hyd_daily.setRange(500, 5000)
        self._hyd_daily.setSingleStep(100)
        self._hyd_daily.setSuffix(" ml")
        form.addRow("每日目标：", self._hyd_daily)
        layout.addWidget(gb)

        layout.addStretch()
        return w

    # ── Load / Save ────────────────────────────────────

    def _load_values(self) -> None:
        c = self._config
        # General
        from PySide6.QtCore import QTime
        self._work_start.setTime(QTime(c.work_start_h, 0))
        self._work_end.setTime(QTime(c.work_end_h, 0))
        self._lunch_start.setTime(QTime(c.lunch_start_h, 0))
        self._lunch_end.setTime(QTime(c.lunch_end_h, 0))
        self._launch_at_startup.setChecked(c.launch_at_startup)
        self._idle_threshold.setValue(c.idle_threshold_seconds)

        # Eye
        self._eye_enabled.setChecked(c.eye_care_enabled)
        self._eye_interval.setValue(c.eye_care_interval_min)
        self._eye_rest.setValue(c.eye_care_rest_seconds)
        idx = {"gentle": 0, "moderate": 1, "strict": 2}.get(c.eye_care_strength, 0)
        self._eye_strength.setCurrentIndex(idx)
        self._overlay_opacity.setValue(int(c.overlay_opacity * 100))
        self._opacity_label.setText(f"{int(c.overlay_opacity * 100)}%")

        # Sedentary
        self._sed_enabled.setChecked(c.sedentary_enabled)
        self._sed_interval.setValue(c.sedentary_interval_min)
        self._sed_lock.setValue(c.sedentary_lock_seconds)
        idx = {"gentle": 0, "moderate": 1, "strict": 2}.get(c.sedentary_strength, 0)
        self._sed_strength.setCurrentIndex(idx)

        # Hydration
        self._hyd_enabled.setChecked(c.hydration_enabled)
        self._hyd_interval.setValue(c.hydration_interval_min)
        self._hyd_single.setValue(c.hydration_single_ml)
        self._hyd_daily.setValue(c.hydration_daily_ml)

    def _on_save(self) -> None:
        c = self._config
        # General
        c.work_start_h = self._work_start.time().hour()
        c.work_end_h = self._work_end.time().hour()
        c.lunch_start_h = self._lunch_start.time().hour()
        c.lunch_end_h = self._lunch_end.time().hour()
        c.launch_at_startup = self._launch_at_startup.isChecked()
        c.idle_threshold_seconds = self._idle_threshold.value()

        # Eye
        c.eye_care_enabled = self._eye_enabled.isChecked()
        c.eye_care_interval_min = self._eye_interval.value()
        c.eye_care_rest_seconds = self._eye_rest.value()
        c.eye_care_strength = ["gentle", "moderate", "strict"][self._eye_strength.currentIndex()]
        c.overlay_warning_timeout_seconds = self._overlay_warning.value()
        c.overlay_opacity = self._overlay_opacity.value() / 100.0

        # Sedentary
        c.sedentary_enabled = self._sed_enabled.isChecked()
        c.sedentary_interval_min = self._sed_interval.value()
        c.sedentary_lock_seconds = self._sed_lock.value()
        c.sedentary_strength = ["gentle", "moderate", "strict"][self._sed_strength.currentIndex()]

        # Hydration
        c.hydration_enabled = self._hyd_enabled.isChecked()
        c.hydration_interval_min = self._hyd_interval.value()
        c.hydration_single_ml = self._hyd_single.value()
        c.hydration_daily_ml = self._hyd_daily.value()

        logger.info(
            "Settings saved: eye={}min/{}s sed={}min/{}s hyd={}min",
            c.eye_care_interval_min,
            c.eye_care_rest_seconds,
            c.sedentary_interval_min,
            c.sedentary_lock_seconds,
            c.hydration_interval_min,
        )
        c.save()
        self.config_changed.emit()
        self.accept()
