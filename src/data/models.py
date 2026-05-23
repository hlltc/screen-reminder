"""SQLAlchemy ORM models for the Screen Reminder database."""

from __future__ import annotations

import datetime as _dt

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# ── Rest / break events ────────────────────────────────

class RestEvent(Base):
    __tablename__ = "rest_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(32), nullable=False)   # eye_care | sedentary | hydration | stretch
    action = Column(String(32), nullable=False)        # reminded | completed | skipped | dismissed
    created_at = Column(DateTime, default=_dt.datetime.now)

    def __repr__(self) -> str:
        return f"<RestEvent {self.event_type}:{self.action} @ {self.created_at}>"


# ── Hydration log ──────────────────────────────────────

class HydrationLog(Base):
    __tablename__ = "hydration_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount_ml = Column(Integer, default=200)
    created_at = Column(DateTime, default=_dt.datetime.now)

    def __repr__(self) -> str:
        return f"<HydrationLog {self.amount_ml}ml @ {self.created_at}>"


# ── Daily summary (aggregated for dashboard) ───────────

class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True)       # day-only
    total_eye_breaks = Column(Integer, default=0)
    total_eye_completed = Column(Integer, default=0)
    total_sedentary_breaks = Column(Integer, default=0)
    total_sedentary_completed = Column(Integer, default=0)
    total_hydration_reminders = Column(Integer, default=0)
    total_hydration_ml = Column(Integer, default=0)
    total_idle_minutes = Column(Integer, default=0)
    health_score = Column(Integer, default=0)                  # 0-100
    updated_at = Column(DateTime, default=_dt.datetime.now, onupdate=_dt.datetime.now)

    def __repr__(self) -> str:
        return f"<DailySummary {self.date.date()}>"


# ── Pain log (for later Phase 3) ────────────────────────

class PainLog(Base):
    __tablename__ = "pain_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    body_part = Column(String(32), nullable=False)    # neck | back | eyes | wrist
    pain_level = Column(Integer, default=0)            # 0-10
    note = Column(Text, default="")
    created_at = Column(DateTime, default=_dt.datetime.now)

    def __repr__(self) -> str:
        return f"<PainLog {self.body_part}:{self.pain_level} @ {self.created_at}>"
