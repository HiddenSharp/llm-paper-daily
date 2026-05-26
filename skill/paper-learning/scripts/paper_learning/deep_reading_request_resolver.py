from __future__ import annotations

import json
from pathlib import Path

from .models import DailyPaperRecord, DeepReadingRequest, SelectedPaper
from .notion_client import NotionClient
from .paper_daily_adapter import load_discovered_records, load_paper_daily_records


def load_daily_records(*, cfg, date: str, skip_summary: bool) -> list[DailyPaperRecord]:
    run_dir = cfg.runtime.artifact_dir / date
    discovered_path = run_dir / "discovered-papers.json"
    canonical_path = cfg.paper_daily.repo_root / "data" / "canonical-papers.json"
    if skip_summary:
        return load_discovered_records(discovered_path, run_date=date)
    return load_paper_daily_records(canonical_path=canonical_path, discovered_path=discovered_path)


def resolve_deep_reading_request(
    *,
    cfg,
    date: str,
    selector_type: str,
    human_instruction: str,
    trigger_source: str,
    notion: NotionClient | None = None,
    skip_summary: bool = False,
    paper_ids: list[str] | None = None,
) -> DeepReadingRequest:
    daily_records = load_daily_records(cfg=cfg, date=date, skip_summary=skip_summary)
    if selector_type == "notion_selected_set":
        notion = notion or NotionClient(cfg.notion)
        selected = _resolve_notion_selected_set(
            daily_records=daily_records,
            selected_papers=notion.query_selected_papers(),
            human_instruction=human_instruction,
        )
        return DeepReadingRequest(
            date=date,
            selector_type=selector_type,
            candidate_source="notion_selected",
            resolved_paper_ids=[paper.record.paper_id for paper in selected],
            human_instruction=human_instruction,
            trigger_source=trigger_source,
            requires_confirmation=True,
            selected_papers=selected,
        )

    page_id_map = _load_daily_page_id_map(cfg.runtime.artifact_dir / f"{date}.json", daily_records)
    notion = notion or NotionClient(cfg.notion)
    if selector_type == "all_from_daily_report":
        selected = _resolve_daily_report_set(
            daily_records=daily_records,
            page_id_map=page_id_map,
            notion=notion,
            human_instruction=human_instruction,
        )
        return DeepReadingRequest(
            date=date,
            selector_type=selector_type,
            candidate_source="daily_report",
            resolved_paper_ids=[paper.record.paper_id for paper in selected],
            human_instruction=human_instruction,
            trigger_source=trigger_source,
            requires_confirmation=False,
            selected_papers=selected,
        )

    if selector_type in {"explicit_paper_ids", "agent_selected_subset"}:
        wanted = list(paper_ids or [])
        selected = _resolve_explicit_set(
            daily_records=daily_records,
            page_id_map=page_id_map,
            notion=notion,
            paper_ids=wanted,
            human_instruction=human_instruction,
        )
        return DeepReadingRequest(
            date=date,
            selector_type=selector_type,
            candidate_source="chat_explicit" if selector_type == "explicit_paper_ids" else "agent_resolution",
            resolved_paper_ids=[paper.record.paper_id for paper in selected],
            human_instruction=human_instruction,
            trigger_source=trigger_source,
            requires_confirmation=(selector_type == "agent_selected_subset"),
            selected_papers=selected,
        )

    raise ValueError(f"Unsupported selector_type: {selector_type}")


def _resolve_notion_selected_set(
    *,
    daily_records: list[DailyPaperRecord],
    selected_papers: list[SelectedPaper],
    human_instruction: str,
) -> list[SelectedPaper]:
    daily_ids = {record.paper_id for record in daily_records}
    result = [paper for paper in selected_papers if paper.record.paper_id in daily_ids]
    if human_instruction:
        result = [_with_instruction(paper, human_instruction) for paper in result]
    return result


def _resolve_daily_report_set(
    *,
    daily_records: list[DailyPaperRecord],
    page_id_map: dict[str, str],
    notion: NotionClient,
    human_instruction: str,
) -> list[SelectedPaper]:
    paper_ids = [record.paper_id for record in daily_records]
    return _resolve_explicit_set(
        daily_records=daily_records,
        page_id_map=page_id_map,
        notion=notion,
        paper_ids=paper_ids,
        human_instruction=human_instruction,
    )


def _resolve_explicit_set(
    *,
    daily_records: list[DailyPaperRecord],
    page_id_map: dict[str, str],
    notion: NotionClient,
    paper_ids: list[str],
    human_instruction: str,
) -> list[SelectedPaper]:
    by_id = {record.paper_id: record for record in daily_records}
    missing = [paper_id for paper_id in paper_ids if paper_id not in by_id]
    if missing:
        raise ValueError(f"Paper IDs not present in the daily report: {', '.join(missing)}")

    selected_by_id: dict[str, SelectedPaper] = {}
    if _is_dry_run_notion(notion):
        selected_by_id.update(_build_local_selected_by_id(by_id, paper_ids, page_id_map, human_instruction))
    else:
        available_page_ids = [page_id_map[paper_id] for paper_id in paper_ids if paper_id in page_id_map]
        if available_page_ids:
            selected_by_id.update({
                paper.record.paper_id: paper
                for paper in notion.get_papers_by_page_ids(available_page_ids)
            })

        missing_ids = [paper_id for paper_id in paper_ids if paper_id not in selected_by_id]
        if missing_ids:
            fallback_urls = [by_id[paper_id].url for paper_id in missing_ids if by_id[paper_id].url]
            if fallback_urls:
                selected_by_id.update({
                    paper.record.paper_id: paper
                    for paper in notion.find_papers_by_urls(fallback_urls)
                })

    unresolved = [paper_id for paper_id in paper_ids if paper_id not in selected_by_id]
    if unresolved:
        raise ValueError(
            "Could not resolve Notion paper pages for: "
            + ", ".join(unresolved)
        )

    return [
        _with_instruction(selected_by_id[paper_id], human_instruction) if human_instruction else selected_by_id[paper_id]
        for paper_id in paper_ids
    ]


def _load_daily_page_id_map(path: Path, daily_records: list[DailyPaperRecord]) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    paper_results = payload.get("paper_results", [])
    result: dict[str, str] = {}
    for record, paper_result in zip(daily_records, paper_results):
        page_id = paper_result.get("data", {}).get("id")
        if page_id:
            result[record.paper_id] = page_id
    return result


def _with_instruction(paper: SelectedPaper, human_instruction: str) -> SelectedPaper:
    return SelectedPaper(
        notion_page_id=paper.notion_page_id,
        record=paper.record,
        human_instruction=human_instruction,
        existing_research_area_ids=list(paper.existing_research_area_ids),
        existing_deep_note_id=paper.existing_deep_note_id,
    )


def _build_local_selected_by_id(
    by_id: dict[str, DailyPaperRecord],
    paper_ids: list[str],
    page_id_map: dict[str, str],
    human_instruction: str,
) -> dict[str, SelectedPaper]:
    selected: dict[str, SelectedPaper] = {}
    for paper_id in paper_ids:
        record = by_id[paper_id]
        notion_page_id = page_id_map.get(paper_id, f"local-{paper_id.replace(':', '-')}")
        selected[paper_id] = SelectedPaper(
            notion_page_id=notion_page_id,
            record=record,
            human_instruction=human_instruction,
        )
    return selected


def _is_dry_run_notion(notion: NotionClient) -> bool:
    config = getattr(notion, "config", None)
    return bool(getattr(config, "dry_run", False))
