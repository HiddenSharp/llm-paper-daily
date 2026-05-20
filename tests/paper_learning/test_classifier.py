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
        areas = [ResearchArea(name="Agent RL", aliases=["agentic RL"], description="", notion_page_id="area-1")]

        result = classify_note(note, areas)

        self.assertEqual(result.area_ids, ["area-1"])
        self.assertEqual(result.review_status, "Auto Accepted")

    def test_classify_note_matches_area_without_page_id_needs_review(self):
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

        self.assertEqual(result.area_ids, [])
        self.assertEqual(result.proposed_area, "Agent RL")
        self.assertEqual(result.review_status, "Needs Human Review")

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
