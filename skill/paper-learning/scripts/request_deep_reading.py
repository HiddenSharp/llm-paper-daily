#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from paper_learning.config import load_config
from paper_learning.deep_reading_request_resolver import resolve_deep_reading_request
from paper_learning.selected_papers_io import dump_deep_reading_request, dump_selected_papers


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    selector_type = _selector_type(args)
    trigger_source = _trigger_source(args, selector_type)
    request = resolve_deep_reading_request(
        cfg=cfg,
        date=args.date,
        selector_type=selector_type,
        human_instruction=args.human_instruction,
        trigger_source=trigger_source,
        skip_summary=args.skip_summary,
        paper_ids=args.paper_id,
    )

    run_dir = cfg.runtime.artifact_dir / args.date
    request_path = Path(args.out) if args.out else run_dir / "deep-reading-request.json"
    selected_path = request_path.with_name("selected-papers.json")
    dump_deep_reading_request(request_path, request)
    dump_selected_papers(selected_path, request.selected_papers)

    payload = {
        "ok": True,
        "date": args.date,
        "selector_type": request.selector_type,
        "candidate_source": request.candidate_source,
        "trigger_source": request.trigger_source,
        "requires_confirmation": request.requires_confirmation,
        "confirmed": request.confirmed,
        "human_instruction": request.human_instruction,
        "count": len(request.selected_papers),
        "resolved_paper_ids": request.resolved_paper_ids,
        "candidates": [
            {
                "paper_id": paper.record.paper_id,
                "title": paper.record.title,
                "notion_page_id": paper.notion_page_id,
                "human_instruction": paper.human_instruction,
            }
            for paper in request.selected_papers
        ],
        "deep_reading_request_path": str(request_path),
        "selected_papers_path": str(selected_path),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve a deep-reading request from chat-facing selectors into an explicit paper set.")
    parser.add_argument("--config", required=True, help="Path to paper-learning config JSON.")
    parser.add_argument("--date", required=True, help="UTC run date in YYYY-MM-DD format.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--paper-id", action="append", default=[], help="Explicit paper_id values such as arxiv:2605.19932.")
    group.add_argument("--use-notion-selected", action="store_true", help="Use papers currently marked Selected in Notion for this date.")
    group.add_argument("--all-from-report", action="store_true", help="Use every paper in the current daily report.")
    parser.add_argument("--selector-type", choices=["explicit_paper_ids", "agent_selected_subset"], help="Override selector type when using --paper-id.")
    parser.add_argument("--trigger-source", help="Optional provenance string such as chat_manual or chat_agent_select.")
    parser.add_argument("--human-instruction", default="", help="Optional user-provided reading focus.")
    parser.add_argument("--skip-summary", action="store_true", help="Resolve candidates from discovery artifacts instead of canonical summary-backed records.")
    parser.add_argument("--out", help="Optional output path for the deep-reading request JSON.")
    return parser.parse_args()


def _selector_type(args: argparse.Namespace) -> str:
    if args.use_notion_selected:
        return "notion_selected_set"
    if args.all_from_report:
        return "all_from_daily_report"
    return args.selector_type or "explicit_paper_ids"


def _trigger_source(args: argparse.Namespace, selector_type: str) -> str:
    if args.trigger_source:
        return args.trigger_source
    defaults = {
        "notion_selected_set": "chat_manual",
        "all_from_daily_report": "chat_batch_all",
        "explicit_paper_ids": "chat_manual",
        "agent_selected_subset": "chat_agent_select",
    }
    return defaults[selector_type]


if __name__ == "__main__":
    raise SystemExit(main())
