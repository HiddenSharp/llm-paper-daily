from __future__ import annotations

import re
from pathlib import Path

from .config import DeepReadingConfig
from .models import DeepNote, SelectedPaper
from .org_converter import org_to_markdown, validate_ljg_paper_org


def generate_deep_note(paper: SelectedPaper, cfg: DeepReadingConfig) -> DeepNote:
    if cfg.mode == "fallback":
        return fallback_deep_note(paper)
    if cfg.mode == "org_artifact":
        path = org_artifact_path(cfg.org_artifact_dir, paper.record.paper_id)
        if not path.exists():
            raise FileNotFoundError(
                f"Missing ljg-paper Org artifact for {paper.record.paper_id}: {path}. "
                "Run the agent runtime with the ljg-paper skill and write the resulting Org document there."
            )
        return deep_note_from_ljg_org(paper, path.read_text(encoding="utf-8"))
    raise ValueError(f"Unsupported deep_reading.mode: {cfg.mode}")


def org_artifact_path(base_dir: str | Path, paper_id: str) -> Path:
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", paper_id).strip("_")
    return Path(base_dir) / f"{safe_id}.org"


def build_ljg_paper_runtime_request(paper: SelectedPaper, cfg: DeepReadingConfig) -> dict:
    path = org_artifact_path(cfg.org_artifact_dir, paper.record.paper_id)
    return {
        "paper": paper.record.to_dict(),
        "human_instruction": paper.human_instruction,
        "org_artifact_path": str(path),
        "agent_instruction": (
            "Use the ljg-paper skill to deep-read this paper. "
            "Write the complete Org document to org_artifact_path. "
            "Do not convert it to DeepNote JSON; paper-learning will adapt the Org artifact."
        ),
    }


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


def deep_note_from_ljg_org(
    paper: SelectedPaper,
    org_text: str,
    *,
    metadata: dict | None = None,
) -> DeepNote:
    fallback_metadata = {
        **_metadata_from_paper(paper),
        **(metadata or {}),
    }
    validate_ljg_paper_org(org_text, fallback_metadata=fallback_metadata)
    org_metadata, markdown = org_to_markdown(org_text)
    merged_metadata = {**fallback_metadata, **org_metadata}
    tags = [paper.record.topic] if paper.record.topic else []
    proposed = paper.record.topic.title() if paper.record.topic else "Uncategorized Paper"
    return DeepNote(
        title=merged_metadata.get("title") or paper.record.title,
        paper_id=paper.record.paper_id,
        reading_focus=paper.human_instruction,
        markdown=markdown,
        contribution_type="Method",
        method_tags=tags,
        proposed_area=proposed,
        archive_confidence="Medium",
        extra_properties=_build_extra_properties(merged_metadata),
    )


def _metadata_from_paper(paper: SelectedPaper) -> dict:
    record = paper.record
    metadata = {
        "subtitle": record.title,
        "authors": ", ".join(record.authors),
        "source": record.url,
    }
    if record.source and record.published_date:
        metadata["venue"] = f"{record.source} {record.published_date[:4]}"
    return {key: value for key, value in metadata.items() if value}


def _build_extra_properties(metadata: dict) -> dict:
    extras: dict = {}
    if metadata.get("subtitle"):
        extras["original_title"] = metadata["subtitle"]
    if metadata.get("authors"):
        extras["authors"] = metadata["authors"]
    if metadata.get("venue"):
        extras["venue"] = metadata["venue"]
    source = metadata.get("source")
    if source and (source.startswith("http://") or source.startswith("https://")):
        extras["source_url"] = source
    # Allow direct override via explicit keys in the JSON metadata block.
    for key in ("original_title", "authors", "venue", "source_url"):
        if metadata.get(key):
            extras[key] = metadata[key]
    return extras
