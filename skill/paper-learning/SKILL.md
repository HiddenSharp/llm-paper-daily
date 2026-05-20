---
name: paper-learning
description: Use this skill whenever the user wants to run, debug, extend, or reason about the daily paper learning workflow: discover arXiv and Hugging Face papers, publish daily reports to Notion and Feishu, use Notion as the HITL control plane, process selected papers into deep-reading notes, and archive papers into research areas. Trigger this skill for paper learning pipelines, Notion paper inboxes, Feishu paper reports, deep-reading queues, and AI-assisted paper archiving.
---

# Paper Learning

Use this skill for the personal paper learning workflow built on top of `paper-daily`.

## Boundary

- `paper-daily` discovers and summarizes candidate papers.
- `paper-learning` orchestrates Notion, Feishu, human selection, deep reading, and archive classification.
- `paper-subscribe` is not part of this workflow.

## Workflow

1. Run the daily stage with `run_daily_learning.py`.
2. Review candidates in the Notion `Paper Inbox`.
3. Set `Status = Selected` and optionally fill `Human Instruction`.
4. Run `process_notion_queue.py`.
5. Review generated `Deep Notes` and any `Proposed Area` fields in Notion.

## Commands

Daily stage:

```bash
python3 skill/paper-learning/scripts/run_daily_learning.py --config ~/.paper-learning/config.json --date YYYY-MM-DD
```

Queue stage:

```bash
python3 skill/paper-learning/scripts/process_notion_queue.py --config ~/.paper-learning/config.json
```

Dry-run daily stage:

```bash
python3 skill/paper-learning/scripts/run_daily_learning.py --config skill/paper-learning/templates/config.example.json --date YYYY-MM-DD --dry-run
```

Dry-run queue stage:

```bash
python3 skill/paper-learning/scripts/process_notion_queue.py --config skill/paper-learning/templates/config.example.json --dry-run --limit 1
```

Bootstrap Notion workspace:

```bash
python3 skill/paper-learning/scripts/bootstrap_notion.py --config skill/paper-learning/templates/config.example.json --parent-page <NOTION_PAGE_URL> --write-config
```

## Output Contract

The daily stage creates or updates:

- Notion `Paper Inbox` rows.
- One Notion daily report page.
- One Feishu daily report document or webhook message.
- One local run artifact under `data/paper-learning/runs/`.

The queue stage creates or updates:

- Notion `Deep Notes` rows.
- `Paper Inbox` status, archive fields, and deep-note relation.
- Local processing results printed as JSON.

## Notion Rules

- Treat Notion as the only workflow state source.
- Do not overwrite manually set `Research Areas` unless the user explicitly requests force reclassification.
- Treat `Institutions` as a weak rich-text label.
- Use `Proposed Area` for new taxonomy ideas instead of creating official `Research Areas` automatically.

## References

- Default deep-reading prompt: `references/deep_reading_prompt.md`
- Starter research areas: `references/research_areas.example.json`
- Config template: `templates/config.example.json`
