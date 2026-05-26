#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from paper_learning.selected_papers_io import dump_deep_reading_request, load_deep_reading_request


def main() -> int:
    args = parse_args()
    path = Path(args.request)
    request = load_deep_reading_request(path)
    confirmed = request.confirmed if args.unconfirm else True
    if args.unconfirm:
        confirmed = False
    updated = type(request)(
        date=request.date,
        selector_type=request.selector_type,
        candidate_source=request.candidate_source,
        resolved_paper_ids=list(request.resolved_paper_ids),
        human_instruction=request.human_instruction,
        trigger_source=request.trigger_source,
        requires_confirmation=request.requires_confirmation,
        confirmed=confirmed,
        selected_papers=list(request.selected_papers),
    )
    dump_deep_reading_request(path, updated)
    print(json.dumps({
        "ok": True,
        "request_path": str(path),
        "requires_confirmation": updated.requires_confirmation,
        "confirmed": updated.confirmed,
        "count": len(updated.selected_papers),
    }, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mark a deep-reading request as confirmed so it can be executed.")
    parser.add_argument("--request", required=True, help="Path to deep-reading-request.json.")
    parser.add_argument("--unconfirm", action="store_true", help="Clear the confirmed flag instead of setting it.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
