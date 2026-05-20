# Paper Learning Workflow Design

Date: 2026-05-20

## Goal

Build a daily paper learning pipeline on top of the existing `paper-daily` workflow. The system should discover relevant arXiv and Hugging Face papers, publish a daily report to Notion and Feishu, let the user select papers in Notion, run deep-reading only for selected papers, and archive the results into a Notion knowledge base.

Notion is the control plane and long-term source of truth. Feishu is a parallel delivery channel only.

## Non-Goals

- Do not use `paper-subscribe` in this design.
- Do not make Feishu a state source.
- Do not physically move Notion pages as the primary archive mechanism.
- Do not let AI freely create taxonomy entries without human review.

## Architecture

Add a new orchestration skill under `skill/paper-learning/`.

Responsibilities:

- Call or reuse `paper-daily` to produce daily paper records.
- Normalize paper records into a stable `DailyPaperRecord` contract.
- Upsert candidate papers into a Notion `Paper Inbox` database.
- Generate a Notion daily report page.
- Generate a Feishu daily report document from the same report model.
- Read selected papers from Notion.
- Run the deep-reading capability for selected papers.
- Create `Deep Notes` entries in Notion.
- Suggest or apply archive classification through `Research Areas`.

Existing `paper-daily` remains responsible for discovery and paper content assets:

- arXiv discovery and ranking.
- Paper summaries.
- Institution and topic weak labels.
- Existing README/feed artifacts, if still needed.
- A stable JSON output contract for downstream workflows.

The key boundary is:

- `paper-daily`: "What papers are worth looking at, and what summary material exists for them?"
- `paper-learning`: "How do these papers enter my learning system, get selected, read deeply, and archived?"

## Commands

First version exposes two manual commands.

```bash
python3 skill/paper-learning/scripts/run_daily_learning.py --config ~/.paper-learning/config.json --date YYYY-MM-DD
```

This command runs the daily stage: discover papers, write candidates into Notion, create a Notion daily report, and create a Feishu daily report.

```bash
python3 skill/paper-learning/scripts/process_notion_queue.py --config ~/.paper-learning/config.json
```

This command runs the selected-paper stage: read selected papers from Notion, generate deep notes, classify/archive them, and update Notion status.

Daily reporting and deep reading are separate because they happen on different human timelines. The daily report can run before the user has selected anything. Deep reading should only run after explicit human selection.

## Notion Workspace Model

### Paper Inbox

Primary control database. One row per discovered paper.

Properties:

- `Title`: title
- `Paper ID`: rich text, for example `arxiv:2605.xxxxx` or `hf:...`
- `Source`: select, `arXiv` or `HuggingFace`
- `URL`: url
- `PDF URL`: url
- `Authors`: rich text
- `Institutions`: rich text. This is a weak label, not a verified fact.
- `Published Date`: date
- `Run Date`: date
- `Status`: select, `New`, `Selected`, `Deep Reading`, `Deep Read Done`, `Archived`, `Skipped`, `Needs Review`, `Failed`
- `Interest`: select, `High`, `Medium`, `Low`
- `Human Instruction`: rich text
- `Research Areas`: relation to `Research Areas`
- `Proposed Area`: rich text
- `Archive Confidence`: select, `High`, `Medium`, `Low`
- `Archive Review Status`: select, `Auto Accepted`, `Needs Human Review`, `Human Corrected`
- `Deep Note`: relation to `Deep Notes`
- `Digest Summary`: rich text
- `Score`: number
- `Last Processed At`: date
- `Error`: rich text

`Paper ID` is the cross-system idempotency key.

### Deep Notes

Knowledge database for deep-reading outputs. One row per deep-reading note.

Properties:

- `Title`: title
- `Paper`: relation to `Paper Inbox`
- `Research Areas`: relation to `Research Areas`
- `Reading Focus`: rich text
- `Contribution Type`: select, `Method`, `Benchmark`, `System`, `Survey`, `Dataset`, `Tech Report`, `Evaluation`
- `Method Tags`: multi-select
- `Review Status`: select, `Draft`, `Reviewed`, `Needs Fix`
- `Created At`: date
- `Model/Prompt Version`: rich text

The page body contains the full deep-reading note: background, problem, method, evidence, relationship to prior work, reusable ideas, limitations, and any user-requested focus from `Human Instruction`.

### Research Areas

Taxonomy database for long-term organization.

Properties:

- `Name`: title
- `Aliases`: rich text or multi-select
- `Description`: rich text
- `Parent Area`: optional relation to `Research Areas`
- `Status`: select, `Active`, `Proposed`, `Deprecated`
- `Owner Note`: rich text

AI may only auto-link papers and notes to `Active` research areas. If no good active area exists, it writes `Proposed Area` on `Paper Inbox` and marks `Archive Review Status = Needs Human Review`.

The user can then create or select the correct `Research Areas` entry manually. Future runs must respect manually set `Research Areas` and must not overwrite them unless explicitly invoked with a force option.

### Daily Reports

Daily reports are normal Notion pages under a configured parent page, not the source of truth.

Title format:

```text
YYYY-MM-DD Daily Paper Report
```

Content:

- Batch overview.
- Candidate paper list.
- Per-paper summary.
- Links to source paper, PDF, and the corresponding `Paper Inbox` row.

The same report model is rendered to Feishu.

## Data Contracts

`paper-learning` uses a stable intermediate model instead of binding directly to current `paper-daily` dataclasses or Markdown output.

Initial `DailyPaperRecord` fields:

- `paper_id`
- `source`
- `title`
- `authors`
- `institutions`
- `abstract`
- `digest_summary`
- `summary_cn`
- `summary_en`
- `published_date`
- `run_date`
- `url`
- `pdf_url`
- `topic`
- `score`
- `signals`
- `provenance`

Current `paper-daily` fields mostly align through `CanonicalPaper`:

- `paper_id`
- `title`
- `authors`
- `abstract`
- `links.abs`
- `links.pdf`
- `institution`
- `date`
- `category_key`
- `category_alias`
- `summary_cn`
- `summary_en`
- `render_excerpt`
- `render_excerpt_en`
- `provenance`

Known gaps:

- Hugging Face Papers is not yet integrated.
- `paper-daily` has single-value `institution`; `paper-learning` stores `Institutions` as rich text and can accept a single value initially.
- Some ranking fields such as score and reasons may need to be preserved in the JSON contract if they should appear in Notion.

If `paper-daily` output is insufficient, extend its JSON output contract. Do not force the Notion schema to depend on internal `paper-daily` implementation details.

## Notion Adapter

Create a project-local Notion adapter inside `paper-learning`, for example:

```text
skill/paper-learning/scripts/paper_learning/notion_client.py
```

The adapter hides Notion API payload details from orchestration code.

Business methods:

- `upsert_paper(record)`
- `create_daily_report(date, records)`
- `query_selected_papers()`
- `create_deep_note(paper, note)`
- `update_paper_status(...)`
- `resolve_research_areas(...)`

The adapter owns:

- Notion API version.
- Database ids and property names from config.
- Query pagination.
- Rate limit handling.
- Block rendering.
- Property payload construction.
- Idempotent lookup by `Paper ID`.

Orchestration scripts should not manually construct low-level Notion JSON except through this adapter.

## Feishu Adapter

Feishu is a delivery target. It receives the daily report only.

First version should support:

- Create or update one daily Feishu document.
- Use the same report model as Notion daily reports.
- Record the created document id in local run artifacts.

Feishu failures do not invalidate the Notion control-plane updates.

## Daily Stage Flow

`run_daily_learning.py`:

1. Run or reuse `paper-daily` for the requested date.
2. Convert results to `DailyPaperRecord`.
3. Upsert each record into Notion `Paper Inbox` using `Paper ID`.
4. Generate a report model from the same records.
5. Create or update the Notion daily report page.
6. Create or update the Feishu daily report document.
7. Write a local run artifact under `data/paper-learning/runs/YYYY-MM-DD.json`.

The local artifact records input ids, Notion page ids, Feishu document ids, failures, and timestamps.

## Selected-Paper Flow

`process_notion_queue.py`:

1. Query `Paper Inbox` for `Status = Selected`.
2. For each paper, update `Status = Deep Reading` and set `Last Processed At`.
3. Read `Human Instruction`.
4. Fetch PDF or available full text.
5. Run the default deep-reading prompt/skill plus the user instruction.
6. Classify against active `Research Areas`.
7. If classification is confident, set relation to active areas.
8. If classification is not confident, write `Proposed Area` and set `Archive Review Status = Needs Human Review`.
9. Create a `Deep Notes` page and relation it back to `Paper Inbox`.
10. Update the original `Paper Inbox` row with final status, deep note relation, archive fields, and cleared error.

Default behavior must skip a paper if it already has a `Deep Note`. A later explicit force option may reprocess it.

## Error Handling

Errors are isolated at the narrowest practical unit.

- Notion upsert failure: record the failed paper in the local run artifact; command returns non-zero after attempting remaining safe work.
- Feishu failure: record failure but keep Notion updates.
- Deep-reading failure: set that paper to `Status = Failed` and write `Error`; continue with other selected papers.
- Low-confidence archive classification: not a failure; write `Proposed Area` and `Needs Human Review`.
- Existing manual `Research Areas`: do not overwrite unless a force option is explicitly used.

## Verification

First implementation should include these checks:

- `--dry-run` for both commands, printing intended Notion and Feishu operations without external writes.
- `--limit 1` for queue processing.
- Notion adapter tests using fixtures for property payloads and block payloads.
- Orchestration tests using sample `DailyPaperRecord` fixtures.
- Manual acceptance path: one paper goes from discovery to `Paper Inbox`, user marks it `Selected`, queue processing creates one `Deep Notes` page, and archive fields update.

## Configuration

Use `~/.paper-learning/config.json`.

Expected sections:

- `paper_daily`: repo paths and command options.
- `notion`: token env var name, database ids, parent page ids, property mappings.
- `feishu`: credentials or webhook/document config.
- `deep_reading`: model or prompt settings.
- `classification`: active taxonomy behavior and confidence thresholds.
- `runtime`: local artifact paths, rate limits, dry-run defaults.

Secrets should be read from environment variables rather than committed config.

## Open Implementation Decisions

These are implementation choices, not unresolved product requirements:

- Whether Hugging Face Papers discovery lives inside `paper-daily` or as a source adapter in `paper-learning`.
- Whether `paper-daily` gets a new command for stable JSON records or `paper-learning` adapts existing canonical/feed output first.
- Whether deep-reading is implemented as an internal prompt runner first or extracted into a formal skill later.

The design requirement is that these choices preserve the boundaries above.
