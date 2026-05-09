from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstitutionCatalog:
    universities: dict[str, list[str]]
    labs: dict[str, list[str]]


def load_catalog(path: Path) -> InstitutionCatalog:
    data = json.loads(path.read_text(encoding="utf-8"))
    return InstitutionCatalog(
        universities={item["name"]: item["aliases"] for item in data["qs_top50_2026"]},
        labs={item["name"]: item["aliases"] for item in data["ai_labs"]},
    )


def find_matches(text: str, aliases_by_name: dict[str, list[str]]) -> list[str]:
    matches: list[str] = []
    for name, aliases in aliases_by_name.items():
        for alias in sorted(aliases, key=len, reverse=True):
            if is_unsafe_short_alias(alias):
                continue
            if alias_matches(text, alias):
                matches.append(name)
                break
    return sorted(set(matches))


def alias_matches(text: str, alias: str) -> bool:
    pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", re.IGNORECASE)
    return bool(pattern.search(text))


def is_unsafe_short_alias(alias: str) -> bool:
    unsafe = {"MIT", "AI", "ML"}
    return alias in unsafe

