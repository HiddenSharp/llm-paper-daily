#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from paper_daily.arxiv_client import ArxivClient
from paper_daily.discovery import discover_ranked
from paper_daily.filters import DEFAULT_CATEGORIES, DEFAULT_KEYWORDS
from paper_daily.institutions import load_catalog


def main() -> int:
    args = parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    catalog = load_catalog(skill_root / "references" / "institutions.json")

    client = ArxivClient(
        delay_seconds=args.delay_seconds,
        timeout_seconds=args.timeout_seconds,
        retries=args.retries,
    )
    discovered = discover_ranked(
        client=client,
        catalog=catalog,
        date=args.date,
        keywords=args.keywords,
        categories=args.categories,
        max_results_per_keyword=args.max_results_per_keyword,
    )
    ranked = discovered["ranked"]
    selected = ranked[: args.select]

    payload = {
        "date": args.date,
        "keywords": args.keywords,
        "categories": args.categories,
        "query_totals": discovered["query_totals"],
        "counts": discovered["counts"] | {"selected": len(selected)},
        "selected": [candidate.to_dict() for candidate in selected],
        "ranked": [candidate.to_dict() for candidate in ranked],
    }

    if args.json:
        output = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
    else:
        print_report(payload)

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover daily Agent/LLM papers from arXiv.")
    parser.add_argument("--date", default=default_utc_date(), help="UTC arXiv submitted date, YYYY-MM-DD.")
    parser.add_argument("--keywords", nargs="+", default=DEFAULT_KEYWORDS, help="Priority keyword order.")
    parser.add_argument("--categories", nargs="+", default=DEFAULT_CATEGORIES, help="arXiv categories.")
    parser.add_argument("--max-results-per-keyword", type=int, default=50)
    parser.add_argument("--select", type=int, default=5)
    parser.add_argument("--delay-seconds", type=float, default=3.1)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument("--out", help="Write JSON output to a file.")
    return parser.parse_args()


def default_utc_date() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")


def print_report(payload: dict) -> None:
    print(f"date: {payload['date']}")
    print(f"keywords: {', '.join(payload['keywords'])}")
    print(f"categories: {', '.join(payload['categories'])}")
    print(f"query_totals: {payload['query_totals']}")
    print(f"counts: {payload['counts']}")
    print("")
    for index, candidate in enumerate(payload["selected"], start=1):
        matches = candidate["institution_matches"] + candidate["lab_matches"]
        match_text = ", ".join(matches) if matches else "UNKNOWN_FROM_ARXIV"
        print(f"{index}. score={candidate['score']} {candidate['arxiv_id']} [{candidate['priority_keyword']}] {candidate['title']}")
        print(f"   categories: {', '.join(candidate['categories'])}")
        print(f"   institutions: {match_text}")
        print(f"   reasons: {', '.join(candidate['reasons'])}")
        print(f"   abs: {candidate['abs_url']}")
        if candidate["pdf_url"]:
            print(f"   pdf: {candidate['pdf_url']}")


if __name__ == "__main__":
    sys.exit(main())
