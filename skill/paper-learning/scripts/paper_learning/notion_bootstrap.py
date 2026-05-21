from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

from .config import AppConfig, load_config
from .models import OperationResult


_UUID_RE = re.compile(r"([0-9a-fA-F]{32}|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})")


def extract_notion_id(value: str) -> str:
    match = _UUID_RE.search(value)
    if not match:
        raise ValueError(f"Could not find a Notion ID in: {value}")
    raw = match.group(1).lower()
    if "-" in raw:
        return raw
    return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


def default_local_config_path() -> Path:
    return Path("~/.paper-learning/config.json").expanduser()


def bootstrap_notion_workspace(*, notion, parent_page_id: str) -> OperationResult:
    research_areas = _ensure_database(
        notion=notion,
        parent_page_id=parent_page_id,
        title="Research Areas",
        properties=_research_areas_schema(),
    )
    research_db_id = research_areas.data.get("id", "dry-run-research-areas")

    deep_notes = _ensure_database(
        notion=notion,
        parent_page_id=parent_page_id,
        title="Deep Notes",
        properties=_deep_notes_base_schema(),
    )
    deep_db_id = deep_notes.data.get("id", "dry-run-deep-notes")

    paper_inbox = _ensure_database(
        notion=notion,
        parent_page_id=parent_page_id,
        title="Paper Inbox",
        properties=_paper_inbox_base_schema(),
    )
    inbox_db_id = paper_inbox.data.get("id", "dry-run-paper-inbox")

    research_update = notion.update_database(
        research_db_id,
        _research_areas_schema(),
    )
    inbox_update = notion.update_database(
        inbox_db_id,
        _paper_inbox_schema_with_relations(research_db_id, deep_db_id),
    )
    deep_update = notion.update_database(
        deep_db_id,
        _deep_notes_schema_with_relations(inbox_db_id, research_db_id),
    )

    return OperationResult(
        ok=True,
        status="created",
        message="notion workspace bootstrapped",
        data={
            "paper_inbox_database_id": inbox_db_id,
            "deep_notes_database_id": deep_db_id,
            "research_areas_database_id": research_db_id,
            "daily_report_parent_page_id": parent_page_id,
            "paper_inbox_url": paper_inbox.data.get("url", ""),
            "deep_notes_url": deep_notes.data.get("url", ""),
            "research_areas_url": research_areas.data.get("url", ""),
            "research_areas_update": research_update.to_dict(),
            "paper_inbox_update": inbox_update.to_dict(),
            "deep_notes_update": deep_update.to_dict(),
        },
    )


def _ensure_database(*, notion, parent_page_id: str, title: str, properties: dict) -> OperationResult:
    existing = notion.find_database_in_parent(parent_page_id=parent_page_id, title=title)
    if existing:
        return OperationResult(True, "reused", "database reused", existing)
    return notion.create_database(parent_page_id=parent_page_id, title=title, properties=properties)


def write_local_config(
    *,
    template_path: str | Path,
    output_path: str | Path,
    parent_page_id: str,
    paper_inbox_database_id: str,
    deep_notes_database_id: str,
    research_areas_database_id: str,
) -> Path:
    cfg = load_config(template_path)
    payload = app_config_to_dict(cfg)
    payload["notion"]["paper_inbox_database_id"] = paper_inbox_database_id
    payload["notion"]["deep_notes_database_id"] = deep_notes_database_id
    payload["notion"]["research_areas_database_id"] = research_areas_database_id
    payload["notion"]["daily_report_parent_page_id"] = parent_page_id
    output = Path(output_path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def app_config_to_dict(cfg: AppConfig) -> dict:
    payload = asdict(cfg)
    payload["paper_daily"]["repo_root"] = str(cfg.paper_daily.repo_root)
    payload["deep_reading"]["org_artifact_dir"] = str(cfg.deep_reading.org_artifact_dir)
    payload["classification"]["default_research_areas_path"] = str(cfg.classification.default_research_areas_path)
    payload["runtime"]["artifact_dir"] = str(cfg.runtime.artifact_dir)
    payload["notion"]["token"] = ""
    payload["feishu"]["webhook_url"] = ""
    return payload


def _paper_inbox_base_schema() -> dict:
    return {
        "Title": {"title": {}},
        "Status": {
            "status": {
                "options": [
                    {"name": "New", "color": "default"},
                    {"name": "Selected", "color": "blue"},
                    {"name": "Deep Reading", "color": "yellow"},
                    {"name": "Deep Read Done", "color": "green"},
                    {"name": "Failed", "color": "red"},
                ]
            }
        },
        "Digest Summary": {"rich_text": {}},
        "Institutions": {"rich_text": {}},
        "Published Date": {"date": {}},
        "URL": {"url": {}},
        "Human Instruction": {"rich_text": {}},
        "Archive Review Status": {
            "select": {
                "options": [
                    {"name": "Auto Accepted", "color": "green"},
                    {"name": "Needs Human Review", "color": "yellow"},
                ]
            }
        },
        "Archive Confidence": {
            "select": {
                "options": [
                    {"name": "High", "color": "green"},
                    {"name": "Medium", "color": "yellow"},
                    {"name": "Low", "color": "red"},
                ]
            }
        },
        "Proposed Area": {"rich_text": {}},
        "Source": {
            "select": {
                "options": [
                    {"name": "arXiv", "color": "blue"},
                    {"name": "Hugging Face", "color": "orange"},
                ]
            }
        },
        "Error": {"rich_text": {}},
    }


def _paper_inbox_schema_with_relations(research_db_id: str, deep_db_id: str) -> dict:
    base = _paper_inbox_base_schema()
    return {
        "Title": base["Title"],
        "Status": base["Status"],
        "Research Areas": _relation_schema(research_db_id),
        "Digest Summary": base["Digest Summary"],
        "Institutions": base["Institutions"],
        "Published Date": base["Published Date"],
        "URL": base["URL"],
        "Human Instruction": base["Human Instruction"],
        "Deep Note": _relation_schema(deep_db_id),
        "Archive Review Status": base["Archive Review Status"],
        "Archive Confidence": base["Archive Confidence"],
        "Proposed Area": base["Proposed Area"],
        "Source": base["Source"],
        "Error": base["Error"],
    }


def _deep_notes_base_schema() -> dict:
    return {
        "Title": {"title": {}},
        "Reading Focus": {"rich_text": {}},
        "Contribution Type": {
            "select": {
                "options": [
                    {"name": "Method", "color": "blue"},
                    {"name": "System", "color": "green"},
                    {"name": "Benchmark", "color": "orange"},
                    {"name": "Survey", "color": "purple"},
                ]
            }
        },
        "Method Tags": {"multi_select": {}},
        "Review Status": {
            "select": {
                "options": [
                    {"name": "Draft", "color": "default"},
                    {"name": "Reviewed", "color": "green"},
                ]
            }
        },
    }


def _deep_notes_schema_with_relations(inbox_db_id: str, research_db_id: str) -> dict:
    base = _deep_notes_base_schema()
    return {
        "Title": base["Title"],
        "Paper": _relation_schema(inbox_db_id),
        "Research Areas": _relation_schema(research_db_id),
        "Reading Focus": base["Reading Focus"],
        "Contribution Type": base["Contribution Type"],
        "Method Tags": base["Method Tags"],
        "Review Status": base["Review Status"],
    }


def _research_areas_schema() -> dict:
    return {
        "Name": {"title": {}},
        "Aliases": {"rich_text": {}},
        "Description": {"rich_text": {}},
    }


def _relation_schema(database_id: str) -> dict:
    return {"relation": {"database_id": database_id, "type": "single_property", "single_property": {}}}
