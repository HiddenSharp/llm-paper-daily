from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class DailyPaperRecord:
    paper_id: str
    source: str
    title: str
    authors: list[str]
    institutions: str
    abstract: str
    digest_summary: str
    summary_cn: str
    summary_en: str
    published_date: str
    run_date: str
    url: str
    pdf_url: str | None
    topic: str
    score: float
    signals: dict
    provenance: dict

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "DailyPaperRecord":
        return cls(
            paper_id=payload["paper_id"],
            source=payload["source"],
            title=payload["title"],
            authors=list(payload.get("authors", [])),
            institutions=payload.get("institutions", ""),
            abstract=payload.get("abstract", ""),
            digest_summary=payload.get("digest_summary", ""),
            summary_cn=payload.get("summary_cn", ""),
            summary_en=payload.get("summary_en", ""),
            published_date=payload.get("published_date", ""),
            run_date=payload.get("run_date", ""),
            url=payload.get("url", ""),
            pdf_url=payload.get("pdf_url"),
            topic=payload.get("topic", ""),
            score=float(payload.get("score", 0.0)),
            signals=dict(payload.get("signals", {})),
            provenance=dict(payload.get("provenance", {})),
        )


@dataclass(frozen=True)
class ReportModel:
    date: str
    title: str
    overview: str
    records: list[DailyPaperRecord]

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "title": self.title,
            "overview": self.overview,
            "records": [record.to_dict() for record in self.records],
        }


@dataclass(frozen=True)
class ResearchArea:
    name: str
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    notion_page_id: str | None = None

    def matches(self, text: str) -> bool:
        normalized = text.casefold()
        names = [self.name, *self.aliases]
        return any(value.casefold() in normalized for value in names if value)


@dataclass(frozen=True)
class SelectedPaper:
    notion_page_id: str
    record: DailyPaperRecord
    human_instruction: str
    existing_research_area_ids: list[str] = field(default_factory=list)
    existing_deep_note_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "notion_page_id": self.notion_page_id,
            "record": self.record.to_dict(),
            "human_instruction": self.human_instruction,
            "existing_research_area_ids": list(self.existing_research_area_ids),
            "existing_deep_note_id": self.existing_deep_note_id,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "SelectedPaper":
        return cls(
            notion_page_id=payload["notion_page_id"],
            record=DailyPaperRecord.from_dict(payload["record"]),
            human_instruction=payload.get("human_instruction", ""),
            existing_research_area_ids=list(payload.get("existing_research_area_ids", [])),
            existing_deep_note_id=payload.get("existing_deep_note_id"),
        )


@dataclass(frozen=True)
class DeepReadingRequest:
    date: str
    selector_type: str
    candidate_source: str
    resolved_paper_ids: list[str]
    human_instruction: str
    trigger_source: str
    requires_confirmation: bool
    confirmed: bool = False
    selected_papers: list[SelectedPaper] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "selector_type": self.selector_type,
            "candidate_source": self.candidate_source,
            "resolved_paper_ids": list(self.resolved_paper_ids),
            "human_instruction": self.human_instruction,
            "trigger_source": self.trigger_source,
            "requires_confirmation": self.requires_confirmation,
            "confirmed": self.confirmed,
            "selected_papers": [paper.to_dict() for paper in self.selected_papers],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "DeepReadingRequest":
        return cls(
            date=payload["date"],
            selector_type=payload["selector_type"],
            candidate_source=payload["candidate_source"],
            resolved_paper_ids=list(payload.get("resolved_paper_ids", [])),
            human_instruction=payload.get("human_instruction", ""),
            trigger_source=payload.get("trigger_source", "chat_manual"),
            requires_confirmation=bool(payload.get("requires_confirmation", False)),
            confirmed=bool(payload.get("confirmed", False)),
            selected_papers=[SelectedPaper.from_dict(item) for item in payload.get("selected_papers", [])],
        )


@dataclass(frozen=True)
class DeepNote:
    title: str
    paper_id: str
    reading_focus: str
    markdown: str
    contribution_type: str
    method_tags: list[str]
    proposed_area: str
    archive_confidence: str
    extra_properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ClassificationResult:
    area_ids: list[str]
    proposed_area: str
    confidence: str
    review_status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class OperationResult:
    ok: bool
    status: str
    message: str
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
