from __future__ import annotations

import argparse

from .config import load_settings
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Aurevia Swarm-style QA tests.")
    parser.add_argument(
        "--channel",
        action="append",
        choices=["api", "web", "mobile"],
        help="Limit execution to one channel. Can be repeated.",
    )
    args = parser.parse_args()

    settings = load_settings()
    channels = set(args.channel) if args.channel else None
    results, report = run_pipeline(settings, channels)
    passed = sum(1 for result in results if result.verdict == "PASS")
    failed = sum(1 for result in results if result.verdict == "FAIL")
    warned = sum(1 for result in results if result.verdict == "WARN")
    print(f"Report: {report}")
    print(f"PASS={passed} WARN={warned} FAIL={failed}")


if __name__ == "__main__":
    main()


