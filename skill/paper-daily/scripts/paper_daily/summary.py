from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from .models import CanonicalPaper
from .pdf_preprocess import preprocess_pdf

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_MODEL = "qwen3.6-plus"
SUMMARY_PROMPT_PATH = Path(__file__).resolve().parents[2] / "references" / "summary_prompt_cn.txt"
OPENAI_SDK_FALLBACK_PATH = Path("/tmp/paper-daily-deps")

if OPENAI_SDK_FALLBACK_PATH.exists() and str(OPENAI_SDK_FALLBACK_PATH) not in sys.path:
    sys.path.insert(0, str(OPENAI_SDK_FALLBACK_PATH))

try:
    from openai import OpenAI
except Exception:  # optional dependency
    OpenAI = None


def candidate_to_canonical(candidate: dict, *, run_date: str) -> CanonicalPaper:
    pdf_result = preprocess_pdf(candidate.get("pdf_url"))
    institution_hint = extract_institution_from_first_page(pdf_result.first_page_text)
    paper_text = pdf_result.body_text
    summary_payload = summarize_with_dashscope(candidate, paper_text=paper_text, institution_hint=institution_hint)

    institution = clean(summary_payload.get("institution") or institution_hint or "")
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
            "provider": "dashscope-compatible",
            "model": DASHSCOPE_MODEL,
            "captured_at": run_date,
        },
        provenance={
            "institution": "dashscope|pdf-first-page-hint",
            "category_key": "fixed-v1-agent",
            "summary_cn": "dashscope",
            "summary_en": "dashscope",
            "github": "dashscope|none",
            "blog": "dashscope|none",
            "pdf_download": pdf_result.download_error or "ok",
            "pdf_extract": pdf_result.extract_error or "ok",
        },
    )


def summarize_with_dashscope(candidate: dict, *, paper_text: str | None, institution_hint: str | None) -> dict:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not set.")

    prompt_template = load_prompt_template()
    text_excerpt = (paper_text or candidate.get("abstract") or "").strip()
    if len(text_excerpt) > 4500:
        text_excerpt = text_excerpt[:4500] + "\n...[truncated]..."

    user_prompt = "\n\n".join(
        [
            prompt_template,
            "请额外输出英文版本总结，并且只返回严格 JSON，不要返回 markdown code fence。",
            'JSON schema: {"institution": string|null, "github": string|null, "blog": string|null, "summary_cn_markdown": string, "summary_en_markdown": string}',
            f"Title: {candidate.get('title', '')}",
            f"Authors: {', '.join(candidate.get('authors', []))}",
            f"Abstract: {candidate.get('abstract', '')}",
            f"Institution hint from PDF first page: {institution_hint or 'unknown'}",
            "Paper content excerpt:",
            text_excerpt,
        ]
    )

    try:
        if OpenAI is not None:
            client = OpenAI(
                api_key=api_key,
                base_url=DASHSCOPE_BASE_URL,
                timeout=180,
            )
            completion = client.chat.completions.create(
                model=DASHSCOPE_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert LLM paper analyst. "
                            "Return only valid JSON matching the requested schema. "
                            "Do not wrap the JSON in markdown fences. "
                            "Do not include chain-of-thought or source citation markers."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                extra_body={"enable_thinking": False},
            )
            content = completion.choices[0].message.content
        else:
            content = summarize_with_dashscope_http(api_key=api_key, user_prompt=user_prompt)
    except Exception as exc:
        raise RuntimeError(f"DashScope completion failed: {exc}") from exc

    parsed = parse_json_block(content)
    required = ["summary_cn_markdown", "summary_en_markdown"]
    for key in required:
        if not parsed.get(key):
            raise RuntimeError(f"DashScope response missing required field: {key}")
    return parsed


def parse_json_block(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content).strip()
        content = re.sub(r"```$", "", content).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def summarize_with_dashscope_http(*, api_key: str, user_prompt: str) -> str:
    body = {
        "model": DASHSCOPE_MODEL,
        "temperature": 0.2,
        "enable_thinking": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert LLM paper analyst. "
                    "Return only valid JSON matching the requested schema. "
                    "Do not wrap the JSON in markdown fences. "
                    "Do not include chain-of-thought or source citation markers."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
    }
    req = urllib.request.Request(
        DASHSCOPE_BASE_URL + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


def load_prompt_template() -> str:
    return SUMMARY_PROMPT_PATH.read_text(encoding="utf-8").strip()


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


def extract_institution_from_first_page(first_page: str | None) -> str | None:
    if not first_page:
        return None
    lines = [line.strip() for line in first_page.splitlines() if line.strip()]
    patterns = [
        r"(University[^,\n]*|Institute[^,\n]*|Laboratory[^,\n]*|Lab[^,\n]*|College[^,\n]*|Academy[^,\n]*|School[^,\n]*|AWS Agentic AI Labs[^,\n]*)",
        r"(Writer,\s*Inc\.[^,\n]*)",
        r"(National University of Singapore[^,\n]*)",
        r"(University of Maryland[^,\n]*)",
        r"(University of Michigan[^,\n]*)",
        r"(Tsinghua University[^,\n]*)",
    ]
    for line in lines[:20]:
        if "@" in line:
            continue
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return clean(match.group(1))
    return None


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
