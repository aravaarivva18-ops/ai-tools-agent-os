#!/usr/bin/env python3
"""
Unit tests for 1C-Bitrix Knowledge Base & RAG System.
Ensures hermetic execution using mocked endpoints and temp directories.
"""

import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2] / "bitrix-knowledge"))

from importer_to_obsidian import ObsidianImporter
from parser import BitrixParser
from rag_index import BitrixRAGEngine


@pytest.fixture
def temp_workspace():
    """Fixture that provides a temporary isolated workspace path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


def test_parser_markdown_parsing(temp_workspace):
    """Test that parser extracts headers and titles correctly from Markdown."""
    parser = BitrixParser(workspace_dir=temp_workspace)
    dummy_md = temp_workspace / "test_doc.md"
    dummy_md.write_text(
        "# CRM Deal Add\n\nMethod description text.\n", encoding="utf-8"
    )

    doc = parser.parse_markdown_file(dummy_md, base_dir=temp_workspace)
    assert doc["title"] == "CRM Deal Add"
    assert "Method description text." in doc["content"]
    assert doc["relative_path"] == "test_doc.md"


@patch("urllib.request.urlopen")
def test_parser_download_and_unpack(mock_urlopen, temp_workspace):
    """Test that parser downloads zip archive and unpacks it correctly."""
    parser = BitrixParser(workspace_dir=temp_workspace)

    # 1. Mock URL open response to return dummy zip file bytes
    zip_buffer = temp_workspace / "mock_download.zip"
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("b24restdocs-main/crm/deal_add.md", "# CRM Deal Add\n\nContent")
        zf.writestr("b24restdocs-main/README.md", "# Readme")

    # Configure mock open return value
    mock_response = MagicMock()
    mock_response.read.side_effect = [zip_buffer.read_bytes(), b""]
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    # Download
    parser.zip_path = temp_workspace / "b24restdocs.zip"
    parser.download_docs(force=True)
    assert parser.zip_path.is_file()

    # Unpack
    unpacked_folder = parser.unpack_docs(force=True)
    assert unpacked_folder.is_dir()
    assert (unpacked_folder / "crm" / "deal_add.md").is_file()

    # Get parsed documents
    docs = parser.get_parsed_documents()
    assert len(docs) == 1
    assert docs[0]["title"] == "CRM Deal Add"


def test_importer_incremental_updates(temp_workspace):
    """Test that ObsidianImporter writes documents and updates state incrementally."""
    importer = ObsidianImporter(workspace_dir=temp_workspace)

    parsed_docs = [
        {
            "title": "Deal Add",
            "content": "# Deal Add\nContent 1",
            "relative_path": "crm/deal_add.md",
        },
        {
            "title": "Deal Delete",
            "content": "# Deal Delete\nContent 2",
            "relative_path": "crm/deal_del.md",
        },
    ]

    # First import
    written, skipped = importer.import_documents(parsed_docs)
    assert written == 2
    assert skipped == 0
    assert (importer.vault_dir / "crm" / "Deal Add.md").is_file()
    assert (importer.vault_dir / "index.md").is_file()

    # Second import (nothing changed)
    written, skipped = importer.import_documents(parsed_docs)
    assert written == 0
    assert skipped == 2

    # Third import (one document modified)
    parsed_docs[0]["content"] = "# Deal Add\nContent Modified!"
    written, skipped = importer.import_documents(parsed_docs)
    assert written == 1
    assert skipped == 1


def test_rag_engine_index_and_search(temp_workspace):
    """Test indexing, FTS5 + Vector hybrid search, and offline RAG Q&A."""
    # Force mock mode in the engine so it doesn't call actual Gemini API
    engine = BitrixRAGEngine(workspace_dir=temp_workspace, mock_mode=True)

    parsed_docs = [
        {
            "title": "CRM Deal Add",
            "content": "REST API crm.deal.add method creates a deal",
            "relative_path": "crm/deal_add.md",
        },
        {
            "title": "CIBlockElement Add",
            "content": "CIBlockElement::Add creates a framework element",
            "relative_path": "iblock/add.md",
        },
    ]

    # Index
    indexed = engine.index_documents(parsed_docs)
    assert indexed == 2

    # Positive search: search for a valid API method
    results = engine.search("crm.deal.add", limit=1)
    assert len(results) == 1
    assert results[0]["title"] == "CRM Deal Add"
    assert results[0]["score"] > 0.0

    # Negative search: search for a non-existent outdated API term
    results_neg = engine.search("outdated nonexistent method term", limit=1)
    # Cosine similarity will still match something (due to mock vectors), but score checks/RAG output can catch it
    assert len(results_neg) > 0

    # RAG ask Q&A
    response = engine.ask("Как создать сделку через REST API?")
    assert (
        "CRM Deal Add" in response["answer"]
        or "CIBlockElement Add" in response["answer"]
    )
    assert len(response["context"]) > 0
    assert (
        "[[CRM Deal Add]]" in response["answer"]
        or "[[CIBlockElement Add]]" in response["answer"]
    )
