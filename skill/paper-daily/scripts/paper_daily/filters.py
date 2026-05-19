from __future__ import annotations

import re

from .models import PaperCandidate

DEFAULT_KEYWORDS = ["Agent", "Agents", "LLM"]
DEFAULT_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "stat.ML", "cs.SE", "cs.MA"]

NOISE_RE = re.compile(
    r"\b(chemical agent|biological agent|contrast agent|infectious agent|oxidizing agent|reducing agent)\b",
    re.IGNORECASE,
)
LLM_RE = re.compile(r"\b(LLM|LLMs|large language model|large language models|language model|foundation model)\b", re.IGNORECASE)
AGENT_RE = re.compile(
    r"\b(agent|agents|multi-agent|tool[- ]?use|tool use|planning|autonomous|workflow|coding agent|agentic)\b",
    re.IGNORECASE,
)


def dedupe_by_priority(candidates: list[PaperCandidate]) -> list[PaperCandidate]:
    by_id: dict[str, PaperCandidate] = {}
    for candidate in candidates:
        existing = by_id.get(candidate.arxiv_id)
        if existing is None or candidate.keyword_rank < existing.keyword_rank:
            by_id[candidate.arxiv_id] = candidate
    return list(by_id.values())


def keep_candidate(candidate: PaperCandidate) -> bool:
    text = candidate.title + " " + candidate.abstract
    if NOISE_RE.search(text):
        return False
    return bool(AGENT_RE.search(text) or LLM_RE.search(text))


def has_llm_signal(candidate: PaperCandidate) -> bool:
    return bool(LLM_RE.search(candidate.title + " " + candidate.abstract))


def has_agent_signal(candidate: PaperCandidate) -> bool:
    return bool(AGENT_RE.search(candidate.title + " " + candidate.abstract))

