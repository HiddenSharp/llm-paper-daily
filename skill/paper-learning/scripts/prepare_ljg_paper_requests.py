#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from paper_learning.config import load_config
from paper_learning.deep_reading import build_ljg_paper_runtime_request
from paper_learning.notion_client import NotionClient
from paper_learning.selected_papers_io import load_deep_reading_request, load_selected_papers


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    cfg.deep_reading.org_artifact_dir.mkdir(parents=True, exist_ok=True)
    if args.deep_reading_request_json:
        selected = load_deep_reading_request(args.deep_reading_request_json).selected_papers
    elif args.selected_papers_json:
        selected = load_selected_papers(args.selected_papers_json)
    else:
        selected = NotionClient(cfg.notion).query_selected_papers()
    if args.limit:
        selected = selected[: args.limit]

    payload = {
        "mode": "ljg-paper-org-artifact",
        "requests": [build_ljg_paper_runtime_request(paper, cfg.deep_reading) for paper in selected],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare ljg-paper runtime requests for selected Notion papers.")
    parser.add_argument("--config", required=True, help="Path to paper-learning config JSON.")
    parser.add_argument("--limit", type=int, default=0, help="Limit selected papers returned; 0 means no limit.")
    parser.add_argument("--deep-reading-request-json", help="Optional deep-reading request JSON artifact to use as the resolved paper set.")
    parser.add_argument("--selected-papers-json", help="Optional local selected-papers JSON artifact to use instead of querying Notion.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
