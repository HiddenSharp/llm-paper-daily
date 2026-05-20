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
        selected = SelectedPaper(notion_page_id="page-1", record=_sample_record(), human_instruction="Focus on RL")
        notion = FakeNotion([selected])

        result = process_selected_papers(
            notion=notion,
            deep_reader=_deep_reader,
            active_areas=[ResearchArea(name="Agent RL", aliases=["agentic rl"], description="", notion_page_id="area-1")],
            limit=1,
        )

        self.assertTrue(result.ok)
        self.assertEqual(notion.notes, [("arxiv:2605.00001", ["area-1"])])
        self.assertTrue(any(update[1]["Status"]["select"]["name"] == "Deep Reading" for update in notion.status_updates))
        self.assertTrue(any(update[1]["Status"]["select"]["name"] == "Deep Read Done" for update in notion.status_updates))
        self.assertTrue(any(update[1].get("Research Areas") == {"relation": [{"id": "area-1"}]} for update in notion.status_updates))
        self.assertTrue(any(update[1].get("Deep Note") == {"relation": [{"id": "note-1"}]} for update in notion.status_updates))

    def test_process_selected_papers_preserves_manual_research_areas(self):
        selected = SelectedPaper(
            notion_page_id="page-1",
            record=_sample_record(),
            human_instruction="Focus on RL",
            existing_research_area_ids=["manual-area"],
        )
        notion = FakeNotion([selected])

        result = process_selected_papers(
            notion=notion,
            deep_reader=_deep_reader,
            active_areas=[ResearchArea(name="Agent RL", aliases=["agentic rl"], description="", notion_page_id="area-1")],
        )

        self.assertTrue(result.ok)
        final_update = notion.status_updates[-1][1]
        self.assertNotIn("Research Areas", final_update)
        self.assertEqual(notion.notes, [("arxiv:2605.00001", ["manual-area"])])

    def test_process_selected_papers_skips_existing_deep_note_without_force(self):
        selected = SelectedPaper(
            notion_page_id="page-1",
            record=_sample_record(),
            human_instruction="Focus on RL",
            existing_deep_note_id="note-existing",
        )
        notion = FakeNotion([selected])

        result = process_selected_papers(
            notion=notion,
            deep_reader=_deep_reader,
            active_areas=[],
        )

        self.assertTrue(result.ok)
        self.assertEqual(notion.notes, [])
        self.assertEqual(notion.status_updates, [])
        self.assertEqual(result.data["processed"], [{"paper_id": "arxiv:2605.00001", "status": "skipped_existing_deep_note"}])

    def test_process_selected_papers_marks_failure(self):
        selected = SelectedPaper(notion_page_id="page-1", record=_sample_record(), human_instruction="Focus on RL")
        notion = FakeNotion([selected])

        result = process_selected_papers(
            notion=notion,
            deep_reader=lambda paper: (_ for _ in ()).throw(RuntimeError("reader failed")),
            active_areas=[],
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.status, "failed")
        self.assertEqual(notion.status_updates[-1][1]["Status"]["select"]["name"], "Failed")
        self.assertEqual(notion.status_updates[-1][1]["Error"]["rich_text"][0]["text"]["content"], "reader failed")


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


def _deep_reader(paper: SelectedPaper) -> DeepNote:
    return DeepNote(
        title="Deep Note: Agentic RL",
        paper_id=paper.record.paper_id,
        reading_focus=paper.human_instruction,
        markdown="Agentic RL details",
        contribution_type="Method",
        method_tags=["Agent RL"],
        proposed_area="Agent RL",
        archive_confidence="High",
    )


if __name__ == "__main__":
    unittest.main()
