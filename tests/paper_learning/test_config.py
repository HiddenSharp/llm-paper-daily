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
            self.assertEqual(cfg.notion.token, "notion-secret")
            self.assertEqual(cfg.feishu.webhook_url, "https://example.test/webhook")
            self.assertTrue(cfg.runtime.dry_run)


if __name__ == "__main__":
    unittest.main()
