from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .config import NotionConfig
from .models import DailyPaperRecord, DeepNote, OperationResult, ReportModel, SelectedPaper
from .report import render_markdown_report


class NotionClient:
    def __init__(self, config: NotionConfig):
        self.config = config

    def create_database(self, *, parent_page_id: str, title: str, properties: dict) -> OperationResult:
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title[:2000]}}],
            "properties": properties,
        }
        if self.config.dry_run:
            return OperationResult(True, "dry_run", "database creation skipped in dry-run", payload)

        data = self._request("POST", "/databases", payload)
        return OperationResult(True, "created", "database created", data)

    def update_database(self, database_id: str, properties: dict) -> OperationResult:
        payload = {"properties": properties}
        if self.config.dry_run:
            return OperationResult(True, "dry_run", "database update skipped in dry-run", {"database_id": database_id, **payload})

        data = self._request("PATCH", f"/databases/{database_id}", payload)
        return OperationResult(True, "updated", "database updated", data)

    def find_database_in_parent(self, *, parent_page_id: str, title: str) -> dict | None:
        if self.config.dry_run:
            return None

        payload = {
            "query": title,
            "filter": {"property": "object", "value": "database"},
            "page_size": 50,
        }
        data = self._request("POST", "/search", payload)
        for result in data.get("results", []):
            if result.get("object") != "database":
                continue
            if result.get("parent", {}).get("page_id") != parent_page_id:
                continue
            titles = result.get("title", [])
            found = "".join(part.get("plain_text", "") for part in titles)
            if found == title:
                return result
        return None

    def build_paper_properties(self, record: DailyPaperRecord, *, include_workflow_defaults: bool = True) -> dict:
        properties = {
            "Title": _title(record.title),
            "Paper ID": _rich_text(record.paper_id),
            "Source": {"select": {"name": record.source}},
            "URL": {"url": record.url or None},
            "PDF URL": {"url": record.pdf_url},
            "Authors": _rich_text(", ".join(record.authors)),
            "Institutions": _rich_text(record.institutions),
            "Published Date": {"date": {"start": record.published_date}},
            "Run Date": {"date": {"start": record.run_date}},
            "Digest Summary": _rich_text(record.digest_summary),
            "Score": {"number": record.score},
        }
        if include_workflow_defaults:
            properties["Status"] = {"status": {"name": "New"}}
            properties["Error"] = {"rich_text": []}
        return properties

    def upsert_paper(self, record: DailyPaperRecord) -> OperationResult:
        if self.config.dry_run:
            return OperationResult(
                ok=True,
                status="dry_run",
                message="paper upsert skipped in dry-run",
                data={"paper_id": record.paper_id, "properties": self.build_paper_properties(record)},
            )

        existing_page_id = self._find_page_by_paper_id(record.paper_id)
        if existing_page_id:
            properties = self.build_paper_properties(record, include_workflow_defaults=False)
            data = self._request("PATCH", f"/pages/{existing_page_id}", {"properties": properties})
            return OperationResult(True, "updated", "paper updated", data)

        payload = {
            "parent": {"database_id": self.config.paper_inbox_database_id},
            "properties": self.build_paper_properties(record),
        }
        data = self._request("POST", "/pages", payload)
        return OperationResult(True, "created", "paper created", data)

    def create_daily_report(self, report: ReportModel, inbox_links: dict[str, str] | None = None) -> OperationResult:
        markdown = render_markdown_report(report, inbox_links=inbox_links or {})
        if self.config.dry_run:
            return OperationResult(True, "dry_run", "daily report skipped in dry-run", {"markdown": markdown})

        payload = {
            "parent": {"page_id": self.config.daily_report_parent_page_id},
            "properties": {"title": [{"text": {"content": report.title[:2000]}}]},
            "children": markdown_to_blocks(markdown),
        }
        data = self._request("POST", "/pages", payload)
        return OperationResult(True, "created", "daily report created", data)

    def query_selected_papers(self) -> list[SelectedPaper]:
        if self.config.dry_run:
            return []

        payload = {"filter": {"property": "Status", "status": {"equals": "Selected"}}}
        data = self._request("POST", f"/databases/{self.config.paper_inbox_database_id}/query", payload)
        return [selected_paper_from_page(page) for page in data.get("results", [])]

    def create_deep_note(self, paper: SelectedPaper, note: DeepNote, area_ids: list[str]) -> OperationResult:
        if self.config.dry_run:
            return OperationResult(True, "dry_run", "deep note skipped in dry-run", {"paper_id": paper.record.paper_id})

        payload = {
            "parent": {"database_id": self.config.deep_notes_database_id},
            "properties": {
                "Title": _title(note.title),
                "Paper": {"relation": [{"id": paper.notion_page_id}]},
                "Research Areas": {"relation": [{"id": area_id} for area_id in area_ids]},
                "Reading Focus": _rich_text(note.reading_focus),
                "Contribution Type": {"select": {"name": note.contribution_type}},
                "Method Tags": {"multi_select": [{"name": tag} for tag in note.method_tags]},
                "Review Status": {"select": {"name": "Draft"}},
            },
            "children": markdown_to_blocks(note.markdown),
        }
        data = self._request("POST", "/pages", payload)
        return OperationResult(True, "created", "deep note created", data)

    def update_paper_status(self, page_id: str, properties: dict) -> OperationResult:
        if self.config.dry_run:
            return OperationResult(
                True,
                "dry_run",
                "paper status skipped in dry-run",
                {"page_id": page_id, "properties": properties},
            )

        data = self._request("PATCH", f"/pages/{page_id}", {"properties": properties})
        return OperationResult(True, "updated", "paper status updated", data)

    def _find_page_by_paper_id(self, paper_id: str) -> str | None:
        payload = {"filter": {"property": "Paper ID", "rich_text": {"equals": paper_id}}}
        data = self._request("POST", f"/databases/{self.config.paper_inbox_database_id}/query", payload)
        results = data.get("results", [])
        if not results:
            return None
        return results[0]["id"]

    def _request(self, method: str, path: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self.config.api_base.rstrip("/") + path,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Notion-Version": self.config.api_version,
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Notion API {exc.code} {exc.reason}: {details}") from exc


def markdown_to_blocks(markdown: str) -> list[dict]:
    blocks: list[dict] = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            blocks.append(_block("heading_1", line[2:]))
        elif line.startswith("## "):
            blocks.append(_block("heading_2", line[3:]))
        elif line.startswith("- "):
            blocks.append(_block("bulleted_list_item", line[2:]))
        elif line.strip():
            blocks.append(_block("paragraph", line))
    return blocks[:100]


def selected_paper_from_page(page: dict) -> SelectedPaper:
    props = page.get("properties", {})
    authors = _plain_rich_text(props.get("Authors", {}))
    record = DailyPaperRecord(
        paper_id=_plain_rich_text(props.get("Paper ID", {})),
        source=_select_name(props.get("Source", {})),
        title=_plain_title(props.get("Title", {})),
        authors=authors.split(", ") if authors else [],
        institutions=_plain_rich_text(props.get("Institutions", {})),
        abstract="",
        digest_summary=_plain_rich_text(props.get("Digest Summary", {})),
        summary_cn="",
        summary_en="",
        published_date=_date_start(props.get("Published Date", {})),
        run_date=_date_start(props.get("Run Date", {})),
        url=props.get("URL", {}).get("url") or "",
        pdf_url=props.get("PDF URL", {}).get("url"),
        topic="",
        score=float(props.get("Score", {}).get("number") or 0),
        signals={},
        provenance={"source": "notion"},
    )
    return SelectedPaper(
        notion_page_id=page["id"],
        record=record,
        human_instruction=_plain_rich_text(props.get("Human Instruction", {})),
        existing_research_area_ids=[item["id"] for item in props.get("Research Areas", {}).get("relation", [])],
        existing_deep_note_id=_first_relation_id(props.get("Deep Note", {})),
    )


def _title(value: str) -> dict:
    return {"title": [{"text": {"content": value[:2000]}}]}


def _rich_text(value: str) -> dict:
    return {"rich_text": [{"text": {"content": value[:2000]}}]}


def _block(block_type: str, content: str) -> dict:
    return {
        "object": "block",
        "type": block_type,
        block_type: {"rich_text": [{"type": "text", "text": {"content": content[:2000]}}]},
    }


def _plain_title(prop: dict) -> str:
    return "".join(part.get("plain_text", "") for part in prop.get("title", []))


def _plain_rich_text(prop: dict) -> str:
    return "".join(part.get("plain_text", "") for part in prop.get("rich_text", []))


def _select_name(prop: dict) -> str:
    select = prop.get("select")
    return select.get("name", "") if select else ""


def _date_start(prop: dict) -> str:
    date = prop.get("date")
    return date.get("start", "") if date else ""


def _first_relation_id(prop: dict) -> str | None:
    relation = prop.get("relation", [])
    return relation[0]["id"] if relation else None
