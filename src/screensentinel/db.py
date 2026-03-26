from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .types import VisionResult


class Storage:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        try:
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  goal TEXT NOT NULL,
                  started_at TEXT NOT NULL,
                  ended_at TEXT,
                  duration_min INTEGER NOT NULL,
                  interval_sec INTEGER NOT NULL,
                  strictness TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checks (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER NOT NULL,
                  timestamp TEXT NOT NULL,
                  on_task INTEGER NOT NULL,
                  confidence REAL NOT NULL,
                  reason TEXT NOT NULL,
                  image_path TEXT,
                  FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS drift_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER NOT NULL,
                  check_id INTEGER NOT NULL,
                  timestamp TEXT NOT NULL,
                  reason TEXT NOT NULL,
                  FOREIGN KEY(session_id) REFERENCES sessions(id),
                  FOREIGN KEY(check_id) REFERENCES checks(id)
                )
                """
            )

    def start_session(
        self,
        goal: str,
        started_at: datetime,
        duration_min: int,
        interval_sec: int,
        strictness: str,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO sessions(goal, started_at, duration_min, interval_sec, strictness)
                VALUES (?, ?, ?, ?, ?)
                """,
                (goal, started_at.isoformat(), duration_min, interval_sec, strictness),
            )
            return int(cur.lastrowid)

    def finish_session(self, session_id: int, ended_at: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET ended_at = ? WHERE id = ?",
                (ended_at.isoformat(), session_id),
            )

    def log_check(
        self,
        session_id: int,
        timestamp: datetime,
        result: VisionResult,
        image_path: str | None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO checks(session_id, timestamp, on_task, confidence, reason, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    timestamp.isoformat(),
                    int(result.on_task),
                    result.confidence,
                    result.reason,
                    image_path,
                ),
            )
            return int(cur.lastrowid)

    def log_drift(
        self,
        session_id: int,
        check_id: int,
        timestamp: datetime,
        reason: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO drift_events(session_id, check_id, timestamp, reason)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, check_id, timestamp.isoformat(), reason),
            )

    def session_counts(self, session_id: int) -> tuple[int, int, int]:
        with self._connect() as conn:
            total_checks = int(
                conn.execute(
                    "SELECT COUNT(*) FROM checks WHERE session_id = ?", (session_id,)
                ).fetchone()[0]
            )
            on_task_checks = int(
                conn.execute(
                    "SELECT COUNT(*) FROM checks WHERE session_id = ? AND on_task = 1",
                    (session_id,),
                ).fetchone()[0]
            )
            drift_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM drift_events WHERE session_id = ?", (session_id,)
                ).fetchone()[0]
            )
            return total_checks, on_task_checks, drift_count

    def top_drift_reasons(self, session_id: int, limit: int = 3) -> list[tuple[str, int]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT reason, COUNT(*) AS c
                FROM drift_events
                WHERE session_id = ?
                GROUP BY reason
                ORDER BY c DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
            return [(str(row[0]), int(row[1])) for row in rows]
