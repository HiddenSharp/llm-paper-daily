from __future__ import annotations

import json
from urllib.request import Request, urlopen

from .config import FeishuConfig
from .models import OperationResult, ReportModel
from .report import render_markdown_report


class FeishuClient:
    def __init__(self, config: FeishuConfig):
        self.config = config

    def deliver_report(self, report: ReportModel, inbox_links: dict[str, str]) -> OperationResult:
        markdown = render_markdown_report(report, inbox_links=inbox_links)
        if self.config.dry_run or not self.config.webhook_url:
            return OperationResult(True, "dry_run", "feishu delivery skipped in dry-run", {"markdown": markdown})

        payload = {
            "msg_type": "text",
            "content": {"text": markdown[:12000]},
        }
        request = Request(
            self.config.webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        return OperationResult(True, "sent", "feishu report sent", data)
