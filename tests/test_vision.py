from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
