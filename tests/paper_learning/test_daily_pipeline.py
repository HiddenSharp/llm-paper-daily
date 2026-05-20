import json
import tempfile
import unittest
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.daily_pipeline import run_daily_pipeline
from paper_learning.models import DailyPaperRecord, OperationResult


class FakeNotion:
    def __init__(self):
        self.upserted = []

    def upsert_paper(self, record):
        self.upserted.append(record.paper_id)
        return OperationResult(
            True,
            "dry_run",
            "ok",
            {"paper_id": record.paper_id, "url": f"https://notion.test/{record.paper_id}"},
        )

    def create_daily_report(self, report, inbox_links):
        return OperationResult(True, "dry_run", "report", {"title": report.title, "links": inbox_links})


class FakeFeishu:
    def deliver_report(self, report, inbox_links):
        return OperationResult(True, "dry_run", "feishu", {"title": report.title, "links": inbox_links})


class DailyPipelineTest(unittest.TestCase):
    def test_run_daily_pipeline_writes_artifact(self):
        record = _sample_record()
        notion = FakeNotion()

        with tempfile.TemporaryDirectory() as tmp:
            result = run_daily_pipeline(
                date="2026-05-20",
                records=[record],
                notion=notion,
                feishu=FakeFeishu(),
                artifact_dir=Path(tmp),
            )

            self.assertTrue(result.ok)
            self.assertEqual(notion.upserted, ["arxiv:2605.00001"])
            artifact = Path(tmp) / "2026-05-20.json"
            self.assertTrue(artifact.exists())
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            self.assertEqual(payload["paper_count"], 1)
            self.assertEqual(payload["notion_report"]["data"]["links"]["arxiv:2605.00001"], "https://notion.test/arxiv:2605.00001")
            self.assertIn("arxiv:2605.00001", artifact.read_text(encoding="utf-8"))

    def test_run_daily_pipeline_reports_failure_but_still_writes_artifact(self):
        class FailingFeishu:
            def deliver_report(self, report, inbox_links):
                return OperationResult(False, "failed", "no delivery", {})

        with tempfile.TemporaryDirectory() as tmp:
            result = run_daily_pipeline(
                date="2026-05-20",
                records=[_sample_record()],
                notion=FakeNotion(),
                feishu=FailingFeishu(),
                artifact_dir=Path(tmp),
            )

            self.assertFalse(result.ok)
            self.assertEqual(result.status, "failed")
            self.assertTrue((Path(tmp) / "2026-05-20.json").exists())


def _sample_record() -> DailyPaperRecord:
    return DailyPaperRecord(
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


if __name__ == "__main__":
    unittest.main()
