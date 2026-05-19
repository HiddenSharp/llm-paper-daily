---
name: paper-daily
description: Recall daily arXiv papers for LLM/Agent topics, rank candidates with keyword and institution filters, and prepare a broad candidate list for downstream review or publishing workflows.
---

# Paper Daily

Use this skill when you want broad daily recall of LLM/Agent papers from arXiv. The default goal is coverage first, not deep reading.

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
6. Return a broad ranked candidate list, usually `30-50` papers for one day when arXiv supply allows.
7. Use `run_daily.py` only when you explicitly want repo publishing artifacts such as summaries, feed updates, and README patches.

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

Ask for a wider recall set explicitly:

```bash
python3 skill/paper-daily/scripts/discover.py --date YYYY-MM-DD --select 50
```

For local testing with fewer requests or a narrower sample:

```bash
python3 skill/paper-daily/scripts/discover.py --date YYYY-MM-DD --max-results-per-keyword 10 --select 20
```

Run the end-to-end local publishing pipeline against the current repo:

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

## Notes

- arXiv Atom metadata usually does not include author affiliations. Institution matching in this MVP checks title/abstract and PDF first-page extraction, so it remains a weak signal compared with a dedicated affiliation enricher.
- `discover.py` is the primary command for this skill. It stays lightweight and metadata-first.
- `discover.py` always saves a lightweight recall artifact unless you redirect it with `--out`.
- `run_daily.py` is a publishing workflow. It may download PDFs and call the summary model, so it is slower and more expensive than recall-only discovery.
- Keep short aliases conservative. Do not match ambiguous aliases like `MIT` across the full abstract because words such as `committed` can create false positives.
- Respect arXiv API etiquette. The CLI defaults to a delay between keyword queries.
- This skill operates on `README.md`, `README_en.md`, `summary/`, and `summary_en/`.

## References

- Institution whitelist: `references/institutions.json`
- Discovery implementation: `scripts/paper_daily/`
