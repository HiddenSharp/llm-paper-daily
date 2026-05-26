from __future__ import annotations

import json
from pathlib import Path

from .models import DeepReadingRequest, SelectedPaper


def load_selected_papers(path: str | Path) -> list[SelectedPaper]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [SelectedPaper.from_dict(item) for item in payload.get("selected_papers", [])]


def dump_selected_papers(path: str | Path, papers: list[SelectedPaper]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"selected_papers": [paper.to_dict() for paper in papers]}
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def load_deep_reading_request(path: str | Path) -> DeepReadingRequest:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return DeepReadingRequest.from_dict(payload)


def dump_deep_reading_request(path: str | Path, request: DeepReadingRequest) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(request.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


class LocalSelectedPapersNotion:
    def __init__(self, papers: list[SelectedPaper]):
        self._papers = papers
        self.status_updates: list[dict] = []
        self.note_creates: list[dict] = []
        self._next_note_id = 1

    def query_selected_papers(self) -> list[SelectedPaper]:
        return list(self._papers)

    def update_paper_status(self, page_id: str, properties: dict):
        from .models import OperationResult

        self.status_updates.append({"page_id": page_id, "properties": properties})
        return OperationResult(True, "dry_run", "local selected paper status updated", {"page_id": page_id})

    def create_deep_note(self, paper: SelectedPaper, note, area_ids: list[str]):
        from .models import OperationResult

        note_id = paper.existing_deep_note_id or f"local-note-{self._next_note_id}"
        if not paper.existing_deep_note_id:
            self._next_note_id += 1
        self.note_creates.append({
            "paper_id": paper.record.paper_id,
            "note_id": note_id,
            "area_ids": list(area_ids),
            "note": note.to_dict(),
        })
        return OperationResult(True, "dry_run", "local selected paper deep note created", {"id": note_id})
