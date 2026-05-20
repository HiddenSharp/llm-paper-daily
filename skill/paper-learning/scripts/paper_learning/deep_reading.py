from __future__ import annotations

import json
import subprocess

from .config import DeepReadingConfig
from .models import DeepNote, SelectedPaper


def generate_deep_note(paper: SelectedPaper, cfg: DeepReadingConfig) -> DeepNote:
    if cfg.command:
        payload = json.dumps(
            {
                "paper": paper.record.to_dict(),
                "human_instruction": paper.human_instruction,
            },
            ensure_ascii=False,
        )
        completed = subprocess.run(
            list(cfg.command),
            input=payload,
            text=True,
            capture_output=True,
            check=True,
        )
        return deep_note_from_json(json.loads(completed.stdout))
    return fallback_deep_note(paper)


def fallback_deep_note(paper: SelectedPaper) -> DeepNote:
    record = paper.record
    focus = paper.human_instruction or "Default deep-reading focus"
    markdown = "\n".join(
        [
            f"# {record.title}",
            "",
            "## Problem Setting",
            record.abstract or record.digest_summary or "No abstract available.",
            "",
            "## Core Contribution",
            record.summary_en or record.digest_summary or "No generated summary available.",
            "",
            "## User Focus",
            focus,
            "",
            "## Archive Recommendation",
            f"Initial topic signal: {record.topic or 'Unknown'}.",
        ]
    )
    tags = [record.topic] if record.topic else []
    proposed = record.topic.title() if record.topic else "Uncategorized Paper"
    return DeepNote(
        title=f"Deep Note: {record.title}",
        paper_id=record.paper_id,
        reading_focus=focus,
        markdown=markdown,
        contribution_type="Method",
        method_tags=tags,
        proposed_area=proposed,
        archive_confidence="Medium",
    )


def deep_note_from_json(payload: dict) -> DeepNote:
    return DeepNote(
        title=payload["title"],
        paper_id=payload["paper_id"],
        reading_focus=payload.get("reading_focus", ""),
        markdown=payload["markdown"],
        contribution_type=payload.get("contribution_type", "Method"),
        method_tags=list(payload.get("method_tags", [])),
        proposed_area=payload.get("proposed_area", ""),
        archive_confidence=payload.get("archive_confidence", "Medium"),
    )
