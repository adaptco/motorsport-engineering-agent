from __future__ import annotations

import os
from pathlib import Path


def default_session_ledger_path() -> Path:
    configured = os.environ.get("SESSION_LEDGER_DB_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path.cwd() / ".mea_tmp" / "workflow_state" / "session-ledger.db"
