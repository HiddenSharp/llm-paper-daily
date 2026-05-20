import unittest
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.paper_daily_adapter import load_paper_daily_records


ROOT = Path(__file__).resolve().parents[2]


class PaperDailyAdapterTest(unittest.TestCase):
    def test_load_paper_daily_records_merges_canonical_and_discovery_signals(self):
        records = load_paper_daily_records(
            canonical_path=ROOT / "tests/paper_learning/fixtures/canonical-papers.json",
            discovered_path=ROOT / "tests/paper_learning/fixtures/discovered-papers.json",
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].paper_id, "arxiv:2605.00001")
        self.assertEqual(records[0].source, "arXiv")
        self.assertEqual(records[0].institutions, "Example AI Lab")
        self.assertEqual(records[0].score, 8.5)
        self.assertEqual(records[0].signals["priority_keyword"], "Agent")


if __name__ == "__main__":
    unittest.main()
