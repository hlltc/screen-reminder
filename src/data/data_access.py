"""Simple data access layer for writing/reading from the DB."""

from __future__ import annotations

import datetime as _dt

from src.data.database import get_session
from src.data.models import DailySummary, HydrationLog, RestEvent


def log_event(event_type: str, action: str) -> None:
    session = get_session()
    try:
        session.add(RestEvent(event_type=event_type, action=action))
        session.commit()
    finally:
        session.close()


def log_hydration(amount_ml: int) -> None:
    session = get_session()
    try:
        session.add(HydrationLog(amount_ml=amount_ml))
        session.commit()
    finally:
        session.close()


def get_today_event_count(event_type: str, action: str | None = None) -> int:
    """Count RestEvent rows for today, optionally filtered by action."""
    session = get_session()
    try:
        today = _dt.date.today()
        q = session.query(RestEvent).filter(
            RestEvent.created_at >= today,
            RestEvent.event_type == event_type,
        )
        if action:
            q = q.filter(RestEvent.action == action)
        return q.count()
    finally:
        session.close()


def get_today_hydration_ml() -> int:
    session = get_session()
    try:
        today = _dt.date.today()
        total = (
            session.query(HydrationLog)
            .filter(HydrationLog.created_at >= today)
            .with_entities(HydrationLog.amount_ml)
            .all()
        )
        return sum(row[0] for row in total)
    finally:
        session.close()
