from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="screensentinel")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Start a focus session")
    start.add_argument("--goal", required=True, help="Declared focus goal")
    start.add_argument(
        "--duration-min", required=True, type=int, help="Session length in minutes"
    )
    start.add_argument(
        "--interval-sec", type=int, default=30, help="Check interval in seconds"
    )
    start.add_argument(
        "--strictness",
        choices=("lenient", "normal", "strict"),
        default="normal",
        help="Drift sensitivity",
    )
    start.add_argument(
        "--debug-save-captures",
        action="store_true",
        help="Keep screenshot files in data/captures",
    )
    start.add_argument(
        "--db-path",
        default="data/screensentinel.db",
        help="SQLite database path",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "start":
        from rich.console import Console

        from .session import run_session
        from .types import SessionConfig

        console = Console()
        config = SessionConfig(
            goal=args.goal,
            duration_min=args.duration_min,
            interval_sec=args.interval_sec,
            strictness=args.strictness,
            debug_save_captures=args.debug_save_captures,
            db_path=args.db_path,
        )
        run_session(config, console)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
