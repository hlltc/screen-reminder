"""Application configuration management using pydantic-settings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.constants import (
    DEFAULT_LUNCH_END_H,
    DEFAULT_LUNCH_START_H,
    DEFAULT_WORK_DAYS,
    DEFAULT_WORK_END_H,
    DEFAULT_WORK_START_H,
    EYE_CARE_INTERVAL_MIN,
    EYE_CARE_REST_SECONDS,
    HYDRATION_DAILY_ML,
    HYDRATION_INTERVAL_MIN,
    HYDRATION_SINGLE_ML,
    IDLE_THRESHOLD_SECONDS,
    OVERLAY_OPACITY,
    SEDENTARY_INTERVAL_MIN,
    SEDENTARY_LOCK_SECONDS,
)


class ReminderConfig(BaseSettings):
    """Per-module reminder configuration."""

    enabled: bool = True
    interval_minutes: int = 20
    reminder_strength: str = "gentle"  # gentle | moderate | strict


class AppConfig(BaseSettings):
    """Application configuration backed by a JSON file."""

    model_config = SettingsConfigDict(arbitrary_types_allowed=True)

    # ── Work schedule ─────────────────────────────────
    work_start_h: int = Field(default=DEFAULT_WORK_START_H, ge=0, le=23)
    work_end_h: int = Field(default=DEFAULT_WORK_END_H, ge=0, le=23)
    lunch_start_h: int = Field(default=DEFAULT_LUNCH_START_H, ge=0, le=23)
    lunch_end_h: int = Field(default=DEFAULT_LUNCH_END_H, ge=0, le=23)
    work_days: set[int] = Field(default_factory=lambda: DEFAULT_WORK_DAYS.copy())

    # ── Eye care ──────────────────────────────────────
    eye_care_enabled: bool = True
    eye_care_interval_min: int = EYE_CARE_INTERVAL_MIN
    eye_care_rest_seconds: int = EYE_CARE_REST_SECONDS
    eye_care_strength: str = "gentle"  # gentle | moderate | strict

    # ── Sedentary / spine ─────────────────────────────
    sedentary_enabled: bool = True
    sedentary_interval_min: int = SEDENTARY_INTERVAL_MIN
    sedentary_lock_seconds: int = SEDENTARY_LOCK_SECONDS
    sedentary_strength: str = "gentle"

    # ── Hydration ─────────────────────────────────────
    hydration_enabled: bool = True
    hydration_interval_min: int = HYDRATION_INTERVAL_MIN
    hydration_single_ml: int = HYDRATION_SINGLE_ML
    hydration_daily_ml: int = HYDRATION_DAILY_ML

    # ── Idle ──────────────────────────────────────────
    idle_threshold_seconds: int = IDLE_THRESHOLD_SECONDS

    # ── Overlay ───────────────────────────────────────
    overlay_opacity: float = Field(default=OVERLAY_OPACITY, ge=0.1, le=1.0)

    # ── Misc ──────────────────────────────────────────
    language: str = "zh"
    theme: str = "system"  # system | light | dark
    launch_at_startup: bool = True
    tray_show_progress_ring: bool = True

    _config_path: Path | None = None

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        """Load config from a JSON file, creating defaults if absent."""
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if "work_days" in data:
                data["work_days"] = set(data["work_days"])
        else:
            data = {}
        cfg = cls(**data)
        cfg._config_path = path
        return cfg

    def save(self) -> None:
        """Persist configuration to the JSON file."""
        if self._config_path is None:
            return
        d = self.model_dump()
        d["work_days"] = list(d["work_days"])
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @property
    def config_dir(self) -> Path:
        return self._config_path.parent if self._config_path else Path(".")

    @property
    def db_path(self) -> Path:
        from src.utils.constants import DB_FILENAME
        return self.config_dir / DB_FILENAME

    # ── Helpers ───────────────────────────────────────

    def is_work_time(self, dt: "datetime.datetime") -> bool:  # noqa: F821
        """Check if a given datetime falls within configured work hours."""
        import datetime as _dt
        if dt.weekday() not in self.work_days:
            return False
        t = dt.time()
        if t < _dt.time(self.work_start_h, 0):
            return False
        if t >= _dt.time(self.work_end_h, 0):
            return False
        return True

    def is_lunch_time(self, dt: "datetime.datetime") -> bool:  # noqa: F821
        """Check if a given datetime falls within configured lunch break."""
        import datetime as _dt
        lunch_start = _dt.time(self.lunch_start_h, 0)
        lunch_end = _dt.time(self.lunch_end_h, 0)
        t = dt.time()
        return lunch_start <= t < lunch_end
