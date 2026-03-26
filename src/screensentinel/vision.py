from __future__ import annotations

import json
import os
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
                "Moondream is not installed. Install with: pip install -e '.[vision]'"
            ) from exc

        # moondream>=1.1.0 exposes a vl(...) factory.
        if hasattr(md, "vl"):
            mode = os.getenv("MOONDREAM_MODE", "local").strip().lower()
            if mode == "cloud":
                return md.vl(api_key=os.getenv("MOONDREAM_API_KEY"))
            if mode == "endpoint":
                endpoint = os.getenv("MOONDREAM_ENDPOINT", "http://localhost:2020/v1")
                return md.vl(endpoint=endpoint, api_key=os.getenv("MOONDREAM_API_KEY"))
            # Default local path (requires local backend/model setup).
            return md.vl(local=True)

        raise RuntimeError("Unable to initialize moondream model from installed package.")

    def analyze(self, image_path: Path, goal: str) -> VisionResult:
        prompt = (
            "You are a strict focus accountability assistant. "
            "Given the user goal and screenshot, decide if the user is currently on-task. "
            "Respond ONLY JSON with keys: on_task (bool), confidence (0..1), reason (short string). "
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
        if hasattr(model, "query"):
            try:
                from PIL import Image
            except ImportError as exc:
                raise RuntimeError(
                    "Pillow is required for moondream image loading. "
                    "Install with: pip install -e '.[vision]'"
                ) from exc

            with Image.open(image_path) as image:
                result = model.query(image=image, question=prompt)
            return str(result.get("answer", result))

        raise RuntimeError("Moondream model object has no supported inference method.")

    def _parse_response(self, raw: str) -> VisionResult | None:
        text = raw.strip()
        lowered = text.lower()

        # Preferred path: strict JSON response.
        try:
            payload = json.loads(text)
            on_task = bool(payload["on_task"])
            confidence = max(0.0, min(1.0, float(payload.get("confidence", 0.55))))
            reason = str(payload.get("reason", "Focus drift suspected"))[:160]
            return VisionResult(on_task=on_task, confidence=confidence, reason=reason)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

        on_task = None
        if "on_task=true" in lowered or "on task: true" in lowered:
            on_task = True
        elif "on_task=false" in lowered or "on task: false" in lowered:
            on_task = False
        elif "off-task" in lowered or "off task" in lowered:
            on_task = False
        elif "on-task" in lowered or "on task" in lowered:
            on_task = True

        confidence = 0.55
        marker = "confidence="
        if marker in lowered:
            snippet = lowered.split(marker, 1)[1].split(";", 1)[0].strip()
            try:
                confidence = max(0.0, min(1.0, float(snippet)))
            except ValueError:
                pass

        reason = "Focus drift suspected"
        reason_marker = "reason="
        if reason_marker in lowered:
            reason = lowered.split(reason_marker, 1)[1].strip()[:160]

        if on_task is None:
            return None

        return VisionResult(on_task=on_task, confidence=confidence, reason=reason)
