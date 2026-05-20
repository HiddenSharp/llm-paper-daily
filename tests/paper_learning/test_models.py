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
