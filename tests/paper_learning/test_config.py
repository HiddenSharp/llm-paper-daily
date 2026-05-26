import json
import os
import tempfile
import unittest
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.config import load_config


class ConfigTest(unittest.TestCase):
    def test_load_config_resolves_defaults_and_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({
                "paper_daily": {"repo_root": "."},
                "notion": {"token_env": "NOTION_TOKEN", "dry_run": True},
                "feishu": {"webhook_url_env": "FEISHU_WEBHOOK_URL", "dry_run": True},
                "runtime": {"artifact_dir": "data/paper-learning/runs", "dry_run": True}
            }), encoding="utf-8")
            os.environ["NOTION_TOKEN"] = "notion-secret"
            os.environ["FEISHU_WEBHOOK_URL"] = "https://example.test/webhook"

            cfg = load_config(path)

            self.assertEqual(cfg.paper_daily.repo_root, Path("."))
            self.assertEqual(cfg.paper_daily.prepare_summary_requests_script, "skill/paper-daily/scripts/prepare_summary_requests.py")
            self.assertEqual(cfg.paper_daily.select, 20)
            self.assertEqual(cfg.paper_daily.max_results_per_keyword, 50)
            self.assertEqual(cfg.notion.token, "notion-secret")
            self.assertEqual(cfg.feishu.webhook_url, "https://example.test/webhook")
            self.assertTrue(cfg.runtime.dry_run)
            self.assertEqual(cfg.deep_reading.mode, "org_artifact")
            self.assertEqual(cfg.deep_reading.org_artifact_dir, Path("data/paper-learning/deep-reading-org"))

    def test_load_config_supports_org_artifact_deep_reading_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({
                "paper_daily": {"repo_root": "."},
                "deep_reading": {
                    "mode": "org_artifact",
                    "org_artifact_dir": "data/paper-learning/ljg-org",
                },
            }), encoding="utf-8")

            cfg = load_config(path)

            self.assertEqual(cfg.deep_reading.mode, "org_artifact")
            self.assertEqual(cfg.deep_reading.org_artifact_dir, Path("data/paper-learning/ljg-org"))


if __name__ == "__main__":
    unittest.main()
