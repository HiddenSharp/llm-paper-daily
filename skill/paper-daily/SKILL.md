---
name: paper-daily
description: Discover daily arXiv papers for LLM/Agent topics, rank candidates with keyword and institution filters, and prepare a small selected paper list for llm-paper-daily style workflows.
---

# Paper Daily

Use this skill when maintaining a daily LLM/Agent paper list from arXiv.

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
6. Select 3-5 papers for summarization and deterministic README rendering when enough ranked candidates are available; fewer papers are allowed only when filtered candidates are genuinely insufficient.

## Commands

Run a real arXiv dry-run for a UTC submitted date:

```bash
python3 skill/paper-daily/scripts/discover.py --date YYYY-MM-DD --select 5
```

Write JSON output:

```bash
python3 skill/paper-daily/scripts/discover.py --date YYYY-MM-DD --select 5 --json --out /tmp/papers.json
```

For local testing with fewer requests:

```bash
python3 skill/paper-daily/scripts/discover.py --date YYYY-MM-DD --max-results-per-keyword 10 --select 5
```

Run the end-to-end local pipeline against the current repo:

```bash
python3 skill/paper-daily/scripts/run_daily.py --repo-root . --date YYYY-MM-DD
```

Inspect a specific date without changing README/feed/state/summary artifacts:

```bash
python3 skill/paper-daily/scripts/run_daily.py --repo-root . --date YYYY-MM-DD --view-only
```

Generate only the canonical/feed outputs:

```bash
python3 skill/paper-daily/scripts/generate_feed.py --repo-root . --date YYYY-MM-DD
```

## Notes

- arXiv Atom metadata usually does not include author affiliations. Institution matching in this MVP checks title/abstract and PDF first-page extraction, so it remains a weak signal compared with a dedicated affiliation enricher.
- Keep short aliases conservative. Do not match ambiguous aliases like `MIT` across the full abstract because words such as `committed` can create false positives.
- Respect arXiv API etiquette. The CLI defaults to a delay between keyword queries.
- This skill operates on `README.md`, `README_en.md`, `summary/`, and `summary_en/`.

## References

- Institution whitelist: `references/institutions.json`
- Discovery implementation: `scripts/paper_daily/`
