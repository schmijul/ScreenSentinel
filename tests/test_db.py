from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from screensentinel.db import Storage
from screensentinel.types import VisionResult


class TestStorage(unittest.TestCase):
    def test_session_check_and_drift_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "sentinel.db"
            storage = Storage(str(db_path))

            started = datetime.now()
            session_id = storage.start_session(
                goal="Build feature",
                started_at=started,
                duration_min=30,
                interval_sec=30,
                strictness="normal",
            )

            check_id = storage.log_check(
                session_id=session_id,
                timestamp=started,
                result=VisionResult(False, 0.8, "off task"),
                image_path=None,
            )
            storage.log_drift(
                session_id=session_id,
                check_id=check_id,
                timestamp=started,
                reason="off task",
            )
            storage.finish_session(session_id, datetime.now())

            total, on_task, drift_count = storage.session_counts(session_id)
            self.assertEqual(total, 1)
            self.assertEqual(on_task, 0)
            self.assertEqual(drift_count, 1)


if __name__ == "__main__":
    unittest.main()
