"""Unit tests for tools/obsidian_sync.py."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure tools/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from obsidian_sync import ObsidianVaultManager


@pytest.fixture
def temp_vault():
    """Create a temporary directory simulating Obsidian Vault."""
    vault_dir = tempfile.mkdtemp()
    yield Path(vault_dir)
    shutil.rmtree(vault_dir)


def test_sanitize_filename(temp_vault):
    """Verify filename sanitization removes forbidden characters."""
    manager = ObsidianVaultManager(temp_vault)
    bad_name = 'Lead / Name * With : In?val"id < Chars>'
    clean = manager._sanitize_filename(bad_name)
    assert clean == "Lead  Name  With  Invalid  Chars"


def test_create_note(temp_vault):
    """Verify notes and subfolders are correctly created inside the vault."""
    manager = ObsidianVaultManager(temp_vault)
    note_content = "This is a test note."
    tags = ["test", "integration"]

    filepath = manager.create_note("TestFolder", "Sample Note", note_content, tags)

    assert filepath.exists()
    assert filepath.parent.name == "TestFolder"
    assert filepath.name == "Sample Note.md"

    with open(filepath, encoding="utf-8") as f:
        content = f.read()
        assert "title: Sample Note" in content
        assert "  - test" in content
        assert "  - integration" in content
        assert "This is a test note." in content


def test_lead_registration_and_audit_linking(temp_vault):
    """Verify lead notes are created and bidirectionally linked with audits."""
    manager = ObsidianVaultManager(temp_vault)

    lead_data = {
        "name": "Stomatology Deluxe",
        "url": "https://deluxedental.ru",
        "phone": "+7 999 123-45-67",
        "status": "Contacted",
        "geo_visibility": "45%",
        "rating": "4.2",
        "notes": "Interested in map optimization.",
    }

    lead_path = manager.register_lead(lead_data)
    assert lead_path.exists()

    audit_data = {
        "ssl": True,
        "mobile_friendly": False,
        "lcp": "3.8",
        "recommendations": "Fix LCP issues. Add alt tags.",
    }

    audit_path = manager.register_audit_report("Stomatology Deluxe", audit_data)
    assert audit_path.exists()

    # Check bidirectional linking
    with open(lead_path, encoding="utf-8") as f:
        lead_content = f.read()
        assert "Связанная информация: [[Аудит - Stomatology Deluxe]]" in lead_content

    with open(audit_path, encoding="utf-8") as f:
        audit_content = f.read()
        assert "Связанная информация: [[Stomatology Deluxe]]" in audit_content
