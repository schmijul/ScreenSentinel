from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from .types import VisionResult


class VisionEngine:
    def __init__(self) -> None:
        self._backend = os.getenv("SCREENSENTINEL_VISION_BACKEND", "moondream").strip().lower()
        self._model = self._load_model()

    def _load_model(self):
        if self._backend == "ollama":
            return None

        try:
            import moondream as md  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Moondream is not installed. Install with: pip install -e '.[vision]'"
            ) from exc

        # moondream>=1.1.0 exposes a vl(...) factory.
        if hasattr(md, "vl"):
            mode = os.getenv("MOONDREAM_MODE", "local").strip().lower()
            try:
                if mode == "cloud":
                    return md.vl(api_key=os.getenv("MOONDREAM_API_KEY"))
                if mode == "endpoint":
                    endpoint = os.getenv("MOONDREAM_ENDPOINT", "http://localhost:2020/v1")
                    return md.vl(endpoint=endpoint, api_key=os.getenv("MOONDREAM_API_KEY"))
                # Default local path (requires local backend/model setup).
                return md.vl(local=True)
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(self._friendly_load_error(exc)) from exc

        raise RuntimeError("Unable to initialize moondream model from installed package.")

    def _friendly_load_error(self, exc: Exception) -> str:
        msg = str(exc)
        lowered = msg.lower()
        if (
            "gatedrepoerror" in lowered
            or "cannot access gated repo" in lowered
            or "moondream/moondream3-preview" in lowered
        ):
            return (
                "Moondream local model access is gated on Hugging Face. "
                "Fix one of these ways:\n"
                "1) Request access to moondream/moondream3-preview and login:\n"
                "   huggingface-cli login\n"
                "2) Use endpoint mode:\n"
                "   export MOONDREAM_MODE=endpoint\n"
                "   export MOONDREAM_ENDPOINT=http://localhost:2020/v1\n"
                "3) Use cloud mode:\n"
                "   export MOONDREAM_MODE=cloud\n"
                "   export MOONDREAM_API_KEY=<key>"
            )
        return f"Failed to initialize Moondream model: {msg}"

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
        if self._backend == "ollama":
            return self._run_ollama(prompt, image_path)

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

    def _run_ollama(self, prompt: str, image_path: Path) -> str:
        model = os.getenv("OLLAMA_VISION_MODEL", "llava:7b")
        endpoint = os.getenv("OLLAMA_ENDPOINT", "http://127.0.0.1:11434/api/generate")
        image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")

        payload = {
            "model": model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "format": "json",
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                parsed = json.loads(response.read().decode("utf-8"))
            return str(parsed.get("response", ""))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Ollama is not reachable. Start it and pull a vision model, e.g.:\n"
                "  ollama serve\n"
                "  ollama pull llava:7b\n"
                "Then set SCREENSENTINEL_VISION_BACKEND=ollama"
            ) from exc

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
