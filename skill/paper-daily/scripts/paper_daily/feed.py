from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .models import CanonicalPaper, FeedItem
from .render import summary_paths


def read_feed_state(repo_root: Path) -> dict:
    path = repo_root / "data" / "state-feed.json"
    legacy_path = repo_root / "skill" / "paper-daily" / "output" / "state-feed.json"
    if not path.exists() and legacy_path.exists():
        path = legacy_path
    if not path.exists():
        return default_feed_state()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise RuntimeError(f"Corrupt feed state: {path}")
    return migrate_feed_state(payload)


def default_feed_state() -> dict:
    return {
        "schema_version": "v2",
        "feed_id": "paper-daily",
        "analyzed_content_dates": [],
        "last_item_ids": [],
        "watermarks": {},
    }


def migrate_feed_state(payload: dict) -> dict:
    state = default_feed_state()
    state.update(payload)

    analyzed_dates = list(state.get("analyzed_content_dates", []))
    if not analyzed_dates and state.get("last_item_ids"):
        watermarks = state.get("watermarks", {}) or {}
        migrated_date = (
            state.get("last_success_date")
            or state.get("last_content_date")
            or watermarks.get("selected_date")
            or watermarks.get("run_date")
            or state.get("last_run_date")
        )
        if migrated_date:
            analyzed_dates.append(migrated_date)

    state["schema_version"] = "v2"
    state["analyzed_content_dates"] = unique_dates(analyzed_dates)
    state["watermarks"] = state.get("watermarks", {}) or {}
    latest_candidates = [
        state.get("latest_updates_date"),
        state.get("last_success_date"),
        state.get("last_content_date"),
        *state["analyzed_content_dates"],
    ]
    state["latest_updates_date"] = max((value for value in latest_candidates if value), default=None)
    return state


def unique_dates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def write_feed_outputs(
    repo_root: Path,
    records: list[CanonicalPaper],
    run_date: str,
    *,
    public_base_url: str | None = None,
    source_repo: str = "xianshang33/llm-paper-daily",
) -> tuple[Path, Path, Path]:
    generated_at = datetime.now(timezone.utc).isoformat()
    canonical_payload = {
        "schema_version": "v1",
        "generated_at": generated_at,
        "run_date": run_date,
        "items": [record.to_dict() for record in records],
    }
    feed_payload = {
        "schema_version": "v1",
        "feed_id": "paper-daily",
        "generated_at": generated_at,
        "run_date": run_date,
        "source_repo": source_repo,
        "items": [canonical_to_feed_item(record, public_base_url=public_base_url).to_dict() for record in records],
    }
    root_canonical = repo_root / "data" / "canonical-papers.json"
    root_feed = repo_root / "feed-papers.json"
    root_canonical.parent.mkdir(parents=True, exist_ok=True)
    root_canonical.write_text(json.dumps(canonical_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    root_feed.write_text(json.dumps(feed_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return root_canonical, root_feed, repo_root / "data" / "state-feed.json"


def write_feed_state(
    repo_root: Path,
    *,
    previous_state: dict | None,
    records: list[CanonicalPaper],
    preferred_date: str,
    attempted_dates: list[str],
    updated: bool,
    selected_date: str | None = None,
) -> Path:
    generated_at = datetime.now(timezone.utc).isoformat()
    output_dir = repo_root / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    previous_state = previous_state or read_feed_state(repo_root)
    analyzed_dates = list(previous_state.get("analyzed_content_dates", []))
    if updated and selected_date and selected_date not in analyzed_dates:
        analyzed_dates.append(selected_date)
    latest_updates_date = previous_state.get("latest_updates_date")
    if updated and selected_date and (not latest_updates_date or selected_date >= latest_updates_date):
        latest_updates_date = selected_date
    state_payload = {
        "schema_version": "v2",
        "feed_id": "paper-daily",
        "last_run_date": selected_date if updated else previous_state.get("last_run_date"),
        "last_preferred_date": preferred_date,
        "last_run_at": generated_at,
        "last_attempted_dates": attempted_dates,
        "last_update_status": "updated" if updated else "no_new_content",
        "last_success_at": generated_at if updated else previous_state.get("last_success_at"),
        "last_success_date": selected_date if updated else previous_state.get("last_success_date"),
        "last_content_date": selected_date if updated else previous_state.get("last_content_date"),
        "latest_updates_date": latest_updates_date,
        "last_item_ids": [record.paper_id for record in records] if updated else previous_state.get("last_item_ids", []),
        "analyzed_content_dates": unique_dates(analyzed_dates),
        "watermarks": {
            "preferred_date": preferred_date,
            "selected_date": selected_date if updated else previous_state.get("watermarks", {}).get("selected_date"),
        },
    }
    state_output = output_dir / "state-feed.json"
    state_output.write_text(json.dumps(state_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state_output


def canonical_to_feed_item(record: CanonicalPaper, *, public_base_url: str | None = None) -> FeedItem:
    summary_zh_path, summary_en_path = summary_paths(record)
    base = (public_base_url or "").rstrip("/")
    return FeedItem(
        id=f"arxiv:{record.paper_id}",
        date=record.date,
        title=record.title,
        topic=record.category_key,
        language=["zh", "en"],
        authors=record.authors,
        institution=record.institution,
        summary={
            "zh": compact_digest_summary(record.render_excerpt, lang="zh"),
            "en": compact_digest_summary(record.render_excerpt_en, lang="en"),
        },
        links={
            "abs": record.links.get("abs"),
            "pdf": record.links.get("pdf"),
            "github": record.links.get("github"),
        },
        artifacts={
            "summary_zh_path": summary_zh_path,
            "summary_en_path": summary_en_path,
            "summary_zh_url": f"{base}/{summary_zh_path}" if base else None,
            "summary_en_url": f"{base}/{summary_en_path}" if base else None,
        },
        signals={
            "priority_keyword": record.category_alias,
        },
        provenance=record.provenance,
    )


def compact_digest_summary(text: str, *, lang: str) -> str:
    text = text.replace("<br>", "\n")
    if lang == "zh":
        text = re.sub(r"^机构:.*?\n", "", text, flags=re.S)
    else:
        text = re.sub(r"^Institution:.*?\n", "", text, flags=re.S)
    text = re.sub(r"##+\s*[^-]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 220:
        text = text[:220].rsplit(" ", 1)[0] + "..."
    return text
