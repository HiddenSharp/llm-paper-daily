import json
import tempfile
import unittest

from skill.paper_daily_import import add_paper_daily_path


add_paper_daily_path()

from paper_daily.summary import (
    build_summary_runtime_request,
    candidate_to_canonical,
    load_summary_payload,
    summary_artifact_path,
    validate_summary_artifacts,
)


class SummaryArtifactTest(unittest.TestCase):
    def test_load_summary_payload_requires_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = summary_artifact_path(tmp, "2605.00001")
            path.write_text(json.dumps({"summary_cn_markdown": "x"}), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "summary_en_markdown"):
                load_summary_payload(tmp, "2605.00001")

    def test_candidate_to_canonical_reads_external_summary_artifact(self):
        candidate = {
            "arxiv_id": "2605.00001",
            "title": "Example Paper",
            "abstract": "Example abstract.",
            "authors": ["A Author"],
            "abs_url": "https://arxiv.org/abs/2605.00001",
            "pdf_url": "https://arxiv.org/pdf/2605.00001",
            "priority_keyword": "Agent",
            "published": "2026-05-19T00:00:00Z",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = summary_artifact_path(tmp, "2605.00001")
            path.write_text(json.dumps({
                "institution": "Example Lab",
                "github": "https://github.com/example/repo",
                "blog": None,
                "summary_cn_markdown": "## 文章做了什么\n内容\n\n#### 总结\n中文总结。",
                "summary_en_markdown": "## What This Paper Does\nBody\n\n#### Summary\nEnglish summary.",
                "provider": "paper-daily-skill",
                "model": "conversation-runtime",
            }), encoding="utf-8")
            record = candidate_to_canonical(candidate, run_date="2026-05-19", summary_artifact_dir=tmp)

        self.assertEqual(record.paper_id, "2605.00001")
        self.assertEqual(record.institution, "Example Lab")
        self.assertEqual(record.links["github"], "https://github.com/example/repo")
        self.assertEqual(record.source_summary["provider"], "paper-daily-skill")
        self.assertEqual(record.provenance["summary_cn"], "summary-artifact")

    def test_build_summary_runtime_request_points_to_json_artifact(self):
        candidate = {"arxiv_id": "2605.00001", "title": "Example"}
        request = build_summary_runtime_request(candidate, run_date="2026-05-19", artifact_dir="data/summaries")
        self.assertEqual(request["summary_artifact_path"], "data/summaries/2605.00001.json")
        self.assertIn("paper-daily skill", request["agent_instruction"])

    def test_validate_summary_artifacts_reports_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = validate_summary_artifacts(tmp, ["2605.00001"])
        self.assertFalse(results[0]["ok"])
        self.assertIn("Missing summary artifact", results[0]["error"])


if __name__ == "__main__":
    unittest.main()
