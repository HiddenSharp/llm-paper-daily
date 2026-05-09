from __future__ import annotations

import re

from .filters import has_agent_signal, has_llm_signal
from .institutions import InstitutionCatalog, find_matches
from .models import PaperCandidate


KEYWORD_SCORES = {
    "Agent": 3.0,
    "Agents": 2.6,
    "LLM": 1.6,
}

TITLE_AGENT_RE = re.compile(r"\b(agent|agents|multi-agent|coding agent|agentic)\b", re.IGNORECASE)
TITLE_LLM_RE = re.compile(r"\b(LLM|LLMs|large language model|language model)\b", re.IGNORECASE)
QUALITY_RE = re.compile(
    r"\b(benchmark|dataset|system|framework|evaluation|empirical|open-source|coding agent|tool calls?|real users?)\b",
    re.IGNORECASE,
)


def rank_candidates(candidates: list[PaperCandidate], catalog: InstitutionCatalog) -> list[PaperCandidate]:
    ranked: list[PaperCandidate] = []
    for candidate in candidates:
        score, reasons, universities, labs = score_candidate(candidate, catalog)
        candidate.score = score
        candidate.reasons = reasons
        candidate.institution_matches = universities
        candidate.lab_matches = labs
        ranked.append(candidate)
    return sorted(ranked, key=lambda item: (item.score, item.published), reverse=True)


def score_candidate(candidate: PaperCandidate, catalog: InstitutionCatalog) -> tuple[float, list[str], list[str], list[str]]:
    text = candidate.title + " " + candidate.abstract
    score = KEYWORD_SCORES.get(candidate.priority_keyword, 0.0)
    reasons = [f"keyword:{candidate.priority_keyword}"]

    if TITLE_AGENT_RE.search(candidate.title):
        score += 2.5
        reasons.append("title-agent")
    if TITLE_LLM_RE.search(candidate.title):
        score += 1.5
        reasons.append("title-llm")
    elif has_llm_signal(candidate):
        score += 0.8
        reasons.append("abstract-llm")

    if has_agent_signal(candidate) and has_llm_signal(candidate):
        score += 1.0
        reasons.append("agent+llm")

    if "cs.AI" in candidate.categories:
        score += 1.0
        reasons.append("cs.AI")
    if "cs.CL" in candidate.categories:
        score += 0.7
        reasons.append("cs.CL")
    if "cs.LG" in candidate.categories:
        score += 0.5
        reasons.append("cs.LG")

    universities = find_matches(text, catalog.universities)
    labs = find_matches(text, catalog.labs)
    if universities:
        score += 2.5
        reasons.append("qs-top50-signal")
    if labs:
        score += 2.5
        reasons.append("ai-lab-signal")

    if QUALITY_RE.search(text):
        score += 0.8
        reasons.append("quality-keyword")

    return round(score, 2), reasons, universities, labs

