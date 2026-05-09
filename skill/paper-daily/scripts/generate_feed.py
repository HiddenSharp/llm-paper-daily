#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from paper_daily.arxiv_client import ArxivClient
from paper_daily.discovery import find_next_discovery, select_ranked_candidates
from paper_daily.feed import read_feed_state, write_feed_outputs, write_feed_state
from paper_daily.institutions import load_catalog
from paper_daily.render import write_summary_files
from paper_daily.summary import candidate_to_canonical


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    skill_root = Path(__file__).resolve().parents[1]
    catalog = load_catalog(skill_root / "references" / "institutions.json")
    client = ArxivClient(delay_seconds=args.delay_seconds, timeout_seconds=args.timeout_seconds, retries=args.retries)
    previous_state = read_feed_state(skill_root)
    selection = find_next_discovery(
        client=client,
        catalog=catalog,
        preferred_date=args.date,
        analyzed_dates=set(previous_state.get("analyzed_content_dates", [])),
        max_lookback_days=args.backfill_days,
        max_results_per_keyword=args.max_results_per_keyword,
    )
    selected_date = selection["selected_date"]
    attempted_dates = selection["attempted_dates"]
    discovered = selection["discovered"]

    if not selected_date or not discovered:
        state_path = write_feed_state(
            skill_root,
            previous_state=previous_state,
            records=[],
            preferred_date=args.date,
            attempted_dates=attempted_dates,
            updated=False,
        )
        print(f"preferred_date={args.date}")
        print("selected=0")
        print(f"attempted_dates={','.join(attempted_dates)}")
        print(f"state={state_path}")
        return 0

    selected_candidates = select_ranked_candidates(
        discovered["ranked"],
        min_select=args.min_select,
        max_select=args.select,
        score_threshold=args.score_threshold,
    )
    selected = [candidate.to_dict() for candidate in selected_candidates]
    canonical = [candidate_to_canonical(candidate, run_date=selected_date) for candidate in selected]
    write_summary_files(repo_root, canonical)
    canonical_path, feed_path, state_path = write_feed_outputs(
        repo_root,
        skill_root,
        canonical,
        selected_date,
        public_base_url=args.public_base_url,
        source_repo=args.source_repo,
    )
    state_path = write_feed_state(
        skill_root,
        previous_state=previous_state,
        records=canonical,
        preferred_date=args.date,
        attempted_dates=attempted_dates,
        updated=True,
        selected_date=selected_date,
    )
    print(f"preferred_date={args.date}")
    print(f"selected_date={selected_date}")
    print(f"selected={len(canonical)}")
    print(f"canonical={canonical_path}")
    print(f"feed={feed_path}")
    print(f"state={state_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate canonical and feed outputs for paper-daily.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--date", default=(datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"))
    parser.add_argument("--select", type=int, default=5, help="Maximum number of papers to publish.")
    parser.add_argument("--min-select", type=int, default=3, help="Minimum number of papers to publish when filtered candidates allow it.")
    parser.add_argument("--score-threshold", type=float, default=6.0, help="Score threshold for preferred selection before falling back to the top-ranked minimum set.")
    parser.add_argument("--max-results-per-keyword", type=int, default=10)
    parser.add_argument("--delay-seconds", type=float, default=3.1)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--backfill-days", type=int, default=7)
    parser.add_argument("--public-base-url", default="", help="Optional public base URL for summary asset links.")
    parser.add_argument("--source-repo", default="xianshang33/llm-paper-daily", help="Source repository identifier for feed metadata.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
