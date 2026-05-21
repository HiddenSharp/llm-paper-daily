import unittest
import tempfile
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.config import DeepReadingConfig
from paper_learning.deep_reading import (
    build_ljg_paper_runtime_request,
    deep_note_from_ljg_org,
    generate_deep_note,
    org_artifact_path,
)
from paper_learning.models import DailyPaperRecord, SelectedPaper


class DeepReadingTest(unittest.TestCase):
    def test_ljg_org_adapter_uses_paper_metadata_as_fallback(self):
        org = _sample_org("#+title: 凝练 A\n")
        paper = SelectedPaper(notion_page_id="page-1", record=_sample_record(), human_instruction="Focus on RL")

        note = deep_note_from_ljg_org(paper, org)

        self.assertEqual(note.title, "笔记：Agentic RL")
        self.assertEqual(note.paper_id, "arxiv:2605.00001")
        self.assertEqual(note.reading_focus, "Focus on RL")
        self.assertIn("## 问题", note.markdown)
        self.assertEqual(note.extra_properties["original_title"], "Agentic RL")
        self.assertEqual(note.extra_properties["authors"], "Alice, Bob")
        self.assertEqual(note.extra_properties["venue"], "arXiv 2026")
        self.assertEqual(note.extra_properties["source_url"], "https://arxiv.org/abs/2605.00001")

    def test_generate_deep_note_reads_ljg_org_artifact(self):
        paper = SelectedPaper(notion_page_id="page-1", record=_sample_record(), human_instruction="")
        with tempfile.TemporaryDirectory() as tmp:
            path = org_artifact_path(Path(tmp), paper.record.paper_id)
            path.write_text(_sample_org("#+title: 凝练 A\n"), encoding="utf-8")

            note = generate_deep_note(
                paper,
                DeepReadingConfig(mode="org_artifact", org_artifact_dir=Path(tmp)),
            )

        self.assertEqual(note.title, "笔记：Agentic RL")
        self.assertIn("## 问题", note.markdown)

    def test_generate_deep_note_reports_missing_ljg_org_artifact(self):
        paper = SelectedPaper(notion_page_id="page-1", record=_sample_record(), human_instruction="")

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError) as raised:
                generate_deep_note(
                    paper,
                    DeepReadingConfig(mode="org_artifact", org_artifact_dir=Path(tmp)),
                )

        self.assertIn("Missing ljg-paper Org artifact", str(raised.exception))

    def test_generate_deep_note_rejects_invalid_ljg_org_artifact(self):
        paper = SelectedPaper(notion_page_id="page-1", record=_sample_record(), human_instruction="")
        with tempfile.TemporaryDirectory() as tmp:
            path = org_artifact_path(Path(tmp), paper.record.paper_id)
            path.write_text("#+title: only title\n\n* 问题\nx\n", encoding="utf-8")

            with self.assertRaises(ValueError) as raised:
                generate_deep_note(
                    paper,
                    DeepReadingConfig(mode="org_artifact", org_artifact_dir=Path(tmp)),
                )

        self.assertIn("Missing required top-level sections", str(raised.exception))

    def test_build_ljg_paper_runtime_request_points_to_org_artifact(self):
        paper = SelectedPaper(notion_page_id="page-1", record=_sample_record(), human_instruction="Focus on RL")

        request = build_ljg_paper_runtime_request(
            paper,
            DeepReadingConfig(mode="org_artifact", org_artifact_dir=Path("data/org")),
        )

        self.assertEqual(request["paper"]["paper_id"], "arxiv:2605.00001")
        self.assertEqual(request["human_instruction"], "Focus on RL")
        self.assertEqual(request["org_artifact_path"], "data/org/arxiv_2605.00001.org")
        self.assertIn("Use the ljg-paper skill", request["agent_instruction"])


def _sample_record() -> DailyPaperRecord:
    return DailyPaperRecord(
        paper_id="arxiv:2605.00001",
        source="arXiv",
        title="Agentic RL",
        authors=["Alice", "Bob"],
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


def _sample_org(header: str) -> str:
    return (
        f"{header}\n"
        "* 问题\n\nbody\n\n"
        "* 翻译\n\nbody\n\n"
        "* 核心概念\n\nbody\n\n"
        "* 洞见\n\nbody\n\n"
        "* 博导审稿\n\nbody\n\n"
        "* 启发\n\nbody\n"
    )


if __name__ == "__main__":
    unittest.main()
