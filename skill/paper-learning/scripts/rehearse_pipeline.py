#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from paper_learning.config import load_config
from paper_learning.deep_reading import validate_org_artifacts
from paper_learning.paper_daily_adapter import load_discovered_records
from paper_learning.selected_papers_io import load_selected_papers


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    run_dir = cfg.runtime.artifact_dir / args.date
    selected_path = Path(args.selected_papers_json) if args.selected_papers_json else run_dir / "selected-papers.json"

    daily_readiness = _run_json_command(
        [
            cfg.paper_daily.python,
            "skill/paper-learning/scripts/check_pipeline_readiness.py",
            "--config",
            args.config,
            "--date",
            args.date,
            "--stage",
            "daily",
            "--limit",
            str(args.daily_limit),
        ],
        cwd=cfg.paper_daily.repo_root,
    )

    queue_readiness = None
    if selected_path.exists():
        queue_readiness = _run_json_command(
            [
                cfg.paper_daily.python,
                "skill/paper-learning/scripts/check_pipeline_readiness.py",
                "--config",
                args.config,
                "--date",
                args.date,
                "--stage",
                "queue",
                "--selected-papers-json",
                str(selected_path),
                "--limit",
                str(args.queue_limit),
            ],
            cwd=cfg.paper_daily.repo_root,
        )
    elif args.include_queue:
        queue_readiness = {
            "ok": False,
            "stage": "queue",
            "date": args.date,
            "results": [],
            "message": f"Missing selected-papers artifact: {selected_path}",
        }

    daily_run = None
    if daily_readiness.get("ok"):
        daily_run = _run_json_command(
            [
                cfg.paper_daily.python,
                "skill/paper-learning/scripts/run_daily_learning.py",
                "--config",
                args.config,
                "--date",
                args.date,
                "--dry-run",
                "--limit",
                str(args.daily_limit),
            ],
            cwd=cfg.paper_daily.repo_root,
        )

    queue_run = None
    if args.include_queue and queue_readiness and queue_readiness.get("ok"):
        queue_run = _run_json_command(
            [
                cfg.paper_daily.python,
                "skill/paper-learning/scripts/process_notion_queue.py",
                "--config",
                args.config,
                "--selected-papers-json",
                str(selected_path),
                "--dry-run",
                "--limit",
                str(args.queue_limit),
            ],
            cwd=cfg.paper_daily.repo_root,
        )

    payload = {
        "date": args.date,
        "daily_readiness": daily_readiness,
        "daily_run": daily_run,
        "queue_readiness": queue_readiness,
        "queue_run": queue_run,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    overall_ok = bool(daily_run and daily_run.get("ok")) and (not args.include_queue or bool(queue_run and queue_run.get("ok")))
    return 0 if overall_ok else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local rehearsal of the paper-learning pipeline by checking readiness and executing dry-run stages when artifacts are present.")
    parser.add_argument("--config", required=True, help="Path to paper-learning config JSON.")
    parser.add_argument("--date", required=True, help="UTC run date in YYYY-MM-DD format.")
    parser.add_argument("--daily-limit", type=int, default=3, help="Number of papers to use for the daily-stage rehearsal.")
    parser.add_argument("--queue-limit", type=int, default=1, help="Number of papers to use for the queue-stage rehearsal.")
    parser.add_argument("--selected-papers-json", help="Optional selected-papers JSON artifact for queue rehearsal.")
    parser.add_argument("--include-queue", action="store_true", help="Also rehearse the queue stage when selected papers and org artifacts are available.")
    return parser.parse_args()


def _run_json_command(args: list[str], *, cwd: Path) -> dict:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    content = (result.stdout or result.stderr).strip()
    if not content:
        return {
            "ok": False,
            "status": "failed",
            "message": f"Command returned no output: {' '.join(args)}",
        }
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "status": "failed",
            "message": content,
        }


if __name__ == "__main__":
    raise SystemExit(main())
