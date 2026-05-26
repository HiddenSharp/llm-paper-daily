#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from paper_learning.config import load_config
from paper_learning.deep_reading import build_ljg_paper_runtime_request
from paper_learning.selected_papers_io import dump_selected_papers
from paper_learning.models import SelectedPaper
from paper_learning.paper_daily_adapter import load_discovered_records, load_paper_daily_records


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

    selected_path = run_dir / "selected-papers.json"
    dump_selected_papers(selected_path, selected)
    cfg.deep_reading.org_artifact_dir.mkdir(parents=True, exist_ok=True)
    ljg_path = run_dir / "ljg-paper-requests.json"
    ljg_payload = {
        "mode": "ljg-paper-org-artifact",
        "requests": [build_ljg_paper_runtime_request(paper, cfg.deep_reading) for paper in selected],
    }
    ljg_path.write_text(json.dumps(ljg_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_papers_path": str(selected_path),
        "ljg_paper_requests_path": str(ljg_path),
        "count": len(selected),
    }, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare local selected-paper and ljg-paper request artifacts for queue-stage validation.")
    parser.add_argument("--config", required=True, help="Path to paper-learning config JSON.")
    parser.add_argument("--date", required=True, help="UTC run date in YYYY-MM-DD format.")
    parser.add_argument("--limit", type=int, default=0, help="Select the first N papers when paper IDs are not provided.")
    parser.add_argument("--paper-id", action="append", default=[], help="Explicit paper_id values such as arxiv:2605.19932.")
    parser.add_argument("--skip-summary", action="store_true", help="Build selected papers from discovery artifacts instead of canonical summary-backed records.")
    parser.add_argument("--human-instruction", default="", help="Optional instruction applied to each selected paper.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
