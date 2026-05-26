import json
import tempfile
import unittest
from pathlib import Path

from skill.paper_learning_import import add_paper_learning_path


add_paper_learning_path()

from paper_learning.config import NotionConfig, PaperDailyConfig, RuntimeConfig
from paper_learning.deep_reading_request_resolver import resolve_deep_reading_request
from paper_learning.models import DailyPaperRecord, SelectedPaper


class DeepReadingRequestResolverTest(unittest.TestCase):
    def test_resolve_notion_selected_set_filters_to_daily_report_and_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _config_fixture(tmp)
            _write_discovered(cfg.runtime.artifact_dir / "2026-05-20" / "discovered-papers.json")
            request = resolve_deep_reading_request(
                cfg=cfg,
                date="2026-05-20",
                selector_type="notion_selected_set",
                human_instruction="Focus on evals",
                trigger_source="chat_manual",
                notion=_FakeNotion(
                    selected=[
                        _selected_paper("page-1", "arxiv:2605.00001", "Paper 1"),
                        _selected_paper("page-2", "arxiv:2605.99999", "Other Day"),
                    ]
                ),
                skip_summary=True,
            )

        self.assertTrue(request.requires_confirmation)
        self.assertEqual(request.resolved_paper_ids, ["arxiv:2605.00001"])
        self.assertEqual(request.selected_papers[0].human_instruction, "Focus on evals")

    def test_resolve_explicit_paper_ids_uses_page_id_map_and_live_notion_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _config_fixture(tmp)
            _write_discovered(cfg.runtime.artifact_dir / "2026-05-20" / "discovered-papers.json")
            (cfg.runtime.artifact_dir / "2026-05-20.json").write_text(
                json.dumps(
                    {
                        "paper_results": [
                            {"data": {"id": "page-1"}},
                            {"data": {"id": "page-2"}},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            request = resolve_deep_reading_request(
                cfg=cfg,
                date="2026-05-20",
                selector_type="explicit_paper_ids",
                human_instruction="Focus on memory",
                trigger_source="chat_manual",
                notion=_FakeNotion(
                    by_page_id={
                        "page-1": _selected_paper("page-1", "arxiv:2605.00001", "Paper 1"),
                        "page-2": _selected_paper("page-2", "arxiv:2605.00002", "Paper 2"),
                    }
                ),
                skip_summary=True,
                paper_ids=["arxiv:2605.00002"],
            )

        self.assertFalse(request.requires_confirmation)
        self.assertEqual(request.resolved_paper_ids, ["arxiv:2605.00002"])
        self.assertEqual(request.selected_papers[0].notion_page_id, "page-2")
        self.assertEqual(request.selected_papers[0].human_instruction, "Focus on memory")

    def test_resolve_explicit_paper_ids_falls_back_to_url_lookup_when_page_map_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _config_fixture(tmp)
            _write_discovered(cfg.runtime.artifact_dir / "2026-05-20" / "discovered-papers.json")
            (cfg.runtime.artifact_dir / "2026-05-20.json").write_text(
                json.dumps({"paper_results": [{"data": {"id": "page-1"}}]}),
                encoding="utf-8",
            )
            request = resolve_deep_reading_request(
                cfg=cfg,
                date="2026-05-20",
                selector_type="explicit_paper_ids",
                human_instruction="",
                trigger_source="chat_manual",
                notion=_FakeNotion(
                    by_page_id={"page-1": _selected_paper("page-1", "arxiv:2605.00001", "Paper 1")},
                    by_url={"https://arxiv.org/abs/2605.00002": _selected_paper("page-2", "arxiv:2605.00002", "Paper 2")},
                ),
                skip_summary=True,
                paper_ids=["arxiv:2605.00002"],
            )

        self.assertEqual(request.resolved_paper_ids, ["arxiv:2605.00002"])
        self.assertEqual(request.selected_papers[0].notion_page_id, "page-2")

    def test_resolve_explicit_paper_ids_builds_local_selection_in_dry_run_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _config_fixture(tmp)
            _write_discovered(cfg.runtime.artifact_dir / "2026-05-20" / "discovered-papers.json")
            (cfg.runtime.artifact_dir / "2026-05-20.json").write_text(
                json.dumps({"paper_results": [{"data": {"id": "page-1"}}]}),
                encoding="utf-8",
            )
            request = resolve_deep_reading_request(
                cfg=cfg,
                date="2026-05-20",
                selector_type="explicit_paper_ids",
                human_instruction="Focus on evals",
                trigger_source="chat_manual",
                notion=_DryRunNotion(),
                skip_summary=True,
                paper_ids=["arxiv:2605.00001", "arxiv:2605.00002"],
            )

        self.assertEqual(request.resolved_paper_ids, ["arxiv:2605.00001", "arxiv:2605.00002"])
        self.assertEqual(request.selected_papers[0].notion_page_id, "page-1")
        self.assertEqual(request.selected_papers[1].notion_page_id, "local-arxiv-2605.00002")
        self.assertEqual(request.selected_papers[1].human_instruction, "Focus on evals")


class _FakeNotion:
    def __init__(self, *, selected=None, by_page_id=None, by_url=None):
        self._selected = selected or []
        self._by_page_id = by_page_id or {}
        self._by_url = by_url or {}

    def query_selected_papers(self):
        return list(self._selected)

    def get_papers_by_page_ids(self, page_ids):
        return [self._by_page_id[page_id] for page_id in page_ids]

    def find_papers_by_urls(self, urls):
        return [self._by_url[url] for url in urls if url in self._by_url]


class _Cfg:
    def __init__(self, *, repo_root: Path, artifact_dir: Path):
        self.paper_daily = PaperDailyConfig(repo_root=repo_root)
        self.runtime = RuntimeConfig(artifact_dir=artifact_dir)
        self.notion = NotionConfig(dry_run=True)


class _DryRunNotion:
    def __init__(self):
        self.config = NotionConfig(dry_run=True)


def _config_fixture(tmp: str) -> _Cfg:
    root = Path(tmp)
    return _Cfg(repo_root=root, artifact_dir=root / "runs")


def _write_discovered(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "selected": [
            {
                "arxiv_id": "2605.00001v1",
                "title": "Paper 1",
                "authors": ["A. Author"],
                "abstract": "Abstract 1",
                "abs_url": "https://arxiv.org/abs/2605.00001",
                "pdf_url": "https://arxiv.org/pdf/2605.00001",
                "published": "2026-05-20T00:00:00Z",
                "priority_keyword": "memory",
                "score": 10.0,
                "reasons": [],
                "institution_matches": [],
                "lab_matches": [],
            },
            {
                "arxiv_id": "2605.00002v1",
                "title": "Paper 2",
                "authors": ["B. Author"],
                "abstract": "Abstract 2",
                "abs_url": "https://arxiv.org/abs/2605.00002",
                "pdf_url": "https://arxiv.org/pdf/2605.00002",
                "published": "2026-05-20T00:00:00Z",
                "priority_keyword": "eval",
                "score": 9.5,
                "reasons": [],
                "institution_matches": [],
                "lab_matches": [],
            },
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _selected_paper(page_id: str, paper_id: str, title: str) -> SelectedPaper:
    return SelectedPaper(
        notion_page_id=page_id,
        record=DailyPaperRecord(
            paper_id=paper_id,
            source="arXiv",
            title=title,
            authors=[],
            institutions="",
            abstract="",
            digest_summary="Digest",
            summary_cn="",
            summary_en="",
            published_date="2026-05-20",
            run_date="2026-05-20",
            url=f"https://arxiv.org/abs/{paper_id.split(':', 1)[1]}",
            pdf_url=None,
            topic="agent",
            score=0.0,
            signals={},
            provenance={},
        ),
        human_instruction="",
    )


if __name__ == "__main__":
    unittest.main()
