from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console

from screensentinel.db import Storage
from screensentinel.session import _score_line, run_session_with
from screensentinel.types import SessionConfig, VisionResult


class _FakeCapture:
    def capture_primary(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake")
        return output_path


class _FakeVision:
    def __init__(self, results: list[VisionResult]) -> None:
        self._results = results
        self._index = 0

    def analyze(self, image_path: Path, goal: str) -> VisionResult:
        if self._index >= len(self._results):
            return self._results[-1]
        value = self._results[self._index]
        self._index += 1
        return value


class _FakeClock:
    def __init__(self, start: datetime) -> None:
        self.current = start

    def now(self) -> datetime:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.current += timedelta(seconds=seconds)


class TestSessionLoop(unittest.TestCase):
    def test_score_line_when_no_checks(self) -> None:
        line = _score_line(0.0, 0)
        self.assertIn("No checks collected", line)

    def test_logs_checks_and_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = SessionConfig(
                goal="Build ScreenSentinel",
                duration_min=1,
                interval_sec=30,
                strictness="normal",
                debug_save_captures=False,
                db_path=str(Path(tmp) / "sentinel.db"),
            )
            storage = Storage(config.db_path)
            capture = _FakeCapture()
            vision = _FakeVision(
                [
                    VisionResult(on_task=True, confidence=0.9, reason="coding"),
                    VisionResult(on_task=False, confidence=0.8, reason="news feed"),
                ]
            )
            clock = _FakeClock(datetime(2026, 1, 1, 12, 0, 0))
            notifications: list[tuple[str, str]] = []

            summary = run_session_with(
                config=config,
                console=Console(record=True),
                storage=storage,
                capture=capture,
                vision=vision,
                now_fn=clock.now,
                sleep_fn=clock.sleep,
                notify_fn=lambda goal, reason: notifications.append((goal, reason)),
            )

            self.assertEqual(summary.total_checks, 2)
            self.assertEqual(summary.on_task_checks, 1)
            self.assertEqual(summary.drift_count, 1)
            self.assertEqual(len(notifications), 1)
            self.assertEqual(notifications[0][1], "news feed")


if __name__ == "__main__":
    unittest.main()
