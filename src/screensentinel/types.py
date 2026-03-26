from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class VisionResult:
    on_task: bool
    confidence: float
    reason: str


@dataclass(slots=True)
class SessionConfig:
    goal: str
    duration_min: int
    interval_sec: int = 30
    strictness: str = "normal"
    debug_save_captures: bool = False
    db_path: str = "data/screensentinel.db"


@dataclass(slots=True)
class SessionSummary:
    session_id: int
    goal: str
    started_at: datetime
    ended_at: datetime
    total_checks: int
    on_task_checks: int
    drift_count: int
