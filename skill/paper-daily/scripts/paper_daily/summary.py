from __future__ import annotations

import json
import re
from pathlib import Path

from .defaults import DEFAULT_SUMMARY_ARTIFACT_DIR
from .models import CanonicalPaper


def candidate_to_canonical(candidate: dict, *, run_date: str, summary_artifact_dir: str | Path = DEFAULT_SUMMARY_ARTIFACT_DIR) -> CanonicalPaper:
    summary_payload = load_summary_payload(summary_artifact_dir, candidate["arxiv_id"])

    institution = clean(summary_payload.get("institution") or "")
    category_key = "agent"
    category_alias = candidate.get("priority_keyword", "Agent")
    category_display = {"zh": "Agent", "en": "Agent"}
    summary_cn_markdown = normalize_summary_markdown(clean_markdown(summary_payload["summary_cn_markdown"]), lang="zh")
    summary_en_markdown = normalize_summary_markdown(clean_markdown(summary_payload["summary_en_markdown"]), lang="en")
    summary_cn_excerpt = extract_summary_excerpt(summary_cn_markdown, lang="zh")
    summary_en_excerpt = extract_summary_excerpt(summary_en_markdown, lang="en")
    if institution:
        summary_cn_excerpt = f"机构: {institution}<br>{summary_cn_excerpt}"
        summary_en_excerpt = f"Institution: {institution}<br>{summary_en_excerpt}"

    provider = clean(summary_payload.get("provider") or "agent-skill-artifact")
    model = clean(summary_payload.get("model") or "external-skill")

    return CanonicalPaper(
        schema_version="v1",
        paper_id=candidate["arxiv_id"],
        date=run_date,
        title=candidate["title"],
        authors=candidate.get("authors", []),
        abstract=candidate.get("abstract", ""),
        links={
            "abs": candidate.get("abs_url"),
            "pdf": candidate.get("pdf_url"),
            "github": summary_payload.get("github"),
            "blog": summary_payload.get("blog"),
        },
        institution=institution or None,
        category_key=category_key,
        category_alias=category_alias,
        category_display=category_display,
        summary_cn=summary_cn_markdown,
        summary_en=summary_en_markdown,
        render_excerpt=summary_cn_excerpt,
        render_excerpt_en=summary_en_excerpt,
        source_discovery={
            "source": "arxiv",
            "query": candidate.get("priority_keyword", ""),
            "captured_at": candidate.get("published", ""),
        },
        source_summary={
            "provider": provider,
            "model": model,
            "captured_at": run_date,
        },
        provenance={
            "institution": "summary-artifact",
            "category_key": "fixed-v1-agent",
            "summary_cn": "summary-artifact",
            "summary_en": "summary-artifact",
            "github": "summary-artifact|none",
            "blog": "summary-artifact|none",
        },
    )


def summary_artifact_path(base_dir: str | Path, paper_id: str) -> Path:
    return Path(base_dir) / f"{paper_id}.json"


def build_summary_runtime_request(candidate: dict, *, run_date: str, artifact_dir: str | Path = DEFAULT_SUMMARY_ARTIFACT_DIR) -> dict:
    path = summary_artifact_path(artifact_dir, candidate["arxiv_id"])
    return {
        "run_date": run_date,
        "paper": candidate,
        "summary_artifact_path": str(path),
        "expected_schema": {
            "institution": "string|null",
            "github": "string|null",
            "blog": "string|null",
            "summary_cn_markdown": "string",
            "summary_en_markdown": "string",
            "provider": "string|null",
            "model": "string|null",
        },
        "agent_instruction": (
            "Use the paper-daily skill and the current conversation context to read this paper and write "
            "a strict JSON summary artifact to summary_artifact_path. Do not call a fixed in-script model "
            "workflow. Return bilingual markdown summaries and optional institution/github/blog fields."
        ),
    }


def load_summary_payload(base_dir: str | Path, paper_id: str) -> dict:
    path = summary_artifact_path(base_dir, paper_id)
    if not path.exists():
        raise FileNotFoundError(
            f"Missing summary artifact for {paper_id}: {path}. "
            "Prepare the request with prepare_summary_requests.py and generate the artifact with the paper-daily skill."
        )
    payload = parse_json_block(path.read_text(encoding="utf-8"))
    required = ["summary_cn_markdown", "summary_en_markdown"]
    for key in required:
        if not payload.get(key):
            raise RuntimeError(f"Summary artifact missing required field: {key} ({path})")
    return payload


def validate_summary_artifacts(base_dir: str | Path, paper_ids: list[str]) -> list[dict]:
    results: list[dict] = []
    for paper_id in paper_ids:
        path = summary_artifact_path(base_dir, paper_id)
        try:
            load_summary_payload(base_dir, paper_id)
            results.append({"paper_id": paper_id, "ok": True, "path": str(path)})
        except Exception as exc:
            results.append({"paper_id": paper_id, "ok": False, "path": str(path), "error": str(exc)})
    return results


def parse_json_block(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content).strip()
        content = re.sub(r"```$", "", content).strip()
    content = repair_json_escapes(content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            raise
        return json.loads(repair_json_escapes(match.group(0)))


def repair_json_escapes(content: str) -> str:
    return re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", content)


def extract_summary_excerpt(markdown_text: str, *, lang: str) -> str:
    if lang == "zh":
        pattern = r"####\s*总结\s*\n+(.*)"
    else:
        pattern = r"####\s*Summary\s*\n+(.*)"
    match = re.search(pattern, markdown_text, re.S)
    if not match:
        return first_sentences(clean(markdown_text), 3)
    excerpt = match.group(1).strip()
    return first_sentences(clean(excerpt), 3)


def first_sentences(text: str, count: int) -> str:
    parts = re.split(r"(?<=[.!?。])\s+", text.strip())
    return " ".join(part for part in parts[:count] if part)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_markdown(text: str) -> str:
    return text.strip().replace("\r\n", "\n")


def normalize_summary_markdown(text: str, *, lang: str) -> str:
    if lang == "zh":
        replacements = [
            (r"^##\s*1\.\s*文章做了什么", "## 文章做了什么"),
            (r"^##\s*2\.\s*文章的核心贡献点", "## 文章的核心贡献点"),
            (r"^##\s*3\.\s*实现与部署.*", "## 实现与部署，evaluation 结果，要有和相关工作对比"),
            (r"^##\s*4\.\s*总结", "#### 总结"),
        ]
    else:
        replacements = [
            (r"^##\s*1\.\s*What This Paper Does", "## What This Paper Does"),
            (r"^##\s*2\.\s*Core Contributions", "## Core Contributions"),
            (r"^##\s*3\.\s*Implementation.*", "## Implementation and Evaluation"),
            (r"^##\s*4\.\s*Summary", "#### Summary"),
        ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.M)
    return text
