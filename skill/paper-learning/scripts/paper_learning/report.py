from __future__ import annotations

from .models import DailyPaperRecord, ReportModel


def build_report(date: str, records: list[DailyPaperRecord]) -> ReportModel:
    topics = sorted({record.topic for record in records if record.topic})
    topic_text = ", ".join(topics) if topics else "mixed paper topics"
    overview = f"{len(records)} papers collected for {date}. Main topic signals: {topic_text}."
    return ReportModel(
        date=date,
        title=f"{date} Daily Paper Report",
        overview=overview,
        records=records,
    )


def render_markdown_report(report: ReportModel, inbox_links: dict[str, str] | None = None) -> str:
    inbox_links = inbox_links or {}
    lines = [f"# {report.title}", "", report.overview, ""]
    for index, record in enumerate(report.records, start=1):
        lines.extend([
            f"## {index}. {record.title}",
            "",
            f"- Paper ID: `{record.paper_id}`",
            f"- Source: {record.source}",
            f"- Authors: {', '.join(record.authors) if record.authors else 'Unknown'}",
            f"- Institutions: {record.institutions or 'Unknown'}",
            f"- Topic: {record.topic or 'Unknown'}",
            f"- Score: {record.score:g}",
            f"- Paper: {record.url}",
        ])
        if record.pdf_url:
            lines.append(f"- PDF: {record.pdf_url}")
        if record.paper_id in inbox_links:
            lines.append(f"- Notion Inbox: {inbox_links[record.paper_id]}")
        lines.extend(["", record.digest_summary or record.summary_en or record.abstract, ""])
    return "\n".join(lines).strip() + "\n"
