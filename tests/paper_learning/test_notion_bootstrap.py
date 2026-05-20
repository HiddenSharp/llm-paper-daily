import json
import tempfile
import unittest
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.notion_bootstrap import (
    bootstrap_notion_workspace,
    extract_notion_id,
    write_local_config,
)


class FakeNotion:
    def __init__(self):
        self.created = []
        self.updated = []
        self.found = {}

    def create_database(self, *, parent_page_id, title, properties):
        index = len(self.created) + 1
        payload = {
            "id": f"db-{index}",
            "url": f"https://notion.test/db-{index}",
            "parent_page_id": parent_page_id,
            "title": title,
            "properties": properties,
        }
        self.created.append(payload)
        return _result(payload)

    def find_database_in_parent(self, *, parent_page_id, title):
        return self.found.get((parent_page_id, title))

    def update_database(self, database_id, properties):
        self.updated.append({"database_id": database_id, "properties": properties})
        return _result({"id": database_id})


class NotionBootstrapTest(unittest.TestCase):
    def test_extract_notion_id_from_url(self):
        value = "https://www.notion.so/AI-Paper-Reading-366f2032ccc280d6ac58efc702b665e6?source=copy_link"
        self.assertEqual(extract_notion_id(value), "366f2032-ccc2-80d6-ac58-efc702b665e6")

    def test_bootstrap_notion_workspace_creates_databases_and_relations(self):
        notion = FakeNotion()

        result = bootstrap_notion_workspace(notion=notion, parent_page_id="page-1")

        self.assertTrue(result.ok)
        self.assertEqual([item["title"] for item in notion.created], ["Research Areas", "Deep Notes", "Paper Inbox"])
        self.assertEqual(result.data["paper_inbox_database_id"], "db-3")
        self.assertEqual(result.data["deep_notes_database_id"], "db-2")
        self.assertEqual(result.data["research_areas_database_id"], "db-1")
        self.assertEqual(notion.updated[0]["database_id"], "db-3")
        self.assertIn("Research Areas", notion.updated[0]["properties"])
        self.assertEqual(notion.updated[1]["database_id"], "db-2")
        self.assertIn("Paper", notion.updated[1]["properties"])

    def test_bootstrap_notion_workspace_reuses_existing_databases(self):
        notion = FakeNotion()
        notion.found = {
            ("page-1", "Research Areas"): {"id": "db-research", "url": "https://notion.test/db-research"},
            ("page-1", "Deep Notes"): {"id": "db-deep", "url": "https://notion.test/db-deep"},
            ("page-1", "Paper Inbox"): {"id": "db-inbox", "url": "https://notion.test/db-inbox"},
        }

        result = bootstrap_notion_workspace(notion=notion, parent_page_id="page-1")

        self.assertTrue(result.ok)
        self.assertEqual(notion.created, [])
        self.assertEqual(result.data["paper_inbox_database_id"], "db-inbox")
        self.assertEqual(result.data["deep_notes_database_id"], "db-deep")
        self.assertEqual(result.data["research_areas_database_id"], "db-research")

    def test_write_local_config_populates_database_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "config.json"

            written = write_local_config(
                template_path=Path(__file__).resolve().parents[2] / "skill" / "paper-learning" / "templates" / "config.example.json",
                output_path=output_path,
                parent_page_id="page-1",
                paper_inbox_database_id="inbox-db",
                deep_notes_database_id="deep-db",
                research_areas_database_id="areas-db",
            )

            self.assertEqual(written, output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["notion"]["daily_report_parent_page_id"], "page-1")
            self.assertEqual(payload["notion"]["paper_inbox_database_id"], "inbox-db")
            self.assertEqual(payload["notion"]["deep_notes_database_id"], "deep-db")
            self.assertEqual(payload["notion"]["research_areas_database_id"], "areas-db")
            self.assertEqual(payload["notion"]["token_env"], "NOTION_TOKEN")


def _result(data):
    from paper_learning.models import OperationResult

    return OperationResult(True, "ok", "ok", data)


if __name__ == "__main__":
    unittest.main()
