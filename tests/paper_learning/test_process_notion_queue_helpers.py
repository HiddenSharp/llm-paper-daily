import unittest
from typing import Optional

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

import process_notion_queue as queue_script
from paper_learning.models import DailyPaperRecord, SelectedPaper


class ProcessNotionQueueHelpersTest(unittest.TestCase):
    def test_readiness_targets_skip_existing_deep_note_without_force(self):
        selected = [
            _paper("page-1", "arxiv:2605.00001", deep_note_id="note-1"),
            _paper("page-2", "arxiv:2605.00002"),
        ]

        targets = queue_script._readiness_targets(selected, force=False)

        self.assertEqual([paper.record.paper_id for paper in targets], ["arxiv:2605.00002"])

    def test_refresh_selected_from_notion_uses_live_state_but_preserves_requested_instruction(self):
        requested = [
            _paper("page-1", "arxiv:2605.00001", instruction="Focus on evals"),
        ]
        notion = _FakeNotion([
            _paper("page-1", "arxiv:2605.00001", instruction="", deep_note_id="note-live", area_ids=["area-live"]),
        ])

        refreshed = queue_script._refresh_selected_from_notion(notion, requested)

        self.assertEqual(refreshed[0].human_instruction, "Focus on evals")
        self.assertEqual(refreshed[0].existing_deep_note_id, "note-live")
        self.assertEqual(refreshed[0].existing_research_area_ids, ["area-live"])


class _FakeNotion:
    def __init__(self, papers):
        self._papers = papers

    def get_papers_by_page_ids(self, page_ids):
        by_page_id = {paper.notion_page_id: paper for paper in self._papers}
        return [by_page_id[page_id] for page_id in page_ids]


def _paper(page_id: str, paper_id: str, instruction: str = "", deep_note_id: Optional[str] = None, area_ids=None) -> SelectedPaper:
    return SelectedPaper(
        notion_page_id=page_id,
        record=DailyPaperRecord(
            paper_id=paper_id,
            source="arXiv",
            title="Paper",
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
            topic="",
            score=0.0,
            signals={},
            provenance={},
        ),
        human_instruction=instruction,
        existing_research_area_ids=list(area_ids or []),
        existing_deep_note_id=deep_note_id,
    )


if __name__ == "__main__":
    unittest.main()
