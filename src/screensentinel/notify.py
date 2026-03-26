from __future__ import annotations

from plyer import notification


def send_drift_notification(goal: str, reason: str) -> None:
    notification.notify(
        title="ScreenSentinel: Off-task detected",
        message=f"{reason}\\nGoal: {goal}",
        app_name="ScreenSentinel",
        timeout=7,
    )
