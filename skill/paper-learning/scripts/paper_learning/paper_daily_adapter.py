from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .config import PaperDailyConfig
from .models import DailyPaperRecord


def run_paper_daily(date: str, cfg: PaperDailyConfig) -> None:
    repo_root = cfg.repo_root
    discover_out = repo_root / "data" / "paper-learning" / "runs" / date / "discovered-papers.json"
    discover_out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            cfg.python,
            cfg.discover_script,
            "--date",
            date,
            "--json",
            "--out",
            str(discover_out),
            "--select",
            str(cfg.select),
            "--max-results-per-keyword",
            str(cfg.max_results_per_keyword),
        ],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        [
            cfg.python,
            cfg.generate_feed_script,
            "--repo-root",
            ".",
            "--date",
            date,
            "--select",
            str(cfg.select),
            "--max-results-per-keyword",
            str(cfg.max_results_per_keyword),
            "--score-threshold",
            str(cfg.score_threshold),
        ],
        cwd=repo_root,
        check=True,
    )


def load_paper_daily_records(canonical_path: Path, discovered_path: Path | None = None) -> list[DailyPaperRecord]:
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    discovery_by_id = _load_discovery_by_id(discovered_path)
    records: list[DailyPaperRecord] = []
    for item in canonical.get("items", []):
        paper_id = item["paper_id"]
        discovery = discovery_by_id.get(paper_id, {})
        links = item.get("links", {})
        signals = {
            "priority_keyword": discovery.get("priority_keyword", item.get("category_alias", "")),
            "reasons": discovery.get("reasons", []),
        }
        records.append(DailyPaperRecord(
            paper_id=f"arxiv:{paper_id}",
            source="arXiv",
            title=item.get("title", ""),
            authors=list(item.get("authors", [])),
            institutions=item.get("institution") or "",
            abstract=item.get("abstract", ""),
            digest_summary=item.get("render_excerpt", ""),
            summary_cn=item.get("summary_cn", ""),
            summary_en=item.get("summary_en", ""),
            published_date=item.get("date", canonical.get("run_date", "")),
            run_date=canonical.get("run_date", item.get("date", "")),
            url=links.get("abs") or "",
            pdf_url=links.get("pdf"),
            topic=item.get("category_key", ""),
            score=float(discovery.get("score", 0.0)),
            signals=signals,
            provenance=item.get("provenance", {}),
        ))
    return records


def _load_discovery_by_id(path: Path | None) -> dict[str, dict]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for item in payload.get("selected", []):
        arxiv_id = str(item.get("arxiv_id", "")).split("v", 1)[0]
        if arxiv_id:
            result[arxiv_id] = item
    return result
