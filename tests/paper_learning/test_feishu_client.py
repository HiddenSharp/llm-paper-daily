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
