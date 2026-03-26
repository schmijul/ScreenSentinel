from __future__ import annotations

import unittest

from screensentinel.drift import should_notify_drift
from screensentinel.types import VisionResult


class TestDrift(unittest.TestCase):
    def test_off_task_at_threshold_notifies(self) -> None:
        result = VisionResult(on_task=False, confidence=0.60, reason="social media")
        self.assertTrue(should_notify_drift(result, "normal"))

    def test_on_task_never_notifies(self) -> None:
        result = VisionResult(on_task=True, confidence=0.99, reason="coding")
        self.assertFalse(should_notify_drift(result, "strict"))

    def test_lenient_requires_higher_confidence(self) -> None:
        result = VisionResult(on_task=False, confidence=0.70, reason="news")
        self.assertFalse(should_notify_drift(result, "lenient"))


if __name__ == "__main__":
    unittest.main()
