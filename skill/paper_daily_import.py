from __future__ import annotations

import sys
from pathlib import Path


def add_paper_daily_path() -> None:
    root = Path(__file__).resolve().parents[1]
    scripts = root / "skill" / "paper-daily" / "scripts"
    value = str(scripts)
    if value not in sys.path:
        sys.path.insert(0, value)
