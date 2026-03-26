from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console

from .capture import ScreenCapture
from .db import Storage
from .drift import should_notify_drift
from .notify import send_drift_notification
from .types import SessionConfig, SessionSummary, VisionResult
from .vision import VisionEngine


def _score_line(focus_pct: float) -> str:
    if focus_pct >= 85.0:
        return "Locked in. Keep this intensity."
    if focus_pct >= 60.0:
        return "Mixed focus. You worked, but drift cost real time."
    return "Brutal truth: focus collapsed. Reduce distractions and restart tighter."


def run_session(config: SessionConfig, console: Console) -> SessionSummary:
    return run_session_with(
        config=config,
        console=console,
        storage=Storage(config.db_path),
        capture=ScreenCapture(),
        vision=VisionEngine(),
        now_fn=datetime.now,
        sleep_fn=time.sleep,
        notify_fn=send_drift_notification,
    )


def run_session_with(
    config: SessionConfig,
    console: Console,
    storage: Storage,
    capture: ScreenCapture,
    vision: VisionEngine,
    now_fn: Callable[[], datetime],
    sleep_fn: Callable[[float], None],
    notify_fn: Callable[[str, str], None],
) -> SessionSummary:
    started_at = now_fn()
    end_at = started_at + timedelta(minutes=config.duration_min)

    session_id = storage.start_session(
        goal=config.goal,
        started_at=started_at,
        duration_min=config.duration_min,
        interval_sec=config.interval_sec,
        strictness=config.strictness,
    )

    console.print(f"[bold cyan]Session started:[/bold cyan] {config.goal}")
    console.print(
        f"Duration {config.duration_min}m, check interval {config.interval_sec}s, strictness {config.strictness}"
    )

    try:
        while now_fn() < end_at:
            timestamp = now_fn()
            capture_name = timestamp.strftime("%Y%m%d_%H%M%S") + ".png"
            image_path = Path("data/captures") / capture_name

            try:
                capture.capture_primary(image_path)
                result = vision.analyze(image_path=image_path, goal=config.goal)
            except Exception as exc:  # noqa: BLE001
                result = VisionResult(
                    on_task=False,
                    confidence=0.55,
                    reason=f"Inference failed: {exc}",
                )

            stored_image = str(image_path) if config.debug_save_captures else None
            if not config.debug_save_captures and image_path.exists():
                image_path.unlink(missing_ok=True)

            check_id = storage.log_check(
                session_id=session_id,
                timestamp=timestamp,
                result=result,
                image_path=stored_image,
            )

            status_word = "ON TASK" if result.on_task else "OFF TASK"
            console.print(
                f"[{timestamp.strftime('%H:%M:%S')}] {status_word} ({result.confidence:.2f}) - {result.reason}"
            )

            if should_notify_drift(result=result, strictness=config.strictness):
                notify_fn(config.goal, result.reason)
                storage.log_drift(
                    session_id=session_id,
                    check_id=check_id,
                    timestamp=timestamp,
                    reason=result.reason,
                )

            sleep_seconds = max(0.0, config.interval_sec - (now_fn() - timestamp).total_seconds())
            if sleep_seconds > 0:
                sleep_fn(sleep_seconds)
    except KeyboardInterrupt:
        console.print("[yellow]Session interrupted by user.[/yellow]")

    ended_at = now_fn()
    storage.finish_session(session_id, ended_at)
    total_checks, on_task_checks, drift_count = storage.session_counts(session_id)

    focus_pct = (on_task_checks / total_checks * 100.0) if total_checks else 0.0
    console.print("\n[bold]Session report[/bold]")
    console.print(f"Checks: {total_checks}")
    console.print(f"On-task: {on_task_checks}")
    console.print(f"Drift events: {drift_count}")
    console.print(f"Focus score: {focus_pct:.1f}%")

    for reason, count in storage.top_drift_reasons(session_id):
        console.print(f"- {reason}: {count}")

    console.print(f"[bold]{_score_line(focus_pct)}[/bold]")

    return SessionSummary(
        session_id=session_id,
        goal=config.goal,
        started_at=started_at,
        ended_at=ended_at,
        total_checks=total_checks,
        on_task_checks=on_task_checks,
        drift_count=drift_count,
    )
