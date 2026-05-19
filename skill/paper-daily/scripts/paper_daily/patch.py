from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


README_START = "<!-- paper-daily:readme:months:start -->"
README_END = "<!-- paper-daily:readme:months:end -->"
README_EN_START = "<!-- paper-daily:readme-en:months:start -->"
README_EN_END = "<!-- paper-daily:readme-en:months:end -->"
UPDATES_START = "<!-- paper-daily:readme:updates:start -->"
UPDATES_END = "<!-- paper-daily:readme:updates:end -->"
UPDATES_EN_START = "<!-- paper-daily:readme-en:updates:start -->"
UPDATES_EN_END = "<!-- paper-daily:readme-en:updates:end -->"


def ensure_readme_markers(repo_root: Path) -> None:
    ensure_readme_markers_zh(repo_root / "README.md")
    ensure_readme_markers_en(repo_root / "README_en.md")


def ensure_readme_markers_zh(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = remove_qrcode_and_community_copy(text)
    month_start_anchor = "## 最新论文"
    star_anchor = "## Star History"
    updates_start_anchor = "<details>"
    updates_end_anchor = "</details>"
    if UPDATES_START not in text and updates_start_anchor in text and updates_end_anchor in text:
        before, after = text.split(updates_start_anchor, 1)
        updates_body, tail = after.split(updates_end_anchor, 1)
        replacement = (
            f"{UPDATES_START}\n"
            f"{updates_start_anchor}{updates_body}{updates_end_anchor}\n"
            f"{UPDATES_END}"
        )
        text = before + replacement + tail
    if README_START not in text:
        before, after = text.split(month_start_anchor, 1)
        month_content, star = after.split(star_anchor, 1)
        month_content = month_content.lstrip("\n")
        replacement = (
            f"{month_start_anchor}\n\n"
            f"{README_START}\n"
            f"{month_content.rstrip()}\n"
            f"{README_END}\n\n"
            f"{star_anchor}{star}"
        )
        text = before + replacement
    path.write_text(text, encoding="utf-8")


def ensure_readme_markers_en(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    updates_start_anchor = "<details>"
    updates_end_anchor = "</details>"
    if UPDATES_EN_START not in text and updates_start_anchor in text and updates_end_anchor in text:
        before, after = text.split(updates_start_anchor, 1)
        updates_body, tail = after.split(updates_end_anchor, 1)
        replacement = (
            f"{UPDATES_EN_START}\n"
            f"{updates_start_anchor}{updates_body}{updates_end_anchor}\n"
            f"{UPDATES_EN_END}"
        )
        text = before + replacement + tail
    first_month = re.search(r"^## \d{4}-\d{2}$", text, re.MULTILINE)
    if first_month and README_EN_START not in text:
        idx = first_month.start()
        prefix = text[:idx].rstrip() + "\n\n"
        month_content = text[idx:].lstrip()
        text = prefix + README_EN_START + "\n" + month_content.rstrip() + "\n" + README_EN_END + "\n"
    path.write_text(text, encoding="utf-8")


def update_readme_timestamps(path: Path, *, locale: str, now: datetime) -> None:
    text = path.read_text(encoding="utf-8")
    if locale == "zh":
        badge = now.strftime("%m.%d_%H:%M")
        details = now.strftime("%Y年%m月%d日 %H:%M")
        text = re.sub(
            r"status-Update_[0-9]{2}\.[0-9]{2}_[0-9]{2}:[0-9]{2}-success\.svg",
            f"status-Update_{badge}-success.svg",
            text,
        )
        text = re.sub(
            r"更新时间: (?:[0-9]{4}年)?[0-9]{2}月[0-9]{2}日 [0-9]{2}:[0-9]{2}",
            f"更新时间: {details}",
            text,
        )
    else:
        badge = now.strftime("%m.%d_%H:%M")
        details = now.strftime("%Y-%m-%d %H:%M")
        text = re.sub(
            r"status-Update_[0-9]{2}\.[0-9]{2}_[0-9]{2}:[0-9]{2}-success\.svg",
            f"status-Update_{badge}-success.svg",
            text,
        )
        text = re.sub(
            r"Update time: (?:[0-9]{4}-)?[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}",
            f"Update time: {details}",
            text,
        )
    path.write_text(text, encoding="utf-8")


def patch_updates_block(path: Path, start_marker: str, end_marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise RuntimeError(f"Missing or invalid update markers in {path.name}")
    new_text = text[: start_idx + len(start_marker)] + "\n" + block.strip("\n") + "\n" + text[end_idx:]
    path.write_text(new_text, encoding="utf-8")


def patch_month_block(path: Path, start_marker: str, end_marker: str, month_block: str, *, month_key: str, paper_id: str) -> None:
    text = path.read_text(encoding="utf-8")
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise RuntimeError(f"Missing or invalid markers in {path.name}")
    body = text[start_idx + len(start_marker):end_idx]
    patched_body = inject_month_block(body, month_block, month_key, paper_id=paper_id)
    new_text = text[: start_idx + len(start_marker)] + "\n" + patched_body.strip("\n") + "\n" + text[end_idx:]
    path.write_text(new_text, encoding="utf-8")


def remove_qrcode_and_community_copy(text: str) -> str:
    text = re.sub(r"🌈 \*\*交流学习:\*\*.*?\n\n", "", text, flags=re.S)
    text = re.sub(r"<img src='\./qrcode\.JPG'.*?>\n\n", "", text)
    return text


def inject_month_block(existing_body: str, month_block: str, month_key: str, *, paper_id: str) -> str:
    lines = existing_body.strip("\n")
    if not lines:
        return month_block.strip() + "\n"

    year, month_number = month_key.split("-")
    header_cn = f"### {year}年{month_number}月"
    header_en = f"## {month_key}"

    if header_cn in lines:
        if f"summary/{month_key}/" not in existing_body:
            return month_block.strip() + "\n\n" + lines + "\n"
        return insert_row_into_existing_month(lines, month_block, header_cn, paper_id=paper_id)
    if header_en in lines:
        return insert_row_into_existing_month(lines, month_block, header_en, paper_id=paper_id)

    return month_block.strip() + "\n\n" + lines + "\n"


def insert_row_into_existing_month(existing_body: str, month_block: str, month_header: str, *, paper_id: str) -> str:
    new_lines = month_block.strip().splitlines()
    existing_lines = existing_body.splitlines()
    row_lines = [line for line in new_lines if line.startswith("| <span")]
    if not row_lines:
        return existing_body

    header_idx = existing_lines.index(month_header)
    insert_after = None
    for idx in range(header_idx, min(len(existing_lines), header_idx + 6)):
        if existing_lines[idx].startswith("| ---"):
            insert_after = idx
            break
    if insert_after is None:
        return existing_body

    for offset, row_line in enumerate(row_lines, start=1):
        row_paper_id = row_dedupe_key(row_line)
        replaced = False
        for idx, existing_line in enumerate(existing_lines):
            if row_paper_id in existing_line:
                existing_lines[idx] = row_line
                replaced = True
                break
        if not replaced and row_line not in existing_lines:
            existing_lines.insert(insert_after + offset, row_line)
    return sort_month_rows(existing_lines, header_idx)


def sort_month_rows(existing_lines: list[str], header_idx: int) -> str:
    separator_idx = None
    for idx in range(header_idx + 1, len(existing_lines)):
        if existing_lines[idx].strip() == "---":
            separator_idx = idx
            break
    if separator_idx is None:
        return "\n".join(existing_lines)

    row_indices = [idx for idx in range(header_idx + 1, separator_idx) if existing_lines[idx].startswith("| <span")]
    sorted_rows = sorted((existing_lines[idx] for idx in row_indices), key=row_sort_key, reverse=True)
    unique_rows: list[str] = []
    seen_keys: set[str] = set()
    for row in sorted_rows:
        dedupe_key = row_dedupe_key(row)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        unique_rows.append(row)

    for idx, row in zip(row_indices, unique_rows):
        existing_lines[idx] = row
    for idx in reversed(row_indices[len(unique_rows):]):
        del existing_lines[idx]
    return "\n".join(existing_lines)


def row_sort_key(row_line: str) -> tuple[int, int, int]:
    month_day_match = re.search(r">(\d{2})-(\d{2})</span>", row_line)
    year_month_match = re.search(r"summary(?:_en)?/(\d{4})-(\d{2})/", row_line)
    if not month_day_match or not year_month_match:
        return (0, 0, 0)
    year = int(year_month_match.group(1))
    month = int(year_month_match.group(2))
    day = int(month_day_match.group(2))
    return (year, month, day)


def row_dedupe_key(row_line: str) -> str:
    paper_id_match = re.search(r"summary(?:_en)?/\d{4}-\d{2}/([^.)/]+)\.md", row_line)
    if paper_id_match:
        return paper_id_match.group(1)
    return row_line
