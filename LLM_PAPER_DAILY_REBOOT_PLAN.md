# llm-paper-daily Reboot Plan

Target repo: `https://github.com/xianshang33/llm-paper-daily`

## Goal

Reboot the old `llm-paper-daily` repo with the same split used by `follow-builders`:

```text
central production on GitHub Actions
-> public feed-papers.json and README artifacts
-> local paper-subscribe skill reads the public feed
-> user receives a filtered digest locally or through delivery channels
```

The repo should stop acting like a historical archive dump and become a small, reproducible daily paper feed.

## Current State

- `paper-daily` already discovers arXiv papers, ranks candidates, summarizes selected papers, writes summary files, patches README files, and writes feed JSON.
- `paper-subscribe` already reads `feed-papers.json`, filters by topic/language/max items, emits a digest, delivers to stdout, and records delivered item ids.
- `README.md` and `README_en.md` have been cleaned to keep only 2026 content.
- `paper-subscribe` now has its own `package.json` with `"type": "module"` so Node can run its ESM scripts.
- Feed defaults now point to `xianshang33/llm-paper-daily`.

## Architecture Decision

Keep two skills, but make only one of them part of the automated production path.

| Layer | Owner | Runs Where | Responsibility |
|---|---|---|---|
| `paper-daily` | repo maintainer | GitHub Actions or local maintainer machine | discover papers, summarize, write README, write feed |
| `paper-subscribe` | subscriber | user local machine or agent environment | read public feed, filter, deliver digest |

Do not make subscribers run arXiv discovery or DashScope summarization. That would leak API requirements and make every subscriber pay the production cost.

## Follow Builders Mapping

`follow-builders` uses:

- `.github/workflows/generate-feed.yml` for central scheduled generation.
- `scripts/generate-feed.js` to create public feed JSON files and state.
- `scripts/package.json` with `"type": "module"` for ESM scripts.
- `SKILL.md` as the onboarding surface for user preferences and local delivery.
- `prepare-digest.js` and `deliver.js` for local digest preparation and delivery.

Map that to this project as:

| follow-builders | llm-paper-daily |
|---|---|
| `generate-feed.yml` | `.github/workflows/daily-paper.yml` |
| `scripts/generate-feed.js` | `skill/paper-daily/scripts/run_daily.py` |
| `feed-x.json`, `feed-podcasts.json`, `feed-blogs.json` | `feed-papers.json`, `canonical-papers.json` |
| `state-feed.json` | `skill/paper-daily/output/state-feed.json` |
| local config `~/.follow-builders/config.json` | local config `~/.paper-subscribe/config.json` |
| digest from central feeds | digest from `feed-papers.json` |

## Implementation Plan

### Phase 1: Repo Hygiene

1. Initialize or clone the real target repository locally.
2. Add `.gitignore`:
   - `__pycache__/`
   - `*.pyc`
   - `.DS_Store`
   - local debug output
3. Remove committed `__pycache__` files before the first clean push.
4. Add `requirements.txt` for Python runtime:
   - `openai`
5. Keep Node dependency-free for `paper-subscribe` unless Telegram/email delivery is added.
6. Add or confirm license.

### Phase 2: GitHub Actions Production

Create `.github/workflows/daily-paper.yml`.

Required behavior:

```yaml
on:
  schedule:
    - cron: "17 6 * * *"
  workflow_dispatch:
    inputs:
      date:
        required: false
        description: "UTC arXiv submitted date, YYYY-MM-DD"
```

Workflow steps:

1. `actions/checkout@v4`
2. `actions/setup-python@v5` with Python 3.11 or 3.12
3. Install system dependency: `sudo apt-get update && sudo apt-get install -y poppler-utils`
4. Install Python deps: `python -m pip install -r requirements.txt`
5. Run production:

```bash
DATE="${{ inputs.date }}"
if [ -z "$DATE" ]; then
  DATE="$(date -u -d '1 day ago' +%F)"
fi
python3 skill/paper-daily/scripts/run_daily.py \
  --repo-root . \
  --date "$DATE" \
  --source-repo xianshang33/llm-paper-daily \
  --public-base-url https://raw.githubusercontent.com/xianshang33/llm-paper-daily/main
```

6. Commit only generated artifacts:
   - `README.md`
   - `README_en.md`
   - `summary/`
   - `summary_en/`
   - `feed-papers.json`
   - `canonical-papers.json`
   - `skill/paper-daily/output/state-feed.json`

Required secret:

- `DASHSCOPE_API_KEY`

### Phase 3: Production Robustness

Add degradation so the daily job does not fail the whole repo update because one paper is slow.

1. Fast path: title + abstract + first page.
2. Fallback path: title + abstract only.
3. Offline fallback: deterministic placeholder summary with provenance set to `fallback`.
4. Add per-paper timeout and continue to next paper on failure.
5. Write failure metadata into `provenance` so subscribers can see partial quality.

### Phase 4: Subscription Skill Upgrade

Make `paper-subscribe` behave more like `follow-builders`.

1. First run checks `~/.paper-subscribe/config.json`.
2. If missing, onboarding asks:
   - daily or weekly
   - time and timezone
   - language: `zh`, `en`, or bilingual
   - max items
   - delivery channel
3. Save config with:

```json
{
  "feed_url": "https://raw.githubusercontent.com/xianshang33/llm-paper-daily/main/feed-papers.json",
  "state_path": "~/.paper-subscribe/state.json",
  "timezone": "Asia/Shanghai",
  "schedule": "15 9 * * *",
  "filters": {
    "topics": ["agent", "llm"],
    "max_items": 5,
    "language": "zh"
  },
  "delivery": {
    "channel": "stdout"
  },
  "onboarding_complete": true
}
```

4. Keep stdout as the default delivery.
5. Add Telegram/email later, not in the first reboot, unless you need unattended delivery immediately.

### Phase 5: README as Product Surface

README should explain three things in the first screen:

1. This repo publishes daily LLM/Agent paper picks.
2. `feed-papers.json` is the public machine-readable feed.
3. Users can subscribe through `skill/paper-subscribe`.

Keep historical content out until the new pipeline proves stable. If old history matters later, move it to an archive file instead of mixing it into the generated block.

### Phase 6: Verification

Before pushing:

```bash
python3 -m compileall -q skill/paper-daily/scripts
python3 skill/paper-daily/scripts/discover.py --date 2026-05-07 --max-results-per-keyword 2 --select 2 --json --out /tmp/paper-discover-smoke.json
node skill/paper-subscribe/scripts/prepare-digest.js --config /tmp/paper-subscribe-config.json
node skill/paper-subscribe/scripts/deliver.js --config /tmp/paper-subscribe-config.json --input /tmp/paper-digest.json
```

Also check:

```bash
python3 - <<'PY'
from pathlib import Path
import re
for p in ['README.md', 'README_en.md']:
    text = Path(p).read_text()
    links = re.findall(r'\]\((summary(?:_en)?/[^)]+\.md)\)', text)
    missing = [link for link in links if not Path(link).exists()]
    print(p, 'links', len(links), 'missing', len(missing))
PY
```

## Not In Scope For First Reboot

- Telegram/email delivery.
- Historical backfill before 2026.
- Multi-source paper discovery beyond arXiv.
- Full web UI.
- Complex PDF extraction beyond `pdftotext` and graceful fallback.

## Open Decisions

1. Whether to keep the current `summary_en` long-form style or force README excerpts to short paragraph summaries.
2. Whether `skill/paper-daily/output/feed-papers.json` should be committed, or only root `feed-papers.json` should be public.
3. Whether the first GitHub Actions run should use today's date or replay the last known good date to validate the workflow.
