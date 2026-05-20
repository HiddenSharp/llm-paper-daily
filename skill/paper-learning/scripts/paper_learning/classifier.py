from __future__ import annotations

import json
from pathlib import Path

from .models import ClassificationResult, DeepNote, ResearchArea


def load_research_areas(path: Path) -> list[ResearchArea]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        ResearchArea(
            name=item["name"],
            aliases=list(item.get("aliases", [])),
            description=item.get("description", ""),
            notion_page_id=item.get("notion_page_id"),
        )
        for item in raw
    ]


def classify_note(note: DeepNote, active_areas: list[ResearchArea]) -> ClassificationResult:
    text = " ".join([note.title, note.markdown, " ".join(note.method_tags)])
    matched = [area for area in active_areas if area.matches(text)]
    if matched:
        ids = [area.notion_page_id or area.name for area in matched]
        return ClassificationResult(
            area_ids=ids,
            proposed_area="",
            confidence="High",
            review_status="Auto Accepted",
        )
    return ClassificationResult(
        area_ids=[],
        proposed_area=note.proposed_area or "Uncategorized Paper",
        confidence="Low",
        review_status="Needs Human Review",
    )
