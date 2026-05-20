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
