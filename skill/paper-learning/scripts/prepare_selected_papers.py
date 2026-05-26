#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from paper_learning.config import load_config
from paper_learning.models import SelectedPaper
from paper_learning.paper_daily_adapter import load_discovered_records, load_paper_daily_records
from paper_learning.selected_papers_io import dump_selected_papers


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    run_dir = cfg.runtime.artifact_dir / args.date
    discovered_path = run_dir / "discovered-papers.json"
    canonical_path = cfg.paper_daily.repo_root / "data" / "canonical-papers.json"

    if args.skip_summary:
        records = load_discovered_records(discovered_path, run_date=args.date)
    else:
        records = load_paper_daily_records(canonical_path=canonical_path, discovered_path=discovered_path)

    if args.paper_id:
        wanted = set(args.paper_id)
        records = [record for record in records if record.paper_id in wanted]
    elif args.limit:
        records = records[: args.limit]

    selected = [
        SelectedPaper(
            notion_page_id=f"local-{record.paper_id.replace(':', '-')}",
            record=record,
            human_instruction=args.human_instruction,
        )
        for record in records
    ]
    out_path = Path(args.out) if args.out else run_dir / "selected-papers.json"
    dump_selected_papers(out_path, selected)
    print(json.dumps({
        "selected_papers_path": str(out_path),
        "count": len(selected),
    }, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a local selected-papers artifact for queue-stage validation.")
    parser.add_argument("--config", required=True, help="Path to paper-learning config JSON.")
    parser.add_argument("--date", required=True, help="UTC run date in YYYY-MM-DD format.")
    parser.add_argument("--limit", type=int, default=0, help="Select the first N papers when paper IDs are not provided.")
    parser.add_argument("--paper-id", action="append", default=[], help="Explicit paper_id values such as arxiv:2605.19932.")
    parser.add_argument("--skip-summary", action="store_true", help="Build selected papers from discovery artifacts instead of canonical summary-backed records.")
    parser.add_argument("--human-instruction", default="", help="Optional instruction applied to each selected paper.")
    parser.add_argument("--out", help="Optional output path for the selected-papers JSON.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
