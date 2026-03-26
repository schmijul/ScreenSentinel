from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from screensentinel.vision import VisionEngine


class TestVisionParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = VisionEngine.__new__(VisionEngine)

    def test_parse_json_payload(self) -> None:
        result = self.engine._parse_response('{"on_task": true, "confidence": 0.91, "reason": "coding"}')
        assert result is not None
        self.assertTrue(result.on_task)
        self.assertAlmostEqual(result.confidence, 0.91)
        self.assertEqual(result.reason, "coding")

    def test_parse_legacy_text_payload(self) -> None:
        result = self.engine._parse_response("on_task=false; confidence=0.77; reason=scrolling")
        assert result is not None
        self.assertFalse(result.on_task)
        self.assertAlmostEqual(result.confidence, 0.77)
        self.assertEqual(result.reason, "scrolling")

    def test_friendly_error_for_gated_repo(self) -> None:
        message = self.engine._friendly_load_error(
            Exception("GatedRepoError: Cannot access gated repo moondream/moondream3-preview")
        )
        self.assertIn("huggingface-cli login", message)
        self.assertIn("MOONDREAM_MODE=endpoint", message)

    def test_ollama_backend_returns_response_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "frame.png"
            image_path.write_bytes(b"fake")

            class _Resp:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def read(self):
                    return b'{"response":"{\\"on_task\\": true, \\"confidence\\": 0.9, \\"reason\\": \\"coding\\"}"}'

            with patch.dict(os.environ, {"SCREENSENTINEL_VISION_BACKEND": "ollama"}, clear=False):
                engine = VisionEngine()
                with patch("urllib.request.urlopen", return_value=_Resp()):
                    raw = engine._run_inference("prompt", image_path)
                    self.assertIn('"on_task": true', raw)


if __name__ == "__main__":
    unittest.main()
