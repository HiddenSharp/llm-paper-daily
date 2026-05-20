# Paper Learning Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `skill/paper-learning`, an orchestration layer that turns daily paper discovery into a Notion-controlled learning workflow with parallel Feishu report delivery.

**Architecture:** Keep `paper-daily` responsible for discovery and summary assets, and add `paper-learning` as the workflow owner for Notion, Feishu, HITL selection, deep notes, and archive classification. Implement adapters around external services so orchestration code uses stable business methods and tests can run without network access.

**Tech Stack:** Python 3 standard library, existing `paper-daily` modules and scripts, Notion REST API, Hugging Face Hub daily papers endpoint, Feishu document/webhook API surface through a dry-run-capable adapter, `unittest` for focused tests.

---

## Scope Check

This plan covers one coherent product slice: a manually triggered learning pipeline. It includes daily ingestion, report delivery, queue processing, and skill documentation because those pieces are required for one working end-to-end flow.

The first implementation will not make scheduled automation, GitHub Actions, or rich Feishu bidirectional state. Those are separate future plans.

## File Structure

Create these new files:

- `skill/paper-learning/SKILL.md`: user-facing skill instructions, trigger guidance, workflow, commands, and output contract.
- `skill/paper-learning/templates/config.example.json`: full sample config with property mappings and dry-run defaults.
- `skill/paper-learning/references/deep_reading_prompt.md`: default deep-reading prompt contract.
- `skill/paper-learning/references/research_areas.example.json`: starter taxonomy examples.
- `skill/paper-learning/evals/evals.json`: skill-trigger and workflow test prompts for future `skill-creator` evaluation.
- `skill/paper-learning/scripts/run_daily_learning.py`: daily-stage CLI.
- `skill/paper-learning/scripts/process_notion_queue.py`: selected-paper queue CLI.
- `skill/paper-learning/scripts/paper_learning/__init__.py`: package marker.
- `skill/paper-learning/scripts/paper_learning/config.py`: config loading, env secret resolution, and typed config dataclasses.
- `skill/paper-learning/scripts/paper_learning/models.py`: stable internal dataclasses for records, reports, queue items, notes, and operation results.
- `skill/paper-learning/scripts/paper_learning/paper_daily_adapter.py`: run or read `paper-daily` outputs and convert them to `DailyPaperRecord`.
- `skill/paper-learning/scripts/paper_learning/huggingface_client.py`: fetch Hugging Face daily papers and normalize them.
- `skill/paper-learning/scripts/paper_learning/report.py`: build report models and Markdown renderings.
- `skill/paper-learning/scripts/paper_learning/notion_client.py`: Notion payload builders, dry-run operations, and HTTP adapter.
- `skill/paper-learning/scripts/paper_learning/feishu_client.py`: Feishu report delivery adapter with dry-run operations.
- `skill/paper-learning/scripts/paper_learning/deep_reading.py`: deep-reading command adapter and deterministic fallback note builder.
- `skill/paper-learning/scripts/paper_learning/classifier.py`: research-area classification logic.
- `skill/paper-learning/scripts/paper_learning/daily_pipeline.py`: daily workflow orchestration.
- `skill/paper-learning/scripts/paper_learning/queue_pipeline.py`: Notion selected-paper workflow orchestration.
- `tests/paper_learning/fixtures/canonical-papers.json`: sample canonical `paper-daily` output.
- `tests/paper_learning/fixtures/discovered-papers.json`: sample discovery output with score and institution hints.
- `tests/paper_learning/fixtures/hf-daily-papers.json`: sample Hugging Face daily papers response.
- `tests/paper_learning/test_config.py`: config parsing tests.
- `tests/paper_learning/test_models.py`: dataclass serialization tests.
- `tests/paper_learning/test_paper_daily_adapter.py`: `paper-daily` conversion tests.
- `tests/paper_learning/test_huggingface_client.py`: Hugging Face normalization tests.
- `tests/paper_learning/test_report.py`: daily report rendering tests.
- `tests/paper_learning/test_notion_client.py`: Notion property and block payload tests.
- `tests/paper_learning/test_feishu_client.py`: Feishu dry-run payload tests.
- `tests/paper_learning/test_classifier.py`: taxonomy classification tests.
- `tests/paper_learning/test_daily_pipeline.py`: daily orchestration tests with fake adapters.
- `tests/paper_learning/test_queue_pipeline.py`: queue orchestration tests with fake adapters.

Modify these existing files:

- `.gitignore`: ignore `data/paper-learning/runs/` local run artifacts if they should remain local.
- `AGENTS.md`: add a short note that `paper-learning` is the Notion learning orchestration layer after implementation is complete.

## Task 1: Scaffold the Skill and Skill-Creator Evaluation Prompts

**Files:**
- Create: `skill/paper-learning/SKILL.md`
- Create: `skill/paper-learning/templates/config.example.json`
- Create: `skill/paper-learning/references/deep_reading_prompt.md`
- Create: `skill/paper-learning/references/research_areas.example.json`
- Create: `skill/paper-learning/evals/evals.json`
- Test: `tests/paper_learning/test_skill_contract.py`

- [ ] **Step 1: Write the failing skill contract test**

Create `tests/paper_learning/test_skill_contract.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skill" / "paper-learning" / "SKILL.md"
CONFIG = ROOT / "skill" / "paper-learning" / "templates" / "config.example.json"
EVALS = ROOT / "skill" / "paper-learning" / "evals" / "evals.json"


def test_skill_doc_has_trigger_and_commands():
    text = SKILL.read_text(encoding="utf-8")
    assert "name: paper-learning" in text
    assert "Notion" in text
    assert "Feishu" in text
    assert "run_daily_learning.py" in text
    assert "process_notion_queue.py" in text


def test_config_and_evals_exist():
    assert CONFIG.exists()
    assert EVALS.exists()
```

- [ ] **Step 2: Run the skill contract test to verify it fails**

Run:

```bash
python3 -m unittest tests.paper_learning.test_skill_contract -v
```

Expected: fail with a missing file error for `skill/paper-learning/SKILL.md`.

- [ ] **Step 3: Create the skill documentation**

Create `skill/paper-learning/SKILL.md`:

```markdown
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
```

- [ ] **Step 4: Create the config template**

Create `skill/paper-learning/templates/config.example.json`:

```json
{
  "paper_daily": {
    "repo_root": ".",
    "python": "python3",
    "generate_feed_script": "skill/paper-daily/scripts/generate_feed.py",
    "discover_script": "skill/paper-daily/scripts/discover.py",
    "select": 5,
    "max_results_per_keyword": 10,
    "score_threshold": 6.0
  },
  "huggingface": {
    "enabled": true,
    "endpoint": "https://huggingface.co/api/daily_papers",
    "limit": 20
  },
  "notion": {
    "enabled": true,
    "dry_run": true,
    "api_base": "https://api.notion.com/v1",
    "api_version": "2022-06-28",
    "token_env": "NOTION_TOKEN",
    "paper_inbox_database_id": "paper-inbox-database-id",
    "deep_notes_database_id": "deep-notes-database-id",
    "research_areas_database_id": "research-areas-database-id",
    "daily_report_parent_page_id": "daily-report-parent-page-id"
  },
  "feishu": {
    "enabled": true,
    "dry_run": true,
    "webhook_url_env": "FEISHU_WEBHOOK_URL"
  },
  "deep_reading": {
    "prompt_path": "skill/paper-learning/references/deep_reading_prompt.md",
    "command": []
  },
  "classification": {
    "confidence_threshold": 0.72,
    "default_research_areas_path": "skill/paper-learning/references/research_areas.example.json"
  },
  "runtime": {
    "artifact_dir": "data/paper-learning/runs",
    "timeout_seconds": 60,
    "dry_run": true
  }
}
```

- [ ] **Step 5: Create the deep-reading prompt reference**

Create `skill/paper-learning/references/deep_reading_prompt.md`:

```markdown
# Default Deep-Reading Prompt

Read the paper with the user's focus in mind.

Return a structured note with these sections:

1. Problem Setting
2. Core Contribution
3. Method Structure
4. Evidence and Experiments
5. Relationship to Prior Work
6. Reusable Ideas
7. Limitations
8. Archive Recommendation

Use the user's `Human Instruction` as a priority lens. If the instruction asks for benchmark design, RL formulation, agent workflow, data generation, or evaluation detail, emphasize that part of the note.

Do not claim full-paper evidence when only abstract-level material is available. Mark such sections as abstract-based.
```

- [ ] **Step 6: Create the starter research areas**

Create `skill/paper-learning/references/research_areas.example.json`:

```json
[
  {
    "name": "Agent RL",
    "aliases": ["agentic rl", "reinforcement learning", "on-policy distillation"],
    "description": "Agent training, reinforcement learning, policy optimization, and distillation for agent systems."
  },
  {
    "name": "Benchmark",
    "aliases": ["evaluation", "eval", "leaderboard"],
    "description": "Benchmarks, evaluation protocols, diagnostic datasets, and measurement methods."
  },
  {
    "name": "Reasoning",
    "aliases": ["planning", "chain of thought", "inference"],
    "description": "Reasoning, planning, deliberation, and inference-time techniques."
  },
  {
    "name": "Synthetic Data",
    "aliases": ["data generation", "self training", "bootstrapping"],
    "description": "Synthetic data generation and data-centric model improvement."
  },
  {
    "name": "Tech Report",
    "aliases": ["system report", "model report", "technical report"],
    "description": "Major model, system, or product technical reports."
  }
]
```

- [ ] **Step 7: Create skill-creator eval prompts**

Create `skill/paper-learning/evals/evals.json`:

```json
{
  "skill_name": "paper-learning",
  "evals": [
    {
      "id": 1,
      "prompt": "Run today's paper learning daily report in dry-run mode and explain what would be sent to Notion and Feishu.",
      "expected_output": "Uses paper-learning, runs or describes run_daily_learning.py with --dry-run, and separates Notion control-plane updates from Feishu delivery.",
      "files": []
    },
    {
      "id": 2,
      "prompt": "I selected two papers in Notion and wrote reading instructions. Process the queue without overwriting my manual research-area edits.",
      "expected_output": "Uses paper-learning, runs or describes process_notion_queue.py, preserves manual Research Areas, and updates Deep Notes.",
      "files": []
    },
    {
      "id": 3,
      "prompt": "Add a new archive category suggestion flow for papers that do not match my existing Notion taxonomy.",
      "expected_output": "Uses paper-learning and explains Proposed Area plus Needs Human Review rather than directly creating taxonomy entries.",
      "files": []
    }
  ]
}
```

- [ ] **Step 8: Run the skill contract test to verify it passes**

Run:

```bash
python3 -m unittest tests.paper_learning.test_skill_contract -v
```

Expected: pass.

- [ ] **Step 9: Commit**

```bash
git add skill/paper-learning tests/paper_learning/test_skill_contract.py
git commit -m "feat: scaffold paper-learning skill"
```

## Task 2: Add Typed Config and Core Models

**Files:**
- Create: `skill/paper-learning/scripts/paper_learning/__init__.py`
- Create: `skill/paper-learning/scripts/paper_learning/config.py`
- Create: `skill/paper-learning/scripts/paper_learning/models.py`
- Test: `tests/paper_learning/test_config.py`
- Test: `tests/paper_learning/test_models.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/paper_learning/test_config.py`:

```python
import json
import os
import tempfile
import unittest
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.config import load_config


class ConfigTest(unittest.TestCase):
    def test_load_config_resolves_defaults_and_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({
                "paper_daily": {"repo_root": "."},
                "notion": {"token_env": "NOTION_TOKEN", "dry_run": True},
                "feishu": {"webhook_url_env": "FEISHU_WEBHOOK_URL", "dry_run": True},
                "runtime": {"artifact_dir": "data/paper-learning/runs", "dry_run": True}
            }), encoding="utf-8")
            os.environ["NOTION_TOKEN"] = "notion-secret"
            os.environ["FEISHU_WEBHOOK_URL"] = "https://example.test/webhook"

            cfg = load_config(path)

            self.assertEqual(cfg.paper_daily.repo_root, Path("."))
            self.assertEqual(cfg.notion.token, "notion-secret")
            self.assertEqual(cfg.feishu.webhook_url, "https://example.test/webhook")
            self.assertTrue(cfg.runtime.dry_run)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add an import helper for tests**

Create `skill/paper_learning_import.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path


def add_paper_learning_path() -> None:
    root = Path(__file__).resolve().parents[1]
    scripts = root / "skill" / "paper-learning" / "scripts"
    value = str(scripts)
    if value not in sys.path:
        sys.path.insert(0, value)
```

- [ ] **Step 3: Run config test to verify it fails**

Run:

```bash
python3 -m unittest tests.paper_learning.test_config -v
```

Expected: fail with `ModuleNotFoundError` for `paper_learning.config`.

- [ ] **Step 4: Implement config loading**

Create `skill/paper-learning/scripts/paper_learning/__init__.py`:

```python
"""Paper learning workflow orchestration."""
```

Create `skill/paper-learning/scripts/paper_learning/config.py`:

```python
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PaperDailyConfig:
    repo_root: Path
    python: str = "python3"
    generate_feed_script: str = "skill/paper-daily/scripts/generate_feed.py"
    discover_script: str = "skill/paper-daily/scripts/discover.py"
    select: int = 5
    max_results_per_keyword: int = 10
    score_threshold: float = 6.0


@dataclass(frozen=True)
class HuggingFaceConfig:
    enabled: bool = True
    endpoint: str = "https://huggingface.co/api/daily_papers"
    limit: int = 20


@dataclass(frozen=True)
class NotionConfig:
    enabled: bool = True
    dry_run: bool = True
    api_base: str = "https://api.notion.com/v1"
    api_version: str = "2022-06-28"
    token_env: str = "NOTION_TOKEN"
    token: str = ""
    paper_inbox_database_id: str = ""
    deep_notes_database_id: str = ""
    research_areas_database_id: str = ""
    daily_report_parent_page_id: str = ""


@dataclass(frozen=True)
class FeishuConfig:
    enabled: bool = True
    dry_run: bool = True
    webhook_url_env: str = "FEISHU_WEBHOOK_URL"
    webhook_url: str = ""


@dataclass(frozen=True)
class DeepReadingConfig:
    prompt_path: Path = Path("skill/paper-learning/references/deep_reading_prompt.md")
    command: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ClassificationConfig:
    confidence_threshold: float = 0.72
    default_research_areas_path: Path = Path("skill/paper-learning/references/research_areas.example.json")


@dataclass(frozen=True)
class RuntimeConfig:
    artifact_dir: Path = Path("data/paper-learning/runs")
    timeout_seconds: int = 60
    dry_run: bool = True


@dataclass(frozen=True)
class AppConfig:
    paper_daily: PaperDailyConfig
    huggingface: HuggingFaceConfig
    notion: NotionConfig
    feishu: FeishuConfig
    deep_reading: DeepReadingConfig
    classification: ClassificationConfig
    runtime: RuntimeConfig


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).expanduser()
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return AppConfig(
        paper_daily=_paper_daily(raw.get("paper_daily", {})),
        huggingface=_huggingface(raw.get("huggingface", {})),
        notion=_notion(raw.get("notion", {})),
        feishu=_feishu(raw.get("feishu", {})),
        deep_reading=_deep_reading(raw.get("deep_reading", {})),
        classification=_classification(raw.get("classification", {})),
        runtime=_runtime(raw.get("runtime", {})),
    )


def _paper_daily(raw: dict[str, Any]) -> PaperDailyConfig:
    return PaperDailyConfig(
        repo_root=Path(raw.get("repo_root", ".")),
        python=raw.get("python", "python3"),
        generate_feed_script=raw.get("generate_feed_script", "skill/paper-daily/scripts/generate_feed.py"),
        discover_script=raw.get("discover_script", "skill/paper-daily/scripts/discover.py"),
        select=int(raw.get("select", 5)),
        max_results_per_keyword=int(raw.get("max_results_per_keyword", 10)),
        score_threshold=float(raw.get("score_threshold", 6.0)),
    )


def _huggingface(raw: dict[str, Any]) -> HuggingFaceConfig:
    return HuggingFaceConfig(
        enabled=bool(raw.get("enabled", True)),
        endpoint=raw.get("endpoint", "https://huggingface.co/api/daily_papers"),
        limit=int(raw.get("limit", 20)),
    )


def _notion(raw: dict[str, Any]) -> NotionConfig:
    token_env = raw.get("token_env", "NOTION_TOKEN")
    return NotionConfig(
        enabled=bool(raw.get("enabled", True)),
        dry_run=bool(raw.get("dry_run", True)),
        api_base=raw.get("api_base", "https://api.notion.com/v1"),
        api_version=raw.get("api_version", "2022-06-28"),
        token_env=token_env,
        token=os.environ.get(token_env, ""),
        paper_inbox_database_id=raw.get("paper_inbox_database_id", ""),
        deep_notes_database_id=raw.get("deep_notes_database_id", ""),
        research_areas_database_id=raw.get("research_areas_database_id", ""),
        daily_report_parent_page_id=raw.get("daily_report_parent_page_id", ""),
    )


def _feishu(raw: dict[str, Any]) -> FeishuConfig:
    webhook_url_env = raw.get("webhook_url_env", "FEISHU_WEBHOOK_URL")
    return FeishuConfig(
        enabled=bool(raw.get("enabled", True)),
        dry_run=bool(raw.get("dry_run", True)),
        webhook_url_env=webhook_url_env,
        webhook_url=os.environ.get(webhook_url_env, ""),
    )


def _deep_reading(raw: dict[str, Any]) -> DeepReadingConfig:
    return DeepReadingConfig(
        prompt_path=Path(raw.get("prompt_path", "skill/paper-learning/references/deep_reading_prompt.md")),
        command=list(raw.get("command", [])),
    )


def _classification(raw: dict[str, Any]) -> ClassificationConfig:
    return ClassificationConfig(
        confidence_threshold=float(raw.get("confidence_threshold", 0.72)),
        default_research_areas_path=Path(raw.get("default_research_areas_path", "skill/paper-learning/references/research_areas.example.json")),
    )


def _runtime(raw: dict[str, Any]) -> RuntimeConfig:
    return RuntimeConfig(
        artifact_dir=Path(raw.get("artifact_dir", "data/paper-learning/runs")),
        timeout_seconds=int(raw.get("timeout_seconds", 60)),
        dry_run=bool(raw.get("dry_run", True)),
    )
```

- [ ] **Step 5: Write model tests**

Create `tests/paper_learning/test_models.py`:

```python
import unittest

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.models import DailyPaperRecord, OperationResult, ResearchArea


class ModelsTest(unittest.TestCase):
    def test_daily_paper_record_serializes(self):
        record = DailyPaperRecord(
            paper_id="arxiv:2605.00001",
            source="arXiv",
            title="Test Paper",
            authors=["A. Author"],
            institutions="Test Lab",
            abstract="Abstract",
            digest_summary="Digest",
            summary_cn="中文摘要",
            summary_en="English summary",
            published_date="2026-05-20",
            run_date="2026-05-20",
            url="https://arxiv.org/abs/2605.00001",
            pdf_url="https://arxiv.org/pdf/2605.00001",
            topic="Agent",
            score=7.5,
            signals={"priority_keyword": "Agent"},
            provenance={"source": "fixture"},
        )

        payload = record.to_dict()

        self.assertEqual(payload["paper_id"], "arxiv:2605.00001")
        self.assertEqual(payload["authors"], ["A. Author"])

    def test_research_area_matches_alias(self):
        area = ResearchArea(name="Agent RL", aliases=["agentic rl", "reinforcement learning"], description="RL for agents")

        self.assertTrue(area.matches("A new agentic RL benchmark"))
        self.assertFalse(area.matches("A vision tokenizer"))

    def test_operation_result_failure(self):
        result = OperationResult(ok=False, status="failed", message="bad request", data={"id": "x"})

        self.assertFalse(result.ok)
        self.assertEqual(result.to_dict()["status"], "failed")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Implement models**

Create `skill/paper-learning/scripts/paper_learning/models.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class DailyPaperRecord:
    paper_id: str
    source: str
    title: str
    authors: list[str]
    institutions: str
    abstract: str
    digest_summary: str
    summary_cn: str
    summary_en: str
    published_date: str
    run_date: str
    url: str
    pdf_url: str | None
    topic: str
    score: float
    signals: dict
    provenance: dict

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ReportModel:
    date: str
    title: str
    overview: str
    records: list[DailyPaperRecord]

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "title": self.title,
            "overview": self.overview,
            "records": [record.to_dict() for record in self.records],
        }


@dataclass(frozen=True)
class ResearchArea:
    name: str
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    notion_page_id: str | None = None

    def matches(self, text: str) -> bool:
        normalized = text.casefold()
        names = [self.name, *self.aliases]
        return any(value.casefold() in normalized for value in names if value)


@dataclass(frozen=True)
class SelectedPaper:
    notion_page_id: str
    record: DailyPaperRecord
    human_instruction: str
    existing_research_area_ids: list[str] = field(default_factory=list)
    existing_deep_note_id: str | None = None


@dataclass(frozen=True)
class DeepNote:
    title: str
    paper_id: str
    reading_focus: str
    markdown: str
    contribution_type: str
    method_tags: list[str]
    proposed_area: str
    archive_confidence: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ClassificationResult:
    area_ids: list[str]
    proposed_area: str
    confidence: str
    review_status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class OperationResult:
    ok: bool
    status: str
    message: str
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
```

- [ ] **Step 7: Run config and model tests**

Run:

```bash
python3 -m unittest tests.paper_learning.test_config tests.paper_learning.test_models -v
```

Expected: pass.

- [ ] **Step 8: Commit**

```bash
git add skill/paper_learning_import.py skill/paper-learning/scripts/paper_learning tests/paper_learning/test_config.py tests/paper_learning/test_models.py
git commit -m "feat: add paper-learning config and models"
```

## Task 3: Convert paper-daily and Hugging Face Sources into DailyPaperRecord

**Files:**
- Create: `skill/paper-learning/scripts/paper_learning/paper_daily_adapter.py`
- Create: `skill/paper-learning/scripts/paper_learning/huggingface_client.py`
- Create: `tests/paper_learning/fixtures/canonical-papers.json`
- Create: `tests/paper_learning/fixtures/discovered-papers.json`
- Create: `tests/paper_learning/fixtures/hf-daily-papers.json`
- Test: `tests/paper_learning/test_paper_daily_adapter.py`
- Test: `tests/paper_learning/test_huggingface_client.py`

- [ ] **Step 1: Create fixture files**

Create `tests/paper_learning/fixtures/canonical-papers.json`:

```json
{
  "schema_version": "v1",
  "generated_at": "2026-05-20T00:00:00+00:00",
  "run_date": "2026-05-20",
  "items": [
    {
      "schema_version": "v1",
      "paper_id": "2605.00001",
      "date": "2026-05-20",
      "title": "Agentic RL for Tool-Using Language Models",
      "authors": ["A. Author", "B. Author"],
      "abstract": "We study reinforcement learning for tool-using agents.",
      "links": {
        "abs": "https://arxiv.org/abs/2605.00001",
        "pdf": "https://arxiv.org/pdf/2605.00001",
        "github": null
      },
      "institution": "Example AI Lab",
      "category_key": "agent",
      "category_alias": "Agent",
      "category_display": {"zh": "Agent", "en": "Agent"},
      "summary_cn": "中文摘要",
      "summary_en": "English summary",
      "render_excerpt": "这是一篇关于 Agent RL 的论文。",
      "render_excerpt_en": "This paper studies Agent RL.",
      "source_discovery": {"source": "arxiv"},
      "source_summary": {"source": "local"},
      "provenance": {"pipeline": "paper-daily"}
    }
  ]
}
```

Create `tests/paper_learning/fixtures/discovered-papers.json`:

```json
{
  "date": "2026-05-20",
  "selected": [
    {
      "arxiv_id": "2605.00001",
      "score": 8.5,
      "priority_keyword": "Agent",
      "reasons": ["keyword:agent", "institution:Example AI Lab"],
      "institution_matches": ["Example AI Lab"],
      "lab_matches": []
    }
  ],
  "ranked": []
}
```

Create `tests/paper_learning/fixtures/hf-daily-papers.json`:

```json
[
  {
    "paper": {
      "id": "2605.00002",
      "title": "Benchmarking LLM Agents",
      "summary": "A benchmark for evaluating LLM agents.",
      "authors": [{"name": "C. Author"}],
      "publishedAt": "2026-05-20T00:00:00.000Z"
    },
    "numComments": 3
  }
]
```

- [ ] **Step 2: Write adapter tests**

Create `tests/paper_learning/test_paper_daily_adapter.py`:

```python
import unittest
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.paper_daily_adapter import load_paper_daily_records


ROOT = Path(__file__).resolve().parents[2]


class PaperDailyAdapterTest(unittest.TestCase):
    def test_load_paper_daily_records_merges_canonical_and_discovery_signals(self):
        records = load_paper_daily_records(
            canonical_path=ROOT / "tests/paper_learning/fixtures/canonical-papers.json",
            discovered_path=ROOT / "tests/paper_learning/fixtures/discovered-papers.json",
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].paper_id, "arxiv:2605.00001")
        self.assertEqual(records[0].source, "arXiv")
        self.assertEqual(records[0].institutions, "Example AI Lab")
        self.assertEqual(records[0].score, 8.5)
        self.assertEqual(records[0].signals["priority_keyword"], "Agent")


if __name__ == "__main__":
    unittest.main()
```

Create `tests/paper_learning/test_huggingface_client.py`:

```python
import json
import unittest
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.huggingface_client import normalize_hf_daily_papers


ROOT = Path(__file__).resolve().parents[2]


class HuggingFaceClientTest(unittest.TestCase):
    def test_normalize_hf_daily_papers(self):
        raw = json.loads((ROOT / "tests/paper_learning/fixtures/hf-daily-papers.json").read_text(encoding="utf-8"))

        records = normalize_hf_daily_papers(raw, run_date="2026-05-20")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].paper_id, "hf:2605.00002")
        self.assertEqual(records[0].source, "HuggingFace")
        self.assertEqual(records[0].url, "https://huggingface.co/papers/2605.00002")
        self.assertEqual(records[0].authors, ["C. Author"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run adapter tests to verify they fail**

Run:

```bash
python3 -m unittest tests.paper_learning.test_paper_daily_adapter tests.paper_learning.test_huggingface_client -v
```

Expected: fail with missing module errors.

- [ ] **Step 4: Implement paper-daily conversion**

Create `skill/paper-learning/scripts/paper_learning/paper_daily_adapter.py`:

```python
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .config import PaperDailyConfig
from .models import DailyPaperRecord


def run_paper_daily(date: str, cfg: PaperDailyConfig) -> None:
    repo_root = cfg.repo_root
    discover_out = repo_root / "data" / "paper-learning" / "runs" / date / "discovered-papers.json"
    discover_out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            cfg.python,
            cfg.discover_script,
            "--date",
            date,
            "--json",
            "--out",
            str(discover_out),
            "--select",
            str(cfg.select),
            "--max-results-per-keyword",
            str(cfg.max_results_per_keyword),
        ],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        [
            cfg.python,
            cfg.generate_feed_script,
            "--repo-root",
            ".",
            "--date",
            date,
            "--select",
            str(cfg.select),
            "--max-results-per-keyword",
            str(cfg.max_results_per_keyword),
            "--score-threshold",
            str(cfg.score_threshold),
        ],
        cwd=repo_root,
        check=True,
    )


def load_paper_daily_records(canonical_path: Path, discovered_path: Path | None = None) -> list[DailyPaperRecord]:
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    discovery_by_id = _load_discovery_by_id(discovered_path)
    records: list[DailyPaperRecord] = []
    for item in canonical.get("items", []):
        paper_id = item["paper_id"]
        discovery = discovery_by_id.get(paper_id, {})
        links = item.get("links", {})
        signals = {
            "priority_keyword": discovery.get("priority_keyword", item.get("category_alias", "")),
            "reasons": discovery.get("reasons", []),
        }
        records.append(DailyPaperRecord(
            paper_id=f"arxiv:{paper_id}",
            source="arXiv",
            title=item.get("title", ""),
            authors=list(item.get("authors", [])),
            institutions=item.get("institution") or "",
            abstract=item.get("abstract", ""),
            digest_summary=item.get("render_excerpt", ""),
            summary_cn=item.get("summary_cn", ""),
            summary_en=item.get("summary_en", ""),
            published_date=item.get("date", canonical.get("run_date", "")),
            run_date=canonical.get("run_date", item.get("date", "")),
            url=links.get("abs") or "",
            pdf_url=links.get("pdf"),
            topic=item.get("category_key", ""),
            score=float(discovery.get("score", 0.0)),
            signals=signals,
            provenance=item.get("provenance", {}),
        ))
    return records


def _load_discovery_by_id(path: Path | None) -> dict[str, dict]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for item in payload.get("selected", []):
        arxiv_id = str(item.get("arxiv_id", "")).split("v", 1)[0]
        if arxiv_id:
            result[arxiv_id] = item
    return result
```

- [ ] **Step 5: Implement Hugging Face client**

Create `skill/paper-learning/scripts/paper_learning/huggingface_client.py`:

```python
from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import HuggingFaceConfig
from .models import DailyPaperRecord


def fetch_hf_daily_papers(date: str, cfg: HuggingFaceConfig) -> list[DailyPaperRecord]:
    query = urlencode({"date": date})
    request = Request(f"{cfg.endpoint}?{query}", headers={"User-Agent": "llm-paper-daily/1.0"})
    with urlopen(request, timeout=30) as response:
        raw = json.loads(response.read().decode("utf-8"))
    return normalize_hf_daily_papers(raw[: cfg.limit], run_date=date)


def normalize_hf_daily_papers(raw: list[dict], run_date: str) -> list[DailyPaperRecord]:
    records: list[DailyPaperRecord] = []
    for item in raw:
        paper = item.get("paper", item)
        paper_id = str(paper.get("id") or paper.get("paperId") or "").strip()
        if not paper_id:
            continue
        title = paper.get("title", "")
        summary = paper.get("summary", "")
        published = _date_only(paper.get("publishedAt", run_date))
        authors = []
        for author in paper.get("authors", []):
            if isinstance(author, dict) and author.get("name"):
                authors.append(author["name"])
            elif isinstance(author, str):
                authors.append(author)
        records.append(DailyPaperRecord(
            paper_id=f"hf:{paper_id}",
            source="HuggingFace",
            title=title,
            authors=authors,
            institutions="",
            abstract=summary,
            digest_summary=summary,
            summary_cn="",
            summary_en=summary,
            published_date=published,
            run_date=run_date,
            url=f"https://huggingface.co/papers/{paper_id}",
            pdf_url=f"https://arxiv.org/pdf/{paper_id}" if paper_id[:4].isdigit() else None,
            topic="huggingface-daily",
            score=float(item.get("numComments", 0)),
            signals={"hf_num_comments": item.get("numComments", 0)},
            provenance={"source": "huggingface_daily_papers"},
        ))
    return records


def _date_only(value: str) -> str:
    if "T" not in value:
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
```

- [ ] **Step 6: Run adapter tests**

Run:

```bash
python3 -m unittest tests.paper_learning.test_paper_daily_adapter tests.paper_learning.test_huggingface_client -v
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add skill/paper-learning/scripts/paper_learning/paper_daily_adapter.py skill/paper-learning/scripts/paper_learning/huggingface_client.py tests/paper_learning
git commit -m "feat: normalize paper discovery sources"
```

## Task 4: Build Report Models and Markdown Renderers

**Files:**
- Create: `skill/paper-learning/scripts/paper_learning/report.py`
- Test: `tests/paper_learning/test_report.py`

- [ ] **Step 1: Write failing report tests**

Create `tests/paper_learning/test_report.py`:

```python
import unittest

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.models import DailyPaperRecord
from paper_learning.report import build_report, render_markdown_report


class ReportTest(unittest.TestCase):
    def test_render_markdown_report_contains_paper_and_inbox_hint(self):
        record = DailyPaperRecord(
            paper_id="arxiv:2605.00001",
            source="arXiv",
            title="Agentic RL for Tool-Using Language Models",
            authors=["A. Author"],
            institutions="Example AI Lab",
            abstract="Abstract",
            digest_summary="Digest",
            summary_cn="中文摘要",
            summary_en="English summary",
            published_date="2026-05-20",
            run_date="2026-05-20",
            url="https://arxiv.org/abs/2605.00001",
            pdf_url="https://arxiv.org/pdf/2605.00001",
            topic="Agent",
            score=8.5,
            signals={"priority_keyword": "Agent"},
            provenance={"source": "fixture"},
        )

        report = build_report("2026-05-20", [record])
        markdown = render_markdown_report(report, inbox_links={"arxiv:2605.00001": "https://notion.test/page"})

        self.assertIn("2026-05-20 Daily Paper Report", markdown)
        self.assertIn("Agentic RL for Tool-Using Language Models", markdown)
        self.assertIn("Example AI Lab", markdown)
        self.assertIn("https://notion.test/page", markdown)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run report test to verify it fails**

Run:

```bash
python3 -m unittest tests.paper_learning.test_report -v
```

Expected: fail with `ModuleNotFoundError` for `paper_learning.report`.

- [ ] **Step 3: Implement report rendering**

Create `skill/paper-learning/scripts/paper_learning/report.py`:

```python
from __future__ import annotations

from .models import DailyPaperRecord, ReportModel


def build_report(date: str, records: list[DailyPaperRecord]) -> ReportModel:
    topics = sorted({record.topic for record in records if record.topic})
    topic_text = ", ".join(topics) if topics else "mixed paper topics"
    overview = f"{len(records)} papers collected for {date}. Main topic signals: {topic_text}."
    return ReportModel(
        date=date,
        title=f"{date} Daily Paper Report",
        overview=overview,
        records=records,
    )


def render_markdown_report(report: ReportModel, inbox_links: dict[str, str] | None = None) -> str:
    inbox_links = inbox_links or {}
    lines = [f"# {report.title}", "", report.overview, ""]
    for index, record in enumerate(report.records, start=1):
        lines.extend([
            f"## {index}. {record.title}",
            "",
            f"- Paper ID: `{record.paper_id}`",
            f"- Source: {record.source}",
            f"- Authors: {', '.join(record.authors) if record.authors else 'Unknown'}",
            f"- Institutions: {record.institutions or 'Unknown'}",
            f"- Topic: {record.topic or 'Unknown'}",
            f"- Score: {record.score:g}",
            f"- Paper: {record.url}",
        ])
        if record.pdf_url:
            lines.append(f"- PDF: {record.pdf_url}")
        if record.paper_id in inbox_links:
            lines.append(f"- Notion Inbox: {inbox_links[record.paper_id]}")
        lines.extend(["", record.digest_summary or record.summary_en or record.abstract, ""])
    return "\n".join(lines).strip() + "\n"
```

- [ ] **Step 4: Run report test**

Run:

```bash
python3 -m unittest tests.paper_learning.test_report -v
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add skill/paper-learning/scripts/paper_learning/report.py tests/paper_learning/test_report.py
git commit -m "feat: render paper learning reports"
```

## Task 5: Implement Notion Adapter with Dry-Run and Payload Tests

**Files:**
- Create: `skill/paper-learning/scripts/paper_learning/notion_client.py`
- Test: `tests/paper_learning/test_notion_client.py`

- [ ] **Step 1: Write failing Notion payload tests**

Create `tests/paper_learning/test_notion_client.py`:

```python
import unittest

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.config import NotionConfig
from paper_learning.models import DailyPaperRecord
from paper_learning.notion_client import NotionClient


class NotionClientTest(unittest.TestCase):
    def test_build_paper_properties(self):
        client = NotionClient(NotionConfig(dry_run=True, paper_inbox_database_id="db"))
        record = DailyPaperRecord(
            paper_id="arxiv:2605.00001",
            source="arXiv",
            title="Agentic RL",
            authors=["A. Author"],
            institutions="Example AI Lab",
            abstract="Abstract",
            digest_summary="Digest",
            summary_cn="中文摘要",
            summary_en="English summary",
            published_date="2026-05-20",
            run_date="2026-05-20",
            url="https://arxiv.org/abs/2605.00001",
            pdf_url="https://arxiv.org/pdf/2605.00001",
            topic="Agent",
            score=8.5,
            signals={},
            provenance={},
        )

        props = client.build_paper_properties(record)

        self.assertEqual(props["Title"]["title"][0]["text"]["content"], "Agentic RL")
        self.assertEqual(props["Status"]["select"]["name"], "New")
        self.assertEqual(props["Institutions"]["rich_text"][0]["text"]["content"], "Example AI Lab")

    def test_dry_run_upsert_returns_operation(self):
        client = NotionClient(NotionConfig(dry_run=True, paper_inbox_database_id="db"))
        record = DailyPaperRecord(
            paper_id="arxiv:2605.00001",
            source="arXiv",
            title="Agentic RL",
            authors=[],
            institutions="",
            abstract="",
            digest_summary="",
            summary_cn="",
            summary_en="",
            published_date="2026-05-20",
            run_date="2026-05-20",
            url="https://arxiv.org/abs/2605.00001",
            pdf_url=None,
            topic="Agent",
            score=0,
            signals={},
            provenance={},
        )

        result = client.upsert_paper(record)

        self.assertTrue(result.ok)
        self.assertEqual(result.status, "dry_run")
        self.assertEqual(result.data["paper_id"], "arxiv:2605.00001")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run Notion test to verify it fails**

Run:

```bash
python3 -m unittest tests.paper_learning.test_notion_client -v
```

Expected: fail with missing module error.

- [ ] **Step 3: Implement Notion client**

Create `skill/paper-learning/scripts/paper_learning/notion_client.py`:

```python
from __future__ import annotations

import json
from urllib.request import Request, urlopen

from .config import NotionConfig
from .models import DailyPaperRecord, DeepNote, OperationResult, ReportModel, SelectedPaper
from .report import render_markdown_report


class NotionClient:
    def __init__(self, config: NotionConfig):
        self.config = config

    def build_paper_properties(self, record: DailyPaperRecord) -> dict:
        props = {
            "Title": {"title": [{"text": {"content": record.title[:2000]}}]},
            "Paper ID": {"rich_text": [{"text": {"content": record.paper_id}}]},
            "Source": {"select": {"name": record.source}},
            "URL": {"url": record.url or None},
            "PDF URL": {"url": record.pdf_url},
            "Authors": {"rich_text": [{"text": {"content": ", ".join(record.authors)[:2000]}}]},
            "Institutions": {"rich_text": [{"text": {"content": record.institutions[:2000]}}]},
            "Published Date": {"date": {"start": record.published_date}},
            "Run Date": {"date": {"start": record.run_date}},
            "Status": {"select": {"name": "New"}},
            "Digest Summary": {"rich_text": [{"text": {"content": record.digest_summary[:2000]}}]},
            "Score": {"number": record.score},
            "Error": {"rich_text": []},
        }
        return props

    def upsert_paper(self, record: DailyPaperRecord) -> OperationResult:
        if self.config.dry_run:
            return OperationResult(True, "dry_run", "paper upsert skipped in dry-run", {"paper_id": record.paper_id})
        existing = self._find_page_by_paper_id(record.paper_id)
        if existing:
            payload = {"properties": self.build_paper_properties(record)}
            data = self._request("PATCH", f"/pages/{existing}", payload)
            return OperationResult(True, "updated", "paper updated", data)
        payload = {
            "parent": {"database_id": self.config.paper_inbox_database_id},
            "properties": self.build_paper_properties(record),
        }
        data = self._request("POST", "/pages", payload)
        return OperationResult(True, "created", "paper created", data)

    def create_daily_report(self, report: ReportModel, inbox_links: dict[str, str]) -> OperationResult:
        markdown = render_markdown_report(report, inbox_links=inbox_links)
        if self.config.dry_run:
            return OperationResult(True, "dry_run", "daily report skipped in dry-run", {"markdown": markdown})
        payload = {
            "parent": {"page_id": self.config.daily_report_parent_page_id},
            "properties": {"title": [{"text": {"content": report.title}}]},
            "children": markdown_to_blocks(markdown),
        }
        data = self._request("POST", "/pages", payload)
        return OperationResult(True, "created", "daily report created", data)

    def query_selected_papers(self) -> list[SelectedPaper]:
        if self.config.dry_run:
            return []
        payload = {
            "filter": {
                "property": "Status",
                "select": {"equals": "Selected"},
            }
        }
        data = self._request("POST", f"/databases/{self.config.paper_inbox_database_id}/query", payload)
        return [selected_paper_from_page(page) for page in data.get("results", [])]

    def create_deep_note(self, paper: SelectedPaper, note: DeepNote, area_ids: list[str]) -> OperationResult:
        if self.config.dry_run:
            return OperationResult(True, "dry_run", "deep note skipped in dry-run", {"paper_id": paper.record.paper_id})
        payload = {
            "parent": {"database_id": self.config.deep_notes_database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": note.title[:2000]}}]},
                "Paper": {"relation": [{"id": paper.notion_page_id}]},
                "Research Areas": {"relation": [{"id": area_id} for area_id in area_ids]},
                "Reading Focus": {"rich_text": [{"text": {"content": note.reading_focus[:2000]}}]},
                "Contribution Type": {"select": {"name": note.contribution_type}},
                "Method Tags": {"multi_select": [{"name": tag} for tag in note.method_tags]},
                "Review Status": {"select": {"name": "Draft"}},
            },
            "children": markdown_to_blocks(note.markdown),
        }
        data = self._request("POST", "/pages", payload)
        return OperationResult(True, "created", "deep note created", data)

    def update_paper_status(self, page_id: str, properties: dict) -> OperationResult:
        if self.config.dry_run:
            return OperationResult(True, "dry_run", "paper status skipped in dry-run", {"page_id": page_id, "properties": properties})
        data = self._request("PATCH", f"/pages/{page_id}", {"properties": properties})
        return OperationResult(True, "updated", "paper status updated", data)

    def _find_page_by_paper_id(self, paper_id: str) -> str | None:
        payload = {
            "filter": {
                "property": "Paper ID",
                "rich_text": {"equals": paper_id},
            }
        }
        data = self._request("POST", f"/databases/{self.config.paper_inbox_database_id}/query", payload)
        results = data.get("results", [])
        if not results:
            return None
        return results[0]["id"]

    def _request(self, method: str, path: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self.config.api_base.rstrip("/") + path,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Notion-Version": self.config.api_version,
                "Content-Type": "application/json",
            },
        )
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))


def markdown_to_blocks(markdown: str) -> list[dict]:
    blocks: list[dict] = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:][:2000]}}]}})
        elif line.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:][:2000]}}]}})
        elif line.startswith("- "):
            blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:][:2000]}}]}})
        elif line.strip():
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": line[:2000]}}]}})
    return blocks[:100]


def selected_paper_from_page(page: dict) -> SelectedPaper:
    props = page.get("properties", {})
    paper_id = _plain_rich_text(props.get("Paper ID", {}))
    title = _plain_title(props.get("Title", {}))
    record = DailyPaperRecord(
        paper_id=paper_id,
        source=_select_name(props.get("Source", {})),
        title=title,
        authors=_plain_rich_text(props.get("Authors", {})).split(", ") if _plain_rich_text(props.get("Authors", {})) else [],
        institutions=_plain_rich_text(props.get("Institutions", {})),
        abstract="",
        digest_summary=_plain_rich_text(props.get("Digest Summary", {})),
        summary_cn="",
        summary_en="",
        published_date=_date_start(props.get("Published Date", {})),
        run_date=_date_start(props.get("Run Date", {})),
        url=props.get("URL", {}).get("url") or "",
        pdf_url=props.get("PDF URL", {}).get("url"),
        topic="",
        score=float(props.get("Score", {}).get("number") or 0),
        signals={},
        provenance={"source": "notion"},
    )
    return SelectedPaper(
        notion_page_id=page["id"],
        record=record,
        human_instruction=_plain_rich_text(props.get("Human Instruction", {})),
        existing_research_area_ids=[item["id"] for item in props.get("Research Areas", {}).get("relation", [])],
        existing_deep_note_id=_first_relation_id(props.get("Deep Note", {})),
    )


def _plain_title(prop: dict) -> str:
    return "".join(part.get("plain_text", "") for part in prop.get("title", []))


def _plain_rich_text(prop: dict) -> str:
    return "".join(part.get("plain_text", "") for part in prop.get("rich_text", []))


def _select_name(prop: dict) -> str:
    select = prop.get("select")
    return select.get("name", "") if select else ""


def _date_start(prop: dict) -> str:
    date = prop.get("date")
    return date.get("start", "") if date else ""


def _first_relation_id(prop: dict) -> str | None:
    relation = prop.get("relation", [])
    return relation[0]["id"] if relation else None
```

- [ ] **Step 4: Run Notion tests**

Run:

```bash
python3 -m unittest tests.paper_learning.test_notion_client -v
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add skill/paper-learning/scripts/paper_learning/notion_client.py tests/paper_learning/test_notion_client.py
git commit -m "feat: add notion adapter"
```

## Task 6: Implement Feishu Dry-Run Delivery Adapter

**Files:**
- Create: `skill/paper-learning/scripts/paper_learning/feishu_client.py`
- Test: `tests/paper_learning/test_feishu_client.py`

- [ ] **Step 1: Write failing Feishu tests**

Create `tests/paper_learning/test_feishu_client.py`:

```python
import unittest

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.config import FeishuConfig
from paper_learning.feishu_client import FeishuClient
from paper_learning.models import DailyPaperRecord
from paper_learning.report import build_report


class FeishuClientTest(unittest.TestCase):
    def test_dry_run_deliver_report(self):
        client = FeishuClient(FeishuConfig(dry_run=True))
        record = DailyPaperRecord(
            paper_id="arxiv:2605.00001",
            source="arXiv",
            title="Agentic RL",
            authors=[],
            institutions="",
            abstract="",
            digest_summary="Digest",
            summary_cn="",
            summary_en="",
            published_date="2026-05-20",
            run_date="2026-05-20",
            url="https://arxiv.org/abs/2605.00001",
            pdf_url=None,
            topic="Agent",
            score=0,
            signals={},
            provenance={},
        )
        report = build_report("2026-05-20", [record])

        result = client.deliver_report(report, inbox_links={})

        self.assertTrue(result.ok)
        self.assertEqual(result.status, "dry_run")
        self.assertIn("Agentic RL", result.data["markdown"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run Feishu test to verify it fails**

Run:

```bash
python3 -m unittest tests.paper_learning.test_feishu_client -v
```

Expected: fail with missing module error.

- [ ] **Step 3: Implement Feishu adapter**

Create `skill/paper-learning/scripts/paper_learning/feishu_client.py`:

```python
from __future__ import annotations

import json
from urllib.request import Request, urlopen

from .config import FeishuConfig
from .models import OperationResult, ReportModel
from .report import render_markdown_report


class FeishuClient:
    def __init__(self, config: FeishuConfig):
        self.config = config

    def deliver_report(self, report: ReportModel, inbox_links: dict[str, str]) -> OperationResult:
        markdown = render_markdown_report(report, inbox_links=inbox_links)
        if self.config.dry_run or not self.config.webhook_url:
            return OperationResult(True, "dry_run", "feishu delivery skipped in dry-run", {"markdown": markdown})
        payload = {
            "msg_type": "text",
            "content": {"text": markdown[:12000]},
        }
        request = Request(
            self.config.webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        return OperationResult(True, "sent", "feishu report sent", data)
```

- [ ] **Step 4: Run Feishu test**

Run:

```bash
python3 -m unittest tests.paper_learning.test_feishu_client -v
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add skill/paper-learning/scripts/paper_learning/feishu_client.py tests/paper_learning/test_feishu_client.py
git commit -m "feat: add feishu delivery adapter"
```

## Task 7: Implement Daily Pipeline and CLI

**Files:**
- Create: `skill/paper-learning/scripts/paper_learning/daily_pipeline.py`
- Create: `skill/paper-learning/scripts/run_daily_learning.py`
- Modify: `.gitignore`
- Test: `tests/paper_learning/test_daily_pipeline.py`

- [ ] **Step 1: Write failing daily pipeline test**

Create `tests/paper_learning/test_daily_pipeline.py`:

```python
import tempfile
import unittest
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.models import DailyPaperRecord, OperationResult
from paper_learning.daily_pipeline import run_daily_pipeline


class FakeNotion:
    def __init__(self):
        self.upserted = []

    def upsert_paper(self, record):
        self.upserted.append(record.paper_id)
        return OperationResult(True, "dry_run", "ok", {"paper_id": record.paper_id, "url": f"https://notion.test/{record.paper_id}"})

    def create_daily_report(self, report, inbox_links):
        return OperationResult(True, "dry_run", "report", {"title": report.title, "links": inbox_links})


class FakeFeishu:
    def deliver_report(self, report, inbox_links):
        return OperationResult(True, "dry_run", "feishu", {"title": report.title})


class DailyPipelineTest(unittest.TestCase):
    def test_run_daily_pipeline_writes_artifact(self):
        record = DailyPaperRecord(
            paper_id="arxiv:2605.00001",
            source="arXiv",
            title="Agentic RL",
            authors=[],
            institutions="",
            abstract="",
            digest_summary="Digest",
            summary_cn="",
            summary_en="",
            published_date="2026-05-20",
            run_date="2026-05-20",
            url="https://arxiv.org/abs/2605.00001",
            pdf_url=None,
            topic="Agent",
            score=0,
            signals={},
            provenance={},
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_daily_pipeline(
                date="2026-05-20",
                records=[record],
                notion=FakeNotion(),
                feishu=FakeFeishu(),
                artifact_dir=Path(tmp),
            )

            self.assertTrue(result.ok)
            artifact = Path(tmp) / "2026-05-20.json"
            self.assertTrue(artifact.exists())
            self.assertIn("arxiv:2605.00001", artifact.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run daily pipeline test to verify it fails**

Run:

```bash
python3 -m unittest tests.paper_learning.test_daily_pipeline -v
```

Expected: fail with missing module error.

- [ ] **Step 3: Implement daily pipeline**

Create `skill/paper-learning/scripts/paper_learning/daily_pipeline.py`:

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import DailyPaperRecord, OperationResult
from .report import build_report


def run_daily_pipeline(
    *,
    date: str,
    records: list[DailyPaperRecord],
    notion,
    feishu,
    artifact_dir: Path,
) -> OperationResult:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    inbox_links: dict[str, str] = {}
    paper_results = []
    ok = True
    for record in records:
        result = notion.upsert_paper(record)
        paper_results.append(result.to_dict())
        ok = ok and result.ok
        url = result.data.get("url")
        if url:
            inbox_links[record.paper_id] = url
    report = build_report(date, records)
    notion_report = notion.create_daily_report(report, inbox_links)
    feishu_report = feishu.deliver_report(report, inbox_links)
    ok = ok and notion_report.ok
    artifact = {
        "date": date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "paper_count": len(records),
        "paper_results": paper_results,
        "notion_report": notion_report.to_dict(),
        "feishu_report": feishu_report.to_dict(),
    }
    artifact_path = artifact_dir / f"{date}.json"
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return OperationResult(ok, "completed" if ok else "failed", "daily pipeline completed", {"artifact_path": str(artifact_path)})
```

- [ ] **Step 4: Implement daily CLI**

Create `skill/paper-learning/scripts/run_daily_learning.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from paper_learning.config import load_config
from paper_learning.daily_pipeline import run_daily_pipeline
from paper_learning.feishu_client import FeishuClient
from paper_learning.huggingface_client import fetch_hf_daily_papers
from paper_learning.notion_client import NotionClient
from paper_learning.paper_daily_adapter import load_paper_daily_records, run_paper_daily


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    if args.dry_run:
        cfg = cfg.__class__(
            paper_daily=cfg.paper_daily,
            huggingface=cfg.huggingface,
            notion=cfg.notion.__class__(**{**cfg.notion.__dict__, "dry_run": True}),
            feishu=cfg.feishu.__class__(**{**cfg.feishu.__dict__, "dry_run": True}),
            deep_reading=cfg.deep_reading,
            classification=cfg.classification,
            runtime=cfg.runtime.__class__(**{**cfg.runtime.__dict__, "dry_run": True}),
        )
    repo_root = cfg.paper_daily.repo_root
    run_dir = cfg.runtime.artifact_dir / args.date
    discovered_path = run_dir / "discovered-papers.json"
    canonical_path = repo_root / "data" / "canonical-papers.json"
    if not args.skip_paper_daily:
        run_paper_daily(args.date, cfg.paper_daily)
    records = load_paper_daily_records(canonical_path=canonical_path, discovered_path=discovered_path)
    if cfg.huggingface.enabled:
        records.extend(fetch_hf_daily_papers(args.date, cfg.huggingface))
    if args.limit:
        records = records[: args.limit]
    result = run_daily_pipeline(
        date=args.date,
        records=records,
        notion=NotionClient(cfg.notion),
        feishu=FeishuClient(cfg.feishu),
        artifact_dir=cfg.runtime.artifact_dir,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the paper-learning daily report workflow.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-paper-daily", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Update ignore rules for run artifacts**

Modify `.gitignore` to include:

```gitignore
/data/paper-learning/runs/
```

- [ ] **Step 6: Run daily pipeline test**

Run:

```bash
python3 -m unittest tests.paper_learning.test_daily_pipeline -v
```

Expected: pass.

- [ ] **Step 7: Run daily CLI help**

Run:

```bash
PYTHONPATH=skill/paper-learning/scripts python3 skill/paper-learning/scripts/run_daily_learning.py --help
```

Expected: prints usage and exits with code 0.

- [ ] **Step 8: Commit**

```bash
git add .gitignore skill/paper-learning/scripts/run_daily_learning.py skill/paper-learning/scripts/paper_learning/daily_pipeline.py tests/paper_learning/test_daily_pipeline.py
git commit -m "feat: add daily learning pipeline"
```

## Task 8: Implement Deep Reading and Archive Classification

**Files:**
- Create: `skill/paper-learning/scripts/paper_learning/deep_reading.py`
- Create: `skill/paper-learning/scripts/paper_learning/classifier.py`
- Test: `tests/paper_learning/test_classifier.py`

- [ ] **Step 1: Write failing classifier tests**

Create `tests/paper_learning/test_classifier.py`:

```python
import unittest

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.classifier import classify_note
from paper_learning.models import DeepNote, ResearchArea


class ClassifierTest(unittest.TestCase):
    def test_classify_note_matches_active_area(self):
        note = DeepNote(
            title="Agentic RL note",
            paper_id="arxiv:2605.00001",
            reading_focus="Focus on RL",
            markdown="This paper studies agentic RL and policy optimization.",
            contribution_type="Method",
            method_tags=["Agent", "RL"],
            proposed_area="",
            archive_confidence="Medium",
        )
        areas = [ResearchArea(name="Agent RL", aliases=["agentic RL"], description="")]

        result = classify_note(note, areas)

        self.assertEqual(result.area_ids, ["Agent RL"])
        self.assertEqual(result.review_status, "Auto Accepted")

    def test_classify_note_proposes_new_area_when_no_match(self):
        note = DeepNote(
            title="Tokenizer note",
            paper_id="arxiv:2605.00002",
            reading_focus="Focus on tokenizer",
            markdown="This paper studies a new tokenizer for images.",
            contribution_type="Method",
            method_tags=["Tokenizer"],
            proposed_area="Tokenizer",
            archive_confidence="Low",
        )

        result = classify_note(note, [])

        self.assertEqual(result.area_ids, [])
        self.assertEqual(result.proposed_area, "Tokenizer")
        self.assertEqual(result.review_status, "Needs Human Review")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run classifier test to verify it fails**

Run:

```bash
python3 -m unittest tests.paper_learning.test_classifier -v
```

Expected: fail with missing module error.

- [ ] **Step 3: Implement deep-reading fallback**

Create `skill/paper-learning/scripts/paper_learning/deep_reading.py`:

```python
from __future__ import annotations

import json
import subprocess

from .config import DeepReadingConfig
from .models import DeepNote, SelectedPaper


def generate_deep_note(paper: SelectedPaper, cfg: DeepReadingConfig) -> DeepNote:
    if cfg.command:
        payload = json.dumps({
            "paper": paper.record.to_dict(),
            "human_instruction": paper.human_instruction,
        }, ensure_ascii=False)
        completed = subprocess.run(
            list(cfg.command),
            input=payload,
            text=True,
            capture_output=True,
            check=True,
        )
        return deep_note_from_json(json.loads(completed.stdout))
    return fallback_deep_note(paper)


def fallback_deep_note(paper: SelectedPaper) -> DeepNote:
    record = paper.record
    focus = paper.human_instruction or "Default deep-reading focus"
    markdown = "\n".join([
        f"# {record.title}",
        "",
        "## Problem Setting",
        record.abstract or record.digest_summary or "No abstract available.",
        "",
        "## Core Contribution",
        record.summary_en or record.digest_summary or "No generated summary available.",
        "",
        "## User Focus",
        focus,
        "",
        "## Archive Recommendation",
        f"Initial topic signal: {record.topic or 'Unknown'}.",
    ])
    tags = [record.topic] if record.topic else []
    proposed = record.topic.title() if record.topic else "Uncategorized Paper"
    return DeepNote(
        title=f"Deep Note: {record.title}",
        paper_id=record.paper_id,
        reading_focus=focus,
        markdown=markdown,
        contribution_type="Method",
        method_tags=tags,
        proposed_area=proposed,
        archive_confidence="Medium",
    )


def deep_note_from_json(payload: dict) -> DeepNote:
    return DeepNote(
        title=payload["title"],
        paper_id=payload["paper_id"],
        reading_focus=payload.get("reading_focus", ""),
        markdown=payload["markdown"],
        contribution_type=payload.get("contribution_type", "Method"),
        method_tags=list(payload.get("method_tags", [])),
        proposed_area=payload.get("proposed_area", ""),
        archive_confidence=payload.get("archive_confidence", "Medium"),
    )
```

- [ ] **Step 4: Implement classifier**

Create `skill/paper-learning/scripts/paper_learning/classifier.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from .models import ClassificationResult, DeepNote, ResearchArea


def load_research_areas(path: Path) -> list[ResearchArea]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        ResearchArea(
            name=item["name"],
            aliases=list(item.get("aliases", [])),
            description=item.get("description", ""),
            notion_page_id=item.get("notion_page_id"),
        )
        for item in raw
    ]


def classify_note(note: DeepNote, active_areas: list[ResearchArea]) -> ClassificationResult:
    text = " ".join([note.title, note.markdown, " ".join(note.method_tags)])
    matched = [area for area in active_areas if area.matches(text)]
    if matched:
        ids = [area.notion_page_id or area.name for area in matched]
        return ClassificationResult(
            area_ids=ids,
            proposed_area="",
            confidence="High",
            review_status="Auto Accepted",
        )
    return ClassificationResult(
        area_ids=[],
        proposed_area=note.proposed_area or "Uncategorized Paper",
        confidence="Low",
        review_status="Needs Human Review",
    )
```

- [ ] **Step 5: Run classifier tests**

Run:

```bash
python3 -m unittest tests.paper_learning.test_classifier -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add skill/paper-learning/scripts/paper_learning/deep_reading.py skill/paper-learning/scripts/paper_learning/classifier.py tests/paper_learning/test_classifier.py
git commit -m "feat: add deep reading and archive classification"
```

## Task 9: Implement Queue Pipeline and CLI

**Files:**
- Create: `skill/paper-learning/scripts/paper_learning/queue_pipeline.py`
- Create: `skill/paper-learning/scripts/process_notion_queue.py`
- Test: `tests/paper_learning/test_queue_pipeline.py`

- [ ] **Step 1: Write failing queue pipeline test**

Create `tests/paper_learning/test_queue_pipeline.py`:

```python
import unittest

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.models import DailyPaperRecord, DeepNote, OperationResult, ResearchArea, SelectedPaper
from paper_learning.queue_pipeline import process_selected_papers


class FakeNotion:
    def __init__(self, papers):
        self.papers = papers
        self.status_updates = []
        self.notes = []

    def query_selected_papers(self):
        return self.papers

    def update_paper_status(self, page_id, properties):
        self.status_updates.append((page_id, properties))
        return OperationResult(True, "dry_run", "status", {"page_id": page_id})

    def create_deep_note(self, paper, note, area_ids):
        self.notes.append((paper.record.paper_id, area_ids))
        return OperationResult(True, "dry_run", "note", {"id": "note-1"})


class QueuePipelineTest(unittest.TestCase):
    def test_process_selected_papers_creates_note_and_updates_status(self):
        record = DailyPaperRecord(
            paper_id="arxiv:2605.00001",
            source="arXiv",
            title="Agentic RL",
            authors=[],
            institutions="",
            abstract="Agentic RL paper",
            digest_summary="Digest",
            summary_cn="",
            summary_en="",
            published_date="2026-05-20",
            run_date="2026-05-20",
            url="https://arxiv.org/abs/2605.00001",
            pdf_url=None,
            topic="Agent RL",
            score=0,
            signals={},
            provenance={},
        )
        selected = SelectedPaper(notion_page_id="page-1", record=record, human_instruction="Focus on RL")
        notion = FakeNotion([selected])

        result = process_selected_papers(
            notion=notion,
            deep_reader=lambda paper: DeepNote(
                title="Deep Note: Agentic RL",
                paper_id=paper.record.paper_id,
                reading_focus=paper.human_instruction,
                markdown="Agentic RL details",
                contribution_type="Method",
                method_tags=["Agent RL"],
                proposed_area="Agent RL",
                archive_confidence="High",
            ),
            active_areas=[ResearchArea(name="Agent RL", aliases=["agentic rl"], description="", notion_page_id="area-1")],
            limit=1,
        )

        self.assertTrue(result.ok)
        self.assertEqual(notion.notes, [("arxiv:2605.00001", ["area-1"])])
        self.assertTrue(any(update[1]["Status"]["select"]["name"] == "Deep Reading" for update in notion.status_updates))
        self.assertTrue(any(update[1]["Status"]["select"]["name"] == "Deep Read Done" for update in notion.status_updates))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run queue test to verify it fails**

Run:

```bash
python3 -m unittest tests.paper_learning.test_queue_pipeline -v
```

Expected: fail with missing module error.

- [ ] **Step 3: Implement queue pipeline**

Create `skill/paper-learning/scripts/paper_learning/queue_pipeline.py`:

```python
from __future__ import annotations

from .classifier import classify_note
from .models import OperationResult, ResearchArea, SelectedPaper


def process_selected_papers(
    *,
    notion,
    deep_reader,
    active_areas: list[ResearchArea],
    limit: int = 0,
    force: bool = False,
) -> OperationResult:
    selected = notion.query_selected_papers()
    if limit:
        selected = selected[:limit]
    processed = []
    ok = True
    for paper in selected:
        if paper.existing_deep_note_id and not force:
            processed.append({"paper_id": paper.record.paper_id, "status": "skipped_existing_deep_note"})
            continue
        notion.update_paper_status(paper.notion_page_id, {
            "Status": {"select": {"name": "Deep Reading"}},
            "Error": {"rich_text": []},
        })
        try:
            note = deep_reader(paper)
            classification = classify_note(note, active_areas)
            note_result = notion.create_deep_note(paper, note, classification.area_ids)
            final_properties = {
                "Status": {"select": {"name": "Deep Read Done"}},
                "Archive Confidence": {"select": {"name": classification.confidence}},
                "Archive Review Status": {"select": {"name": classification.review_status}},
                "Proposed Area": {"rich_text": [{"text": {"content": classification.proposed_area}}]} if classification.proposed_area else {"rich_text": []},
                "Error": {"rich_text": []},
            }
            if classification.area_ids and not paper.existing_research_area_ids:
                final_properties["Research Areas"] = {"relation": [{"id": area_id} for area_id in classification.area_ids]}
            if note_result.data.get("id"):
                final_properties["Deep Note"] = {"relation": [{"id": note_result.data["id"]}]}
            notion.update_paper_status(paper.notion_page_id, final_properties)
            processed.append({"paper_id": paper.record.paper_id, "status": "processed"})
        except Exception as exc:
            ok = False
            notion.update_paper_status(paper.notion_page_id, {
                "Status": {"select": {"name": "Failed"}},
                "Error": {"rich_text": [{"text": {"content": str(exc)[:2000]}}]},
            })
            processed.append({"paper_id": paper.record.paper_id, "status": "failed", "error": str(exc)})
    return OperationResult(ok, "completed" if ok else "failed", "queue processing completed", {"processed": processed})
```

- [ ] **Step 4: Implement queue CLI**

Create `skill/paper-learning/scripts/process_notion_queue.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from paper_learning.classifier import load_research_areas
from paper_learning.config import load_config
from paper_learning.deep_reading import generate_deep_note
from paper_learning.notion_client import NotionClient
from paper_learning.queue_pipeline import process_selected_papers


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    if args.dry_run:
        cfg = cfg.__class__(
            paper_daily=cfg.paper_daily,
            huggingface=cfg.huggingface,
            notion=cfg.notion.__class__(**{**cfg.notion.__dict__, "dry_run": True}),
            feishu=cfg.feishu,
            deep_reading=cfg.deep_reading,
            classification=cfg.classification,
            runtime=cfg.runtime.__class__(**{**cfg.runtime.__dict__, "dry_run": True}),
        )
    active_areas = load_research_areas(cfg.classification.default_research_areas_path)
    result = process_selected_papers(
        notion=NotionClient(cfg.notion),
        deep_reader=lambda paper: generate_deep_note(paper, cfg.deep_reading),
        active_areas=active_areas,
        limit=args.limit,
        force=args.force,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process selected papers from Notion.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run queue tests**

Run:

```bash
python3 -m unittest tests.paper_learning.test_queue_pipeline -v
```

Expected: pass.

- [ ] **Step 6: Run queue CLI help**

Run:

```bash
PYTHONPATH=skill/paper-learning/scripts python3 skill/paper-learning/scripts/process_notion_queue.py --help
```

Expected: prints usage and exits with code 0.

- [ ] **Step 7: Commit**

```bash
git add skill/paper-learning/scripts/process_notion_queue.py skill/paper-learning/scripts/paper_learning/queue_pipeline.py tests/paper_learning/test_queue_pipeline.py
git commit -m "feat: add notion queue processing"
```

## Task 10: Final Integration Verification and Repository Docs

**Files:**
- Modify: `AGENTS.md`
- Test: all `tests/paper_learning/*.py`

- [ ] **Step 1: Update repository guidelines**

Modify `AGENTS.md` by adding this section under Project Structure:

```markdown
- `skill/paper-learning/` contains the Notion-centered learning workflow orchestration layer. It consumes `paper-daily` records, publishes daily reports to Notion and Feishu, processes Notion-selected papers, writes deep-reading notes, and manages archive classification.
```

Add these commands under Build, Test, and Development Commands:

```markdown
- `python3 skill/paper-learning/scripts/run_daily_learning.py --config skill/paper-learning/templates/config.example.json --date YYYY-MM-DD --dry-run --skip-paper-daily`
  Preview the Notion/Feishu daily learning workflow without external writes.
- `python3 skill/paper-learning/scripts/process_notion_queue.py --config skill/paper-learning/templates/config.example.json --dry-run --limit 1`
  Preview selected-paper queue processing without external writes.
- `python3 -m unittest discover tests/paper_learning -v`
  Run the paper-learning unit tests.
```

- [ ] **Step 2: Run all paper-learning tests**

Run:

```bash
python3 -m unittest discover tests/paper_learning -v
```

Expected: all tests pass.

- [ ] **Step 3: Run daily CLI dry-run help and queue CLI help**

Run:

```bash
PYTHONPATH=skill/paper-learning/scripts python3 skill/paper-learning/scripts/run_daily_learning.py --help
PYTHONPATH=skill/paper-learning/scripts python3 skill/paper-learning/scripts/process_notion_queue.py --help
```

Expected: both commands print usage and exit with code 0.

- [ ] **Step 4: Run a dry-run daily pipeline using fixtures**

If `data/canonical-papers.json` exists, run:

```bash
PYTHONPATH=skill/paper-learning/scripts python3 skill/paper-learning/scripts/run_daily_learning.py --config skill/paper-learning/templates/config.example.json --date 2026-05-20 --dry-run --skip-paper-daily --limit 1
```

Expected: prints JSON with `"ok": true` and writes an artifact under `data/paper-learning/runs/2026-05-20.json`.

- [ ] **Step 5: Inspect git status**

Run:

```bash
git status --short
```

Expected: only intended implementation files are modified or staged.

- [ ] **Step 6: Commit**

```bash
git add AGENTS.md skill/paper-learning tests/paper_learning skill/paper_learning_import.py .gitignore
git commit -m "docs: document paper-learning workflow"
```

## Self-Review

Spec coverage:

- New `paper-learning` orchestration skill: Task 1.
- Stable `DailyPaperRecord` contract: Task 2 and Task 3.
- arXiv through `paper-daily`: Task 3 and Task 7.
- Hugging Face daily papers: Task 3 and Task 7.
- Notion `Paper Inbox`, daily pages, selected query, deep notes, and status updates: Task 5 and Task 9.
- Feishu parallel delivery: Task 6 and Task 7.
- HITL through `Status = Selected` and `Human Instruction`: Task 5 and Task 9.
- Semi-open archive taxonomy with `Proposed Area`: Task 8 and Task 9.
- Dry-run, limit, local artifacts, and tests: Task 7, Task 9, and Task 10.
- Existing `paper-subscribe` excluded: no task touches it.

Placeholder scan:

- The plan uses concrete paths, commands, and code blocks.
- The plan does not contain unresolved product requirements.

Type consistency:

- `DailyPaperRecord`, `DeepNote`, `ResearchArea`, `SelectedPaper`, `ClassificationResult`, and `OperationResult` are defined in Task 2 and used consistently afterward.
- CLI config types are defined in Task 2 and passed to adapters in later tasks.
- `NotionClient`, `FeishuClient`, `run_daily_pipeline`, and `process_selected_papers` signatures match their tests.
