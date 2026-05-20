from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import HuggingFaceConfig
from .models import DailyPaperRecord


def fetch_hf_daily_papers(date: str, cfg: HuggingFaceConfig) -> list[DailyPaperRecord]:
    query = urlencode({"date": date})
    request = Request(f"{cfg.endpoint}?{query}", headers={"User-Agent": "llm-paper-daily/1.0"})
    with urlopen(request, timeout=30) as response:
        raw = json.loads(response.read().decode("utf-8"))
    return normalize_hf_daily_papers(raw[: cfg.limit], run_date=date)


def normalize_hf_daily_papers(raw: list[dict], run_date: str) -> list[DailyPaperRecord]:
    records: list[DailyPaperRecord] = []
    for item in raw:
        paper = item.get("paper", item)
        paper_id = str(paper.get("id") or paper.get("paperId") or "").strip()
        if not paper_id:
            continue
        title = paper.get("title", "")
        summary = paper.get("summary", "")
        published = _date_only(paper.get("publishedAt", run_date))
        authors = []
        for author in paper.get("authors", []):
            if isinstance(author, dict) and author.get("name"):
                authors.append(author["name"])
            elif isinstance(author, str):
                authors.append(author)
        records.append(DailyPaperRecord(
            paper_id=f"hf:{paper_id}",
            source="HuggingFace",
            title=title,
            authors=authors,
            institutions="",
            abstract=summary,
            digest_summary=summary,
            summary_cn="",
            summary_en=summary,
            published_date=published,
            run_date=run_date,
            url=f"https://huggingface.co/papers/{paper_id}",
            pdf_url=f"https://arxiv.org/pdf/{paper_id}" if paper_id[:4].isdigit() else None,
            topic="huggingface-daily",
            score=float(item.get("numComments", 0)),
            signals={"hf_num_comments": item.get("numComments", 0)},
            provenance={"source": "huggingface_daily_papers"},
        ))
    return records


def _date_only(value: str) -> str:
    if "T" not in value:
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
