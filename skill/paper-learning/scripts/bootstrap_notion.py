#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import replace

from paper_learning.config import load_config
from paper_learning.notion_bootstrap import (
    bootstrap_notion_workspace,
    default_local_config_path,
    extract_notion_id,
    write_local_config,
)
from paper_learning.notion_client import NotionClient


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    cfg = replace(cfg, notion=replace(cfg.notion, dry_run=args.dry_run))

    parent_page_id = extract_notion_id(args.parent_page)
    notion = NotionClient(cfg.notion)
    result = bootstrap_notion_workspace(notion=notion, parent_page_id=parent_page_id)
    if result.ok and args.write_config:
        config_path = write_local_config(
            template_path=args.config,
            output_path=args.config_out,
            parent_page_id=parent_page_id,
            paper_inbox_database_id=result.data["paper_inbox_database_id"],
            deep_notes_database_id=result.data["deep_notes_database_id"],
            research_areas_database_id=result.data["research_areas_database_id"],
        )
        result.data["config_path"] = str(config_path)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the Notion databases required by paper-learning.")
    parser.add_argument("--config", required=True, help="Path to paper-learning config JSON template.")
    parser.add_argument("--parent-page", required=True, help="Notion parent page URL or ID.")
    parser.add_argument("--dry-run", action="store_true", help="Print the create/update payloads without writing to Notion.")
    parser.add_argument(
        "--write-config",
        action="store_true",
        help="Write a local config file populated with the created database IDs.",
    )
    parser.add_argument(
        "--config-out",
        default=str(default_local_config_path()),
        help="Local config output path used with --write-config.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
