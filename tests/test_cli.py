from __future__ import annotations

import unittest

from screensentinel.cli import build_parser


class TestCli(unittest.TestCase):
    def test_start_requires_goal_and_duration(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["start", "--goal", "Write code", "--duration-min", "25"])
        self.assertEqual(args.command, "start")
        self.assertEqual(args.goal, "Write code")
        self.assertEqual(args.duration_min, 25)

    def test_start_defaults(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["start", "--goal", "Focus", "--duration-min", "10"])
        self.assertEqual(args.interval_sec, 30)
        self.assertEqual(args.strictness, "normal")
        self.assertFalse(args.debug_save_captures)


if __name__ == "__main__":
    unittest.main()
