"""Org-mode to Markdown converter for ljg-paper style deep notes.

Covers the Org subset used by ljg-paper notes:

- ``#+key: value`` document metadata headers (title/subtitle/authors/...).
- Heading levels ``*``, ``**``, ``***`` (no jumps).
- Inline single-star bold ``*bold*``.
- Image links ``[[file:relative/path.png]]`` and inline links ``[[url][text]]``.
- ``#+ATTR_ORG`` directives (dropped).
- ``#+begin_example`` / ``#+end_example`` example blocks.
- Unordered ``- `` and ordered ``1. `` lists.
- ASCII-art blocks wrapped in ```text fenced code.

The function intentionally does not try to be a general Org parser; it only
needs to round-trip what ljg-paper writes.
"""

from __future__ import annotations

import re

_META_RE = re.compile(r"^#\+([A-Za-z_]+):\s*(.*)$")
_HEADING_RE = re.compile(r"^(\*+)\s+(.*)$")
_FILE_LINK_RE = re.compile(r"\[\[file:([^\]]+)\]\]")
_LABELED_LINK_RE = re.compile(r"\[\[([^\]]+)\]\[([^\]]+)\]\]")
_BOLD_RE = re.compile(r"(?<![A-Za-z0-9_*])\*([^*\n]+?)\*(?![A-Za-z0-9_*])")

_KNOWN_META_KEYS = {
    "title",
    "subtitle",
    "date",
    "filetags",
    "identifier",
    "source",
    "authors",
    "venue",
}

_ASCII_ART_CHARS = set("+-|/\\><v^=~.:#[]()_,;!'\"`* ")
_REQUIRED_META_KEYS = ("title",)
_REQUIRED_TOP_LEVEL_HEADINGS = ("问题", "翻译", "核心概念", "洞见", "博导审稿", "启发")


def org_to_markdown(org_text: str) -> tuple[dict, str]:
    """Convert an ljg-paper style Org document to Markdown.

    Returns ``(metadata, markdown_body)`` where ``metadata`` is a dict of
    extracted ``#+key`` headers (lower-cased keys) and ``markdown_body`` is
    the converted body with metadata stripped.
    """

    lines = org_text.splitlines()
    metadata, body_lines = _split_metadata(lines)
    body_lines = _drop_attr_directives(body_lines)
    body_lines = _convert_example_blocks(body_lines)
    body_lines = _wrap_ascii_blocks(body_lines)
    converted = [_convert_line(line) for line in body_lines]
    markdown = "\n".join(converted).strip("\n") + "\n"
    return metadata, markdown


def validate_ljg_paper_org(org_text: str, fallback_metadata: dict | None = None) -> dict:
    """Validate the minimum contract paper-learning expects from ljg-paper.

    Returns the extracted metadata when valid. Raises ``ValueError`` with a
    human-readable message when the artifact is incomplete or malformed.
    """

    lines = org_text.splitlines()
    metadata, body_lines = _split_metadata(lines)

    merged_metadata = {**(fallback_metadata or {}), **metadata}
    missing_meta = [key for key in _REQUIRED_META_KEYS if not merged_metadata.get(key)]
    if missing_meta:
        raise ValueError(f"Missing required Org metadata: {', '.join(missing_meta)}")

    headings = _top_level_headings(body_lines)
    missing_headings = [heading for heading in _REQUIRED_TOP_LEVEL_HEADINGS if heading not in headings]
    if missing_headings:
        raise ValueError(f"Missing required top-level sections: {', '.join(missing_headings)}")

    if "**" in org_text:
        raise ValueError("Org artifact contains Markdown-style bold '**'; ljg-paper output must use single-star Org bold.")

    return merged_metadata


def _split_metadata(lines: list[str]) -> tuple[dict, list[str]]:
    metadata: dict[str, str] = {}
    body_start = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            body_start = index + 1
            continue
        match = _META_RE.match(stripped)
        if not match:
            body_start = index
            break
        key = match.group(1).lower()
        value = match.group(2).strip()
        if key in _KNOWN_META_KEYS or key.startswith("html_") or key.startswith("attr_"):
            metadata[key] = value
            body_start = index + 1
        else:
            metadata[key] = value
            body_start = index + 1
    return metadata, lines[body_start:]


def _drop_attr_directives(lines: list[str]) -> list[str]:
    return [line for line in lines if not line.lstrip().lower().startswith("#+attr_")]


def _convert_example_blocks(lines: list[str]) -> list[str]:
    output: list[str] = []
    in_example = False
    for line in lines:
        stripped = line.strip().lower()
        if stripped == "#+begin_example":
            if not in_example:
                output.append("```text")
                in_example = True
            continue
        if stripped == "#+end_example":
            if in_example:
                output.append("```")
                in_example = False
            continue
        output.append(line)
    if in_example:
        output.append("```")
    return output


def _top_level_headings(lines: list[str]) -> list[str]:
    headings: list[str] = []
    for line in lines:
        match = _HEADING_RE.match(line)
        if not match:
            continue
        if len(match.group(1)) == 1:
            headings.append(match.group(2).strip())
    return headings


def _wrap_ascii_blocks(lines: list[str]) -> list[str]:
    """Wrap runs of ASCII-art looking lines in ``` fences.

    A line is considered art-eligible if either:

    - every non-space character is in ``_ASCII_ART_CHARS`` and it contains at
      least one drawing glyph (strict art), or
    - it contains a drawing glyph and the line above OR below is strict art
      (bridging label rows like ``| node |`` inside a box).

    Runs of >=2 art-eligible lines are wrapped in a ``` fenced block.
    """

    drawing_glyphs = set("+|/\\<>^v=")

    def strict_art(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        if not any(ch in drawing_glyphs for ch in stripped):
            return False
        return all(ch in _ASCII_ART_CHARS for ch in stripped)

    def has_drawing(line: str) -> bool:
        stripped = line.strip()
        return bool(stripped) and any(ch in drawing_glyphs for ch in stripped)

    n = len(lines)
    art_flag = [False] * n
    in_fence = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if strict_art(line):
            art_flag[i] = True
    # Bridge: a line with a drawing glyph adjacent to strict art also counts.
    in_fence = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if art_flag[i]:
            continue
        if not has_drawing(line):
            continue
        prev_strict = i > 0 and strict_art(lines[i - 1])
        next_strict = i + 1 < n and strict_art(lines[i + 1])
        if prev_strict or next_strict:
            art_flag[i] = True

    output: list[str] = []
    i = 0
    while i < n:
        if not art_flag[i]:
            output.append(lines[i])
            i += 1
            continue
        j = i
        while j < n and art_flag[j]:
            j += 1
        run = lines[i:j]
        if len(run) >= 2:
            output.append("```text")
            output.extend(run)
            output.append("```")
        else:
            output.extend(run)
        i = j
    return output


def _convert_line(line: str) -> str:
    if line.startswith("```"):
        return line
    heading = _HEADING_RE.match(line)
    if heading:
        level = len(heading.group(1))
        text = heading.group(2).strip()
        # Map Org level n -> Markdown level n+1, capped at h6.
        md_level = min(level + 1, 6)
        return f"{'#' * md_level} {_convert_inline(text)}"
    return _convert_inline(line)


def _convert_inline(text: str) -> str:
    text = _LABELED_LINK_RE.sub(lambda m: f"[{m.group(2)}]({m.group(1)})", text)
    text = _FILE_LINK_RE.sub(lambda m: f"![]({m.group(1)})", text)
    text = _BOLD_RE.sub(lambda m: f"**{m.group(1)}**", text)
    return text
