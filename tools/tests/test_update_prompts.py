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

    # Check for ADRs
    cursor.execute("SELECT * FROM prompts WHERE act LIKE 'ADR:%'")
    adr_rows = cursor.fetchall()
    assert len(adr_rows) > 0

    # Check one specific ADR content
    has_n8n_adr = any("n8n" in row["act"].lower() for row in adr_rows)
    assert has_n8n_adr, "Should import n8n evaluation ADR"

    conn.close()
