import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skill" / "paper-learning" / "SKILL.md"
CONFIG = ROOT / "skill" / "paper-learning" / "templates" / "config.example.json"
EVALS = ROOT / "skill" / "paper-learning" / "evals" / "evals.json"


class SkillContractTest(unittest.TestCase):
    def test_skill_doc_has_trigger_and_commands(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("name: paper-learning", text)
        self.assertIn("Notion", text)
        self.assertIn("Feishu", text)
        self.assertIn("run_daily_learning.py", text)
        self.assertIn("process_notion_queue.py", text)

    def test_config_and_evals_exist(self):
        self.assertTrue(CONFIG.exists())
        self.assertTrue(EVALS.exists())


if __name__ == "__main__":
    unittest.main()
