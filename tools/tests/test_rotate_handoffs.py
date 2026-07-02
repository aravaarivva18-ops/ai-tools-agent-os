import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tools.obsidian.rotate_handoffs import rotate_logs


@pytest.fixture
def temp_handoffs_setup(monkeypatch):
    # Setup temporary directory structure
    temp_dir = tempfile.mkdtemp()
    handoffs_dir = Path(temp_dir) / "vault" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)

    # Mock load_config and get_workspace_root to target our temp directory
    monkeypatch.setattr("tools.obsidian.rotate_handoffs.load_config", lambda: {"vault": {"handoffs_dir": "vault/handoffs"}})
    monkeypatch.setattr("tools.obsidian.rotate_handoffs.get_workspace_root", lambda: temp_dir)

    yield handoffs_dir

    shutil.rmtree(temp_dir)

def test_rotate_and_compress_logs(temp_handoffs_setup):
    handoffs_dir = temp_handoffs_setup
    archive_dir = handoffs_dir / "archive"

    # 1. Create a recent handoff (should NOT be rotated)
    recent_file = handoffs_dir / "handoff_session1_2026-07-02_120000.md"
    recent_file.write_text(
        "<state_snapshot><primary_request_and_intent>Recent task</primary_request_and_intent></state_snapshot>",
        encoding="utf-8"
    )

    # 2. Create an old handoff (should be rotated and compressed)
    old_file = handoffs_dir / "handoff_session2_2026-06-20_120000.md"
    old_file.write_text(
        "<state_snapshot><primary_request_and_intent>Old task analysis</primary_request_and_intent><current_work>Done</current_work></state_snapshot>",
        encoding="utf-8"
    )
    # Set modification time to 15 days ago
    old_mtime = (datetime.now() - timedelta(days=15)).timestamp()
    os.utime(old_file, (old_mtime, old_mtime))

    # Run log rotation with 7 days threshold
    rotate_logs(days_threshold=7)

    # Check files state
    assert recent_file.exists()
    assert not old_file.exists()

    # Verify compacted history creation
    compacted_file = archive_dir / "compacted_history.md"
    assert compacted_file.exists()

    compacted_content = compacted_file.read_text(encoding="utf-8")
    assert "### Сессия 2026-06-20" in compacted_content
    assert "Old task analysis" in compacted_content
    assert "Done" in compacted_content
