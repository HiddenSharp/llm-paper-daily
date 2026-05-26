---
name: paper-daily
description: Recall daily arXiv papers for LLM/Agent topics, rank candidates with keyword and institution filters, and prepare a broad candidate list for downstream review or publishing workflows.
---

# Paper Daily

Use this skill when you want broad daily recall of LLM/Agent papers from arXiv. The default goal is coverage first, not deep reading.

## Preference Profile
When judging recalled papers, prioritize the user's taste over generic paper quality.

- Strong interests: `Agentic RL`, `Rubric`, `Agents`, `On-Policy Distillation`, `Reasoning`, `Reinforcement Learning`, `Benchmark`, `Synthetic Data Generation`
- Secondary interests: agent workflows, multi-agent systems, memory, tool use, skill learning, evaluation, and agent infrastructure
- Prefer papers that are technically concrete, empirically grounded, or benchmark-oriented
- Keep technical reports and major-lab papers unless they are clearly off-taste or too weak to justify inclusion
- Aim for a final daily list of about `20` papers unless the user asks otherwise.
- Use `50` arXiv results per priority keyword by default so daily recall is coverage-oriented.

## Workflow

1. Discover candidates from arXiv by priority keywords: `Agent`, `Agents`, then `LLM`.
2. Query target categories such as `cs.AI`, `cs.CL`, `cs.LG`, `stat.ML`, `cs.SE`, and `cs.MA`.
3. Dedupe by normalized arXiv id without version suffix.
4. Filter obvious noise such as chemical/biological/contrast agents.
5. Rank candidates with:
   - keyword priority
   - title/abstract Agent or LLM signals
   - category signals
   - institution signals from QS Top 50 universities and known AI labs/companies
6. Return a ranked candidate list, usually around `20` recommended papers for one day when arXiv supply allows.
7. After recall, use the current conversation model to judge papers from `title + abstract` against the user's taste profile and narrow the list to the final daily set.
8. After the final paper list is selected, prepare external summary requests and use the runtime skill context to generate the bilingual summary artifacts.
9. Use `run_daily.py` only when the summary artifacts already exist and you explicitly want repo publishing artifacts such as feed updates and README patches.

## Stage Boundaries

- `discover.py` is recall-only. It queries arXiv metadata, ranks candidates, writes a lightweight discovery artifact, and does not require model credentials.
- `prepare_summary_requests.py` prepares external summary-artifact requests for the runtime skill. The actual LLM work should happen outside the local scripts, using skill context instead of a fixed in-script model workflow.
- `run_daily.py` and `generate_feed.py` are publishing/canonicalization workflows. They consume summary artifacts that were generated externally and adapt them into repo feed records.
- `--view-only` prevents repository writes, but it still requires the summary artifacts because it validates the canonical publishing path.
- If the goal is only to test arXiv recall or Notion orchestration without summaries, do not use `run_daily.py`; use `discover.py` or the `paper-learning --skip-summary` path.

## Output Contract
The skill should produce two outputs in sequence:

1. `Paper list`
   - around `20` papers by default
   - include arXiv ID, title, link, date, and inferred keywords
2. `Report`
   - a bilingual report based on the selected paper list
   - include a short batch overview, then per-paper entries
   - do not expose internal filtering, ranking, or selection criteria in the report

## Report Format
After the paper list, write the report in concise Markdown with:

### 1. Batch Overview
- Summarize the dominant themes in the selected batch
- State the practical reading value of the batch
- Keep this section short

### 2. Per-Paper Entries
For each selected paper, include:

1. Paper title
2. Authors and venue/source
3. Link(s) and date
4. Chinese review, around `200-300` Chinese words
5. English review in concise academic prose
6. Metadata table with semantic keywords, not raw arXiv categories
7. Appendix when useful, such as code, project page, benchmark relevance, or related papers

## Writing Guidance
- The report is reader-facing. Do not mention filtering standards, ranking rules, taste profile, score logic, or why a paper was selected.
- The report should still be analytical, not just a list rewrite.
- Borrow the paper-summary style, but simplify it for abstract-level evidence: background -> concrete problem -> what the paper does -> method shape -> reported evidence.
- Adapt that style to abstract-level evidence; do not write as if the full paper was read.
- Prefer compact, evidence-based writing over template-heavy praise.
- Use `title + abstract + categories + institution hints` as the main basis for judgment, but surface semantic keywords instead of raw arXiv categories in the report.
- Do not pretend full-paper certainty when only abstract-level evidence is available.
- The Chinese review should cover: background, challenge, what the paper does, core method, and reported evidence. Do not force limitations unless the abstract explicitly states a constraint.
- The English review should be concise, factual, and non-formulaic.
- The metadata table should include fields such as: arXiv ID, keywords, authors, institution hints, code availability, and source/date.
- Infer `keywords` from the paper topic using concise labels such as `Agent`, `RL`, `Benchmark`, `Reasoning`, `Synthetic Data`, `Evaluation`, `Distillation`, `Tool Use`, or `Multimodal`.
- Keep the batch overview short so most of the output budget goes to the selected papers.
- Avoid generic motivation such as "LLMs are important." Start from the technical baseline or task setting.
- Do not copy abstract sentences verbatim. Reframe the paper in your own words.
- If the abstract reports numbers, include the headline numbers and baseline context. If it does not, say the result evidence is not visible from the abstract.

## Commands

Run a real arXiv dry-run for a UTC submitted date:

```bash
python3 skill/paper-daily/scripts/discover.py --date YYYY-MM-DD
```

Write JSON output:

```bash
python3 skill/paper-daily/scripts/discover.py --date YYYY-MM-DD --json --out /tmp/papers.json
```

By default, discovery results are also saved to:

```text
skill/paper-daily/output/discovered-YYYY-MM-DD.json
```

Ask for deeper retrieval explicitly:

```bash
python3 skill/paper-daily/scripts/discover.py --date YYYY-MM-DD --max-results-per-keyword 50 --select 20
```

For local testing with fewer requests or a narrower sample:

```bash
python3 skill/paper-daily/scripts/discover.py --date YYYY-MM-DD --max-results-per-keyword 10 --select 20
```

Prepare external summary requests for the selected papers:

```bash
python3 skill/paper-daily/scripts/prepare_summary_requests.py --repo-root . --date YYYY-MM-DD --out /tmp/paper-daily-summary-requests.json
```

Run the local publishing pipeline after the summary artifacts have been written:

```bash
python3 skill/paper-daily/scripts/run_daily.py --repo-root . --date YYYY-MM-DD
```

Manually publish specific arXiv IDs with an explicit display date:

```bash
python3 skill/paper-daily/scripts/run_daily.py --repo-root . --date YYYY-MM-DD --arxiv-id 2505.14359v6 --arxiv-id 2512.06746
```

Inspect a specific date without changing README/feed/state/summary artifacts:

```bash
python3 skill/paper-daily/scripts/run_daily.py --repo-root . --date YYYY-MM-DD --view-only
```

Generate only the canonical/feed outputs:

```bash
python3 skill/paper-daily/scripts/generate_feed.py --repo-root . --date YYYY-MM-DD
```

- Judge stage guidance after recall:
  - read the top recalled papers from `selected` or `ranked`
  - judge only from `title`, `abstract`, categories, and lightweight institution hints
  - prefer papers aligned with the user's stated interests
  - keep the final list around `20` papers unless the user asks for a different size
  - after the final list is fixed, write the report immediately instead of stopping at the list
  - generate bilingual summaries for each selected paper using the report format above
  - replace raw arXiv categories with inferred topic keywords in user-facing metadata
  - summarize what the paper does; do not invent weaknesses from title/abstract-only evidence
  - keep judging rationale internal; the user-facing report should focus on the papers

## Notes

- arXiv Atom metadata usually does not include author affiliations. Institution matching in this MVP checks title/abstract and PDF first-page extraction, so it remains a weak signal compared with a dedicated affiliation enricher.
- `discover.py` is the primary command for this skill. It stays metadata-first and does not download PDFs.
- `discover.py` always saves a lightweight recall artifact unless you redirect it with `--out`.
- Shared defaults are `--max-results-per-keyword 50` and `--select 20` across discovery, publishing, and paper-learning integration unless explicitly overridden.
- The LLM judging step belongs to the skill workflow, not to the local discovery script. Judge by the preference profile above, not by generic quality alone.
- `run_daily.py` is a publishing workflow. It does not call a fixed model provider; it expects summary artifacts generated by the runtime skill.
- Keep short aliases conservative. Do not match ambiguous aliases like `MIT` across the full abstract because words such as `committed` can create false positives.
- Respect arXiv API etiquette. The CLI defaults to a delay between keyword queries.
- Summary artifacts are JSON files keyed by arXiv ID under `data/paper-daily/summary-artifacts/` by default.
- This skill operates on `README.md`, `README_en.md`, `summary/`, and `summary_en/`.

## References

- Institution whitelist: `references/institutions.json`
- Discovery implementation: `scripts/paper_daily/`
