from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import CanonicalPaper


def summary_paths(record: CanonicalPaper) -> tuple[str, str]:
    month = record.date[:7]
    return (
        f"summary/{month}/{record.paper_id}.md",
        f"summary_en/{month}/{record.paper_id}.md",
    )


def render_cn_row(record: CanonicalPaper) -> str:
    summary_path, _ = summary_paths(record)
    date_obj = datetime.strptime(record.date, "%Y-%m-%d")
    date_str = f"<span style='display: inline-block; width: 42px;'>{date_obj.strftime('%m-%d')}</span>"
    abstract_link = f"**{record.title}**<br><sub>{record.render_excerpt}</sub>"
    paper_link = f"<div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)]({record.links['pdf'] or record.links['abs']})</div>"
    summary_link = f"<div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)]({summary_path}) "
    github_link = ""
    if record.links.get("github"):
        github_link = f"<div style='min-width:85px;'>[![GitHub](https://img.shields.io/badge/GitHub-View-brightgreen?logo=github)]({record.links['github']})</div>"
    return f"| {date_str} | {abstract_link}| {paper_link}{summary_link}{github_link} |\n"


def render_en_row(record: CanonicalPaper) -> str:
    _, summary_path = summary_paths(record)
    date_obj = datetime.strptime(record.date, "%Y-%m-%d")
    date_str = f"<span style='display: inline-block; width: 42px;'>{date_obj.strftime('%m-%d')}</span>"
    abstract_link = f"**{record.title}**<br><sub>{record.render_excerpt_en}</sub>"
    paper_link = f"<div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)]({record.links['pdf'] or record.links['abs']})</div>"
    summary_link = f"<div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)]({summary_path}) "
    github_link = ""
    if record.links.get("github"):
        github_link = f"<div style='min-width:85px;'>[![GitHub](https://img.shields.io/badge/GitHub-View-brightgreen?logo=github)]({record.links['github']})</div>"
    return f"| {date_str} | {abstract_link}| {paper_link}{summary_link}{github_link} |\n"


def render_cn_month_block(records: list[CanonicalPaper], month: str) -> str:
    year, month_number = month.split("-")
    month_label = f"{year}年{month_number}月"
    rows = "".join(render_cn_row(record) for record in sorted(records, key=lambda record: record.date, reverse=True))
    return (
        f"### {month_label}\n\n"
        "| &nbsp;Date&nbsp;&nbsp; | Paper | Links & Summary |\n"
        "| --- | --- | --- |\n"
        f"{rows}\n---\n"
    )


def render_en_month_block(records: list[CanonicalPaper], month: str) -> str:
    rows = "".join(render_en_row(record) for record in sorted(records, key=lambda record: record.date, reverse=True))
    return (
        f"## {month}\n\n"
        "| &nbsp;Date&nbsp; | Paper | Links & Summary |\n"
        "| --- | --- | --- |\n"
        f"{rows}\n---\n"
    )


def write_summary_files(repo_root: Path, records: list[CanonicalPaper]) -> None:
    for record in records:
        cn_path, en_path = summary_paths(record)
        cn_file = repo_root / cn_path
        en_file = repo_root / en_path
        cn_file.parent.mkdir(parents=True, exist_ok=True)
        en_file.parent.mkdir(parents=True, exist_ok=True)
        cn_file.write_text(record.summary_cn + "\n", encoding="utf-8")
        en_file.write_text(record.summary_en + "\n", encoding="utf-8")


def render_updates_block_zh(records: list[CanonicalPaper], *, now: datetime) -> str:
    lines = [
        "<details>",
        f"  <summary>查看更新文章 &nbsp;&nbsp;<sub>更新时间: {now.strftime('%Y年%m月%d日 %H:%M')}</sub></summary>",
        "<br>",
        "",
    ]
    for record in records:
        lines.append(f"- {record.title} ")
    lines.extend(["</details>"])
    return "\n".join(lines) + "\n"


def render_updates_block_en(records: list[CanonicalPaper], *, now: datetime) -> str:
    lines = [
        "<details>",
        f"  <summary>Click to view latest updates. &nbsp;&nbsp;<sub>Update time: {now.strftime('%Y-%m-%d %H:%M')}</sub></summary>",
        "<br>",
        "",
    ]
    for record in records:
        lines.append(f"- {record.title} ")
    lines.extend(["</details>"])
    return "\n".join(lines) + "\n"
