#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import replace

from paper_learning.classifier import load_research_areas
from paper_learning.config import load_config
from paper_learning.deep_reading import generate_deep_note
from paper_learning.notion_client import NotionClient
from paper_learning.queue_pipeline import process_selected_papers


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    if args.dry_run:
        cfg = replace(
            cfg,
            notion=replace(cfg.notion, dry_run=True),
            runtime=replace(cfg.runtime, dry_run=True),
        )

    active_areas = load_research_areas(cfg.classification.default_research_areas_path)
    result = process_selected_papers(
        notion=NotionClient(cfg.notion),
        deep_reader=lambda paper: generate_deep_note(paper, cfg.deep_reading),
        active_areas=active_areas,
        limit=args.limit,
        force=args.force,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process selected papers from Notion.")
    parser.add_argument("--config", required=True, help="Path to paper-learning config JSON.")
    parser.add_argument("--dry-run", action="store_true", help="Force the Notion adapter into dry-run mode.")
    parser.add_argument("--limit", type=int, default=0, help="Limit selected papers processed; 0 means no limit.")
    parser.add_argument("--force", action="store_true", help="Reprocess papers that already have a deep note relation.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
