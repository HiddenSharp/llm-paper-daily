#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from paper_learning.config import load_config
from paper_learning.daily_pipeline import run_daily_pipeline
from paper_learning.feishu_client import FeishuClient
from paper_learning.huggingface_client import fetch_hf_daily_papers
from paper_learning.notion_client import NotionClient
from paper_learning.paper_daily_adapter import load_paper_daily_records, run_paper_daily


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    if args.dry_run:
        cfg = replace(
            cfg,
            notion=replace(cfg.notion, dry_run=True),
            feishu=replace(cfg.feishu, dry_run=True),
            runtime=replace(cfg.runtime, dry_run=True),
        )

    repo_root = cfg.paper_daily.repo_root
    run_dir = cfg.runtime.artifact_dir / args.date
    discovered_path = run_dir / "discovered-papers.json"
    canonical_path = repo_root / "data" / "canonical-papers.json"

    if not args.skip_paper_daily:
        run_paper_daily(args.date, cfg.paper_daily)

    records = load_paper_daily_records(canonical_path=canonical_path, discovered_path=discovered_path)
    limit_satisfied = bool(args.limit and len(records) >= args.limit)
    if cfg.huggingface.enabled and not limit_satisfied:
        records.extend(fetch_hf_daily_papers(args.date, cfg.huggingface))
    if args.limit:
        records = records[: args.limit]

    result = run_daily_pipeline(
        date=args.date,
        records=records,
        notion=NotionClient(cfg.notion),
        feishu=FeishuClient(cfg.feishu),
        artifact_dir=cfg.runtime.artifact_dir,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the paper-learning daily report workflow.")
    parser.add_argument("--config", required=True, help="Path to paper-learning config JSON.")
    parser.add_argument("--date", required=True, help="UTC run date in YYYY-MM-DD format.")
    parser.add_argument("--dry-run", action="store_true", help="Force Notion and Feishu adapters into dry-run mode.")
    parser.add_argument("--limit", type=int, default=0, help="Limit records after source aggregation; 0 means no limit.")
    parser.add_argument("--skip-paper-daily", action="store_true", help="Read existing paper-daily artifacts instead of running discovery.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
