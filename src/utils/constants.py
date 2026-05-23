"""Application-wide constants."""

APP_NAME = "Screen Reminder"
APP_VERSION = "0.1.0"
APP_AUTHOR = "Screen Reminder Team"

# ── Timing defaults ──────────────────────────────────
EYE_CARE_INTERVAL_MIN = 20       # 20-20-20 rule: every 20 minutes
EYE_CARE_REST_SECONDS = 20       # look 20 feet away for 20 seconds

SEDENTARY_INTERVAL_MIN = 55      # stand up every 55 minutes
SEDENTARY_LOCK_SECONDS = 180     # lock/overlay for 3 minutes

HYDRATION_INTERVAL_MIN = 45      # drink water every 45 minutes
HYDRATION_SINGLE_ML = 200        # default single drink amount
HYDRATION_DAILY_ML = 2000        # daily water goal

# ── Scheduler ────────────────────────────────────────
DEFAULT_WORK_START_H = 9
DEFAULT_WORK_END_H = 18
DEFAULT_LUNCH_START_H = 12
DEFAULT_LUNCH_END_H = 13
DEFAULT_WORK_DAYS = {0, 1, 2, 3, 4}  # Mon-Fri

# ── Idle detection ───────────────────────────────────
IDLE_THRESHOLD_SECONDS = 120       # consider user away after 2 min idle
IDLE_POLL_INTERVAL_SECONDS = 5     # check idle state every 5s

# ── Overlay ──────────────────────────────────────────
OVERLAY_OPACITY = 0.85
OVERLAY_WARNING_TIMEOUT_SECONDS = 15  # time before overlay appears after soft reminder

# ── Gamification ─────────────────────────────────────
STREAK_WEEKLY_REST_DAY = None      # 0=Mon ... 6=Sun, None = no rest day

# ── DB ───────────────────────────────────────────────
DB_FILENAME = "screen_reminder.db"
