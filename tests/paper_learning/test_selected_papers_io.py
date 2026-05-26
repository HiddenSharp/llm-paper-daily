import tempfile
import unittest
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.models import DailyPaperRecord, DeepReadingRequest, SelectedPaper
from paper_learning.selected_papers_io import (
    LocalSelectedPapersNotion,
    dump_deep_reading_request,
    dump_selected_papers,
    load_deep_reading_request,
    load_selected_papers,
)


class SelectedPapersIOTest(unittest.TestCase):
    def test_dump_and_load_selected_papers_round_trip(self):
        paper = SelectedPaper(
            notion_page_id="local-arxiv-2605.00001",
            record=_sample_record(),
            human_instruction="Focus on evals",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selected-papers.json"
            dump_selected_papers(path, [paper])
            loaded = load_selected_papers(path)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].record.paper_id, "arxiv:2605.00001")
        self.assertEqual(loaded[0].human_instruction, "Focus on evals")

    def test_local_selected_papers_notion_records_updates(self):
        notion = LocalSelectedPapersNotion([])
        notion.update_paper_status("page-1", {"Status": {"status": {"name": "Deep Reading"}}})
        result = notion.create_deep_note(
            SelectedPaper(notion_page_id="page-1", record=_sample_record(), human_instruction=""),
            _FakeNote(),
            ["area-1"],
        )
        self.assertEqual(result.data["id"], "local-note-1")
        self.assertEqual(notion.status_updates[0]["page_id"], "page-1")
        self.assertEqual(notion.note_creates[0]["area_ids"], ["area-1"])

    def test_dump_and_load_deep_reading_request_round_trip(self):
        paper = SelectedPaper(
            notion_page_id="local-arxiv-2605.00001",
            record=_sample_record(),
            human_instruction="Focus on evals",
        )
        request = DeepReadingRequest(
            date="2026-05-20",
            selector_type="explicit_paper_ids",
            candidate_source="chat_explicit",
            resolved_paper_ids=["arxiv:2605.00001"],
            human_instruction="Focus on evals",
            trigger_source="chat_manual",
            requires_confirmation=False,
            selected_papers=[paper],
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deep-reading-request.json"
            dump_deep_reading_request(path, request)
            loaded = load_deep_reading_request(path)

        self.assertEqual(loaded.selector_type, "explicit_paper_ids")
        self.assertEqual(loaded.selected_papers[0].record.paper_id, "arxiv:2605.00001")


class _FakeNote:
    def to_dict(self):
        return {"title": "x"}


def _sample_record() -> DailyPaperRecord:
    return DailyPaperRecord(
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


if __name__ == "__main__":
    unittest.main()
