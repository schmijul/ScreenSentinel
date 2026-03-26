from __future__ import annotations

from .types import VisionResult


_THRESHOLDS = {
    "lenient": 0.75,
    "normal": 0.60,
    "strict": 0.45,
}


def should_notify_drift(result: VisionResult, strictness: str) -> bool:
    threshold = _THRESHOLDS.get(strictness, _THRESHOLDS["normal"])
    return (not result.on_task) and result.confidence >= threshold
