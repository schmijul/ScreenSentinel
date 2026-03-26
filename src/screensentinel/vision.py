from __future__ import annotations

from pathlib import Path

from .types import VisionResult


class VisionEngine:
    def __init__(self) -> None:
        self._model = self._load_model()

    def _load_model(self):
        try:
            import moondream as md  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Moondream is not installed. Install dependencies and retry."
            ) from exc

        candidates = ("model", "create_model", "load")
        for name in candidates:
            fn = getattr(md, name, None)
            if callable(fn):
                return fn()

        if hasattr(md, "Moondream"):
            return md.Moondream()

        raise RuntimeError("Unable to initialize moondream model from installed package.")

    def analyze(self, image_path: Path, goal: str) -> VisionResult:
        prompt = (
            "You are a strict focus accountability assistant. "
            "Given the user goal and screenshot, decide if the user is currently on-task. "
            "Respond in a terse form: on_task=<true|false>; confidence=<0.0-1.0>; reason=<short phrase>. "
            f"Goal: {goal}"
        )

        raw = self._run_inference(prompt=prompt, image_path=image_path)
        parsed = self._parse_response(raw)
        if parsed is not None:
            return parsed

        # Conservative fallback: unclear model output is treated as likely off-task.
        return VisionResult(
            on_task=False,
            confidence=0.55,
            reason="Unclear analysis output",
        )

    def _run_inference(self, prompt: str, image_path: Path) -> str:
        model = self._model
        image_str = str(image_path)

        if hasattr(model, "query"):
            result = model.query(image=image_str, question=prompt)
            return str(result)

        if hasattr(model, "caption"):
            result = model.caption(image_str)
            return str(result)

        if hasattr(model, "__call__"):
            result = model(prompt=prompt, image=image_str)
            return str(result)

        raise RuntimeError("Moondream model object has no supported inference method.")

    def _parse_response(self, raw: str) -> VisionResult | None:
        text = raw.strip().lower()

        on_task = None
        if "on_task=true" in text or "on task: true" in text:
            on_task = True
        elif "on_task=false" in text or "on task: false" in text:
            on_task = False
        elif "off-task" in text or "off task" in text:
            on_task = False
        elif "on-task" in text or "on task" in text:
            on_task = True

        confidence = 0.55
        marker = "confidence="
        if marker in text:
            snippet = text.split(marker, 1)[1].split(";", 1)[0].strip()
            try:
                confidence = max(0.0, min(1.0, float(snippet)))
            except ValueError:
                pass

        reason = "Focus drift suspected"
        reason_marker = "reason="
        if reason_marker in text:
            reason = text.split(reason_marker, 1)[1].strip()[:160]

        if on_task is None:
            return None

        return VisionResult(on_task=on_task, confidence=confidence, reason=reason)
