import unittest

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.config import NotionConfig
from paper_learning.models import DailyPaperRecord
from paper_learning.notion_client import NotionClient, markdown_to_blocks, selected_paper_from_page


def sample_record() -> DailyPaperRecord:
    return DailyPaperRecord(
        paper_id="arxiv:2605.00001",
        source="arXiv",
        title="Agentic RL",
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
        signals={},
        provenance={},
    )


class NotionClientTest(unittest.TestCase):
    def test_build_paper_properties(self):
        client = NotionClient(NotionConfig(dry_run=True, paper_inbox_database_id="db"))

        props = client.build_paper_properties(sample_record())

        self.assertEqual(props["Title"]["title"][0]["text"]["content"], "Agentic RL")
        self.assertEqual(props["Status"]["select"]["name"], "New")
        self.assertEqual(props["Institutions"]["rich_text"][0]["text"]["content"], "Example AI Lab")
        self.assertEqual(props["Score"]["number"], 8.5)

    def test_build_paper_properties_can_omit_workflow_defaults_for_existing_pages(self):
        client = NotionClient(NotionConfig(dry_run=True, paper_inbox_database_id="db"))

        props = client.build_paper_properties(sample_record(), include_workflow_defaults=False)

        self.assertNotIn("Status", props)
        self.assertNotIn("Error", props)
        self.assertEqual(props["Paper ID"]["rich_text"][0]["text"]["content"], "arxiv:2605.00001")

    def test_dry_run_upsert_returns_operation(self):
        client = NotionClient(NotionConfig(dry_run=True, paper_inbox_database_id="db"))

        result = client.upsert_paper(sample_record())

        self.assertTrue(result.ok)
        self.assertEqual(result.status, "dry_run")
        self.assertEqual(result.data["paper_id"], "arxiv:2605.00001")
        self.assertEqual(result.data["properties"]["Paper ID"]["rich_text"][0]["text"]["content"], "arxiv:2605.00001")

    def test_markdown_to_blocks_maps_supported_lines(self):
        blocks = markdown_to_blocks("# Report\n\nOverview\n## Paper\n- Point")

        self.assertEqual([block["type"] for block in blocks], ["heading_1", "paragraph", "heading_2", "bulleted_list_item"])
        self.assertEqual(blocks[0]["heading_1"]["rich_text"][0]["text"]["content"], "Report")

    def test_selected_paper_from_page_parses_properties(self):
        page = {
            "id": "page-1",
            "properties": {
                "Title": {"title": [{"plain_text": "Agentic RL"}]},
                "Paper ID": {"rich_text": [{"plain_text": "arxiv:2605.00001"}]},
                "Source": {"select": {"name": "arXiv"}},
                "Authors": {"rich_text": [{"plain_text": "A. Author, B. Author"}]},
                "Institutions": {"rich_text": [{"plain_text": "Example AI Lab"}]},
                "Digest Summary": {"rich_text": [{"plain_text": "Digest"}]},
                "Published Date": {"date": {"start": "2026-05-20"}},
                "Run Date": {"date": {"start": "2026-05-20"}},
                "URL": {"url": "https://arxiv.org/abs/2605.00001"},
                "PDF URL": {"url": "https://arxiv.org/pdf/2605.00001"},
                "Score": {"number": 8.5},
                "Human Instruction": {"rich_text": [{"plain_text": "Focus on evals"}]},
                "Research Areas": {"relation": [{"id": "area-1"}]},
                "Deep Note": {"relation": [{"id": "note-1"}]},
            },
        }

        selected = selected_paper_from_page(page)

        self.assertEqual(selected.notion_page_id, "page-1")
        self.assertEqual(selected.record.paper_id, "arxiv:2605.00001")
        self.assertEqual(selected.record.authors, ["A. Author", "B. Author"])
        self.assertEqual(selected.human_instruction, "Focus on evals")
        self.assertEqual(selected.existing_research_area_ids, ["area-1"])
        self.assertEqual(selected.existing_deep_note_id, "note-1")


if __name__ == "__main__":
    unittest.main()
