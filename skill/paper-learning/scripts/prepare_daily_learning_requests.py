#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from paper_learning.config import load_config
from paper_learning.paper_daily_adapter import prepare_paper_daily_summary_requests


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    select_override = args.limit if args.limit > 0 else None
    requests_path = prepare_paper_daily_summary_requests(args.date, cfg.paper_daily, select_override=select_override)
    payload = json.loads(requests_path.read_text(encoding="utf-8"))
    output = {
        "mode": "paper-learning-daily-stage",
        "date": args.date,
        "paper_daily_summary_requests_path": str(requests_path),
        "paper_daily_summary_requests": payload,
        "next_command": (
            f"python3 skill/paper-learning/scripts/run_daily_learning.py "
            f"--config {args.config} --date {args.date}"
        ),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare runtime requests required before the full paper-learning daily stage.")
    parser.add_argument("--config", required=True, help="Path to paper-learning config JSON.")
    parser.add_argument("--date", required=True, help="UTC run date in YYYY-MM-DD format.")
    parser.add_argument("--limit", type=int, default=0, help="Limit prepared paper-daily requests; 0 means use the configured default.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
