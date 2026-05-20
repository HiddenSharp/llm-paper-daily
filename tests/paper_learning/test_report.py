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
