import unittest

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.models import DailyPaperRecord, DeepReadingRequest, OperationResult, ResearchArea, SelectedPaper


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

    def test_selected_paper_serializes(self):
        selected = SelectedPaper(
            notion_page_id="local-1",
            record=DailyPaperRecord(
                paper_id="arxiv:2605.00001",
                source="arXiv",
                title="Test Paper",
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
            ),
            human_instruction="Focus on evals",
        )

        payload = selected.to_dict()
        rebuilt = SelectedPaper.from_dict(payload)

        self.assertEqual(rebuilt.notion_page_id, "local-1")
        self.assertEqual(rebuilt.record.paper_id, "arxiv:2605.00001")

    def test_deep_reading_request_serializes(self):
        selected = SelectedPaper(
            notion_page_id="local-1",
            record=DailyPaperRecord(
                paper_id="arxiv:2605.00001",
                source="arXiv",
                title="Test Paper",
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
            ),
            human_instruction="Focus on evals",
        )

        request = DeepReadingRequest(
            date="2026-05-20",
            selector_type="notion_selected_set",
            candidate_source="notion_selected",
            resolved_paper_ids=["arxiv:2605.00001"],
            human_instruction="Focus on evals",
            trigger_source="chat_manual",
            requires_confirmation=True,
            selected_papers=[selected],
        )

        rebuilt = DeepReadingRequest.from_dict(request.to_dict())

        self.assertEqual(rebuilt.selector_type, "notion_selected_set")
        self.assertEqual(rebuilt.resolved_paper_ids, ["arxiv:2605.00001"])
        self.assertEqual(rebuilt.selected_papers[0].record.paper_id, "arxiv:2605.00001")


if __name__ == "__main__":
    unittest.main()
