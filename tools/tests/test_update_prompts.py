#!/usr/bin/env python3
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

import tools.update_gem_bot_prompts as ugbp


@pytest.fixture
def temp_prompts_db():
    """Sets up a temporary SQLite database for prompts testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    db_path = Path(path)

    # Save original DB path
    orig_db_path = ugbp.DB_PATH
    ugbp.DB_PATH = db_path

    # Initialize schema
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            act TEXT PRIMARY KEY,
            prompt TEXT NOT NULL,
            for_devs INTEGER DEFAULT 0,
            contributor TEXT
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS prompts_fts USING fts5(
            act,
            prompt,
            content='prompts',
            content_rowid='rowid'
        )
    """)
    conn.commit()
    conn.close()

    yield db_path

    # Teardown
    os.close(fd)
    if db_path.exists():
        db_path.unlink()
    ugbp.DB_PATH = orig_db_path


def test_update_gem_bot_prompts(temp_prompts_db):
    # Run the main import logic using our temporary database
    ugbp.main()

    # Connect to the temp database and verify imports
    conn = sqlite3.connect(temp_prompts_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check for Constitution
    cursor.execute("SELECT * FROM prompts WHERE act = ?", ("Antigravity Constitution",))
    const_row = cursor.fetchone()
    assert const_row is not None
    assert "🧬 GEMINI_ANTIGRAVITY" in const_row["prompt"]

    # Check for Student Guide
    cursor.execute("SELECT * FROM prompts WHERE act = ?", ("Student Guide",))
    guide_row = cursor.fetchone()
    assert guide_row is not None
    assert "Руководство" in guide_row["prompt"]

    # Check for Claude Workspace Rules
    cursor.execute("SELECT * FROM prompts WHERE act = ?", ("Claude Workspace Rules",))
    claude_row = cursor.fetchone()
    assert claude_row is not None
    assert "AI Tools Workspace" in claude_row["prompt"]

    # Check for DOX Agent Contracts
    cursor.execute("SELECT * FROM prompts WHERE act = ?", ("DOX Agent Contracts",))
    dox_row = cursor.fetchone()
    assert dox_row is not None
    assert "DOX" in dox_row["prompt"]

    # Check for Gemini Bot Knowledge Base
    cursor.execute(
        "SELECT * FROM prompts WHERE act = ?", ("Gemini Bot Knowledge Base",)
    )
    kb_row = cursor.fetchone()
    assert kb_row is not None
    assert "База знаний" in kb_row["prompt"]

    # Check for Gemini Bot Developer Mode
    cursor.execute(
        "SELECT * FROM prompts WHERE act = ?", ("Gemini Bot Developer Mode",)
    )
    dev_mode_row = cursor.fetchone()
    assert dev_mode_row is not None
    assert "Developer" in dev_mode_row["prompt"] or "Lead Software Engineer" in dev_mode_row["prompt"]

    # Check for Gemini Bot Prompt Architect Mode
    cursor.execute(
        "SELECT * FROM prompts WHERE act = ?", ("Gemini Bot Prompt Architect Mode",)
    )
    arch_mode_row = cursor.fetchone()
    assert arch_mode_row is not None
    assert "Prompt Architect" in arch_mode_row["prompt"]

    # Check for Gemini Bot Prompt Generator Mode
    cursor.execute(
        "SELECT * FROM prompts WHERE act = ?", ("Gemini Bot Prompt Generator Mode",)
    )
    gen_mode_row = cursor.fetchone()
    assert gen_mode_row is not None
    assert "Prompt Generator" in gen_mode_row["prompt"]

    # Check for Gemini Bot Audit Specialist Mode
    cursor.execute(
        "SELECT * FROM prompts WHERE act = ?", ("Gemini Bot Audit Specialist Mode",)
    )
    audit_mode_row = cursor.fetchone()
    assert audit_mode_row is not None
    assert "Systems Auditor" in audit_mode_row["prompt"] or "AUDIT AND SYSTEM" in audit_mode_row["prompt"]

    # Check for ADRs
    cursor.execute("SELECT * FROM prompts WHERE act LIKE 'ADR:%'")
    adr_rows = cursor.fetchall()
    assert len(adr_rows) > 0

    # Check one specific ADR content
    has_n8n_adr = any("n8n" in row["act"].lower() for row in adr_rows)
    assert has_n8n_adr, "Should import n8n evaluation ADR"

    conn.close()


def test_update_prompts_missing_db(capsys):
    """Test that main() handles a missing database gracefully."""
    orig_db_path = ugbp.DB_PATH
    ugbp.DB_PATH = Path("/nonexistent/path/to/prompts.db")

    try:
        ugbp.main()
        captured = capsys.readouterr()
        assert "Error: Database" in captured.out
    finally:
        ugbp.DB_PATH = orig_db_path


def test_update_prompts_missing_files(temp_prompts_db, capsys):
    """Test that missing source files are skipped and don't raise errors."""
    orig_desktop = ugbp.DESKTOP_DIR
    orig_attachments = ugbp.ATTACHMENTS_DIR

    # Point directories to an empty temporary path
    empty_dir = Path("/nonexistent/empty/dir")
    ugbp.DESKTOP_DIR = empty_dir
    ugbp.ATTACHMENTS_DIR = empty_dir

    try:
        ugbp.main()
        captured = capsys.readouterr()
        # Verify that warning messages are printed for skipped files
        assert "Warning: File" in captured.out
    finally:
        ugbp.DESKTOP_DIR = orig_desktop
        ugbp.ATTACHMENTS_DIR = orig_attachments
