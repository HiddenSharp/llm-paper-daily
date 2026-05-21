import unittest

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.org_converter import org_to_markdown, validate_ljg_paper_org


class OrgConverterTest(unittest.TestCase):
    def test_extracts_known_metadata_headers(self):
        org = (
            "#+title:      学会反成枷锁\n"
            "#+subtitle:   Reinforcement Pre-Training\n"
            "#+authors:    Alice, Bob\n"
            "#+venue:      arXiv 2026\n"
            "#+source:     https://arxiv.org/abs/2605.00001\n"
            "\n"
            "* 问题\n\n"
            "body\n"
        )

        metadata, markdown = org_to_markdown(org)

        self.assertEqual(metadata["title"], "学会反成枷锁")
        self.assertEqual(metadata["subtitle"], "Reinforcement Pre-Training")
        self.assertEqual(metadata["authors"], "Alice, Bob")
        self.assertEqual(metadata["venue"], "arXiv 2026")
        self.assertEqual(metadata["source"], "https://arxiv.org/abs/2605.00001")
        self.assertIn("## 问题", markdown)
        self.assertNotIn("#+title", markdown)

    def test_maps_heading_levels(self):
        org = "* 一\n** 二\n*** 三\n"
        _, markdown = org_to_markdown(org)
        self.assertIn("## 一", markdown)
        self.assertIn("### 二", markdown)
        self.assertIn("#### 三", markdown)

    def test_inline_single_star_bold(self):
        org = "段落里有 *重点* 和 normal\n"
        _, markdown = org_to_markdown(org)
        self.assertIn("**重点**", markdown)

    def test_file_link_becomes_image(self):
        org = "[[file:images/foo.png]]\n"
        _, markdown = org_to_markdown(org)
        self.assertIn("![](images/foo.png)", markdown)

    def test_labeled_link_becomes_inline_link(self):
        org = "[[https://example.com][示例]]\n"
        _, markdown = org_to_markdown(org)
        self.assertIn("[示例](https://example.com)", markdown)

    def test_drops_attr_org_directives(self):
        org = "#+ATTR_ORG: :width 1200\n[[file:a.png]]\n"
        _, markdown = org_to_markdown(org)
        self.assertNotIn("ATTR_ORG", markdown)
        self.assertIn("![](a.png)", markdown)

    def test_wraps_ascii_art_in_code_block(self):
        org = (
            "* 翻译\n\n"
            "  +------+\n"
            "  | node |\n"
            "  +------+\n"
            "       |\n"
            "       v\n"
            "  +------+\n"
            "  | next |\n"
            "  +------+\n"
            "\n"
            "普通段落\n"
        )

        _, markdown = org_to_markdown(org)

        self.assertIn("```text", markdown)
        self.assertIn("| node |", markdown)
        self.assertIn("| next |", markdown)
        # Code fence should be balanced.
        self.assertEqual(markdown.count("```text"), 1)
        self.assertGreaterEqual(markdown.count("```"), 2)

    def test_unknown_headers_are_still_extracted(self):
        org = "#+date:       [2026-05-20 Wed 10:00]\n#+filetags:   :paper:\n\nbody\n"
        metadata, markdown = org_to_markdown(org)
        self.assertEqual(metadata["date"], "[2026-05-20 Wed 10:00]")
        self.assertEqual(metadata["filetags"], ":paper:")
        self.assertNotIn("#+date", markdown)

    def test_validate_ljg_paper_org_accepts_complete_contract(self):
        org = (
            "#+title: 学会反成枷锁\n"
            "#+subtitle: Reinforcement Pre-Training\n"
            "#+authors: Alice, Bob\n"
            "#+venue: arXiv 2026\n"
            "#+source: https://arxiv.org/abs/2605.00001\n\n"
            "* 问题\nx\n* 翻译\nx\n* 核心概念\nx\n* 洞见\nx\n* 博导审稿\nx\n* 启发\nx\n"
        )

        metadata = validate_ljg_paper_org(org)

        self.assertEqual(metadata["title"], "学会反成枷锁")

    def test_validate_ljg_paper_org_rejects_missing_metadata(self):
        org = "* 问题\nx\n* 翻译\nx\n* 核心概念\nx\n* 洞见\nx\n* 博导审稿\nx\n* 启发\nx\n"

        with self.assertRaises(ValueError) as raised:
            validate_ljg_paper_org(org)

        self.assertIn("Missing required Org metadata", str(raised.exception))

    def test_validate_ljg_paper_org_rejects_missing_sections(self):
        org = (
            "#+title: 学会反成枷锁\n"
            "#+subtitle: Reinforcement Pre-Training\n"
            "#+authors: Alice, Bob\n"
            "#+venue: arXiv 2026\n"
            "#+source: https://arxiv.org/abs/2605.00001\n\n"
            "* 问题\nx\n* 翻译\nx\n"
        )

        with self.assertRaises(ValueError) as raised:
            validate_ljg_paper_org(org)

        self.assertIn("Missing required top-level sections", str(raised.exception))

    def test_validate_ljg_paper_org_rejects_markdown_bold(self):
        org = (
            "#+title: 学会反成枷锁\n"
            "#+subtitle: Reinforcement Pre-Training\n"
            "#+authors: Alice, Bob\n"
            "#+venue: arXiv 2026\n"
            "#+source: https://arxiv.org/abs/2605.00001\n\n"
            "* 问题\n**粗体**\n* 翻译\nx\n* 核心概念\nx\n* 洞见\nx\n* 博导审稿\nx\n* 启发\nx\n"
        )

        with self.assertRaises(ValueError) as raised:
            validate_ljg_paper_org(org)

        self.assertIn("Markdown-style bold", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
