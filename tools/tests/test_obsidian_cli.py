from unittest.mock import MagicMock, patch

import pytest

from tools.obsidian.obsidian_cli import ObsidianCLI


@pytest.fixture
def cli():
    import os

    mock_token = os.getenv("OBSIDIAN_TEST_TOKEN", "mocked-token")
    return ObsidianCLI(token=mock_token, host="127.0.0.1", port=27124, use_https=False)


@patch("urllib.request.urlopen")
def test_create_note_success(mock_urlopen, cli):
    """Test creating a note successfully via Obsidian API."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"path": "test.md"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    result = cli.create_note("test.md", "Note Content")
    assert result is True

    # Verify call arguments
    args, _ = mock_urlopen.call_args
    req = args[0]
    assert req.get_method() == "PUT"
    assert req.headers.get("Authorization") == "Bearer mocked-token"

    assert req.headers.get("Content-type") == "text/markdown"
    assert req.data == b"Note Content"


@patch("urllib.request.urlopen")
def test_get_note_success(mock_urlopen, cli):
    """Test getting note content."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b"Hello Obsidian"
    mock_urlopen.return_value.__enter__.return_value = mock_response

    content = cli.get_note("test.md")
    assert content == "Hello Obsidian"


@patch("urllib.request.urlopen")
def test_append_daily_note_success(mock_urlopen, cli):
    """Test appending content to a daily note."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    result = cli.append_daily_note("Log item entry")
    assert result is True

    args, _ = mock_urlopen.call_args
    req = args[0]
    assert req.get_method() == "POST"
    assert req.headers.get("Content-type") == "text/markdown"
    assert req.data == b"Log item entry"


@patch("urllib.request.urlopen")
def test_search_notes(mock_urlopen, cli):
    """Test searching notes."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'[{"path": "target.md", "score": 1}]'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    results = cli.search("query string")
    assert len(results) == 1
    assert results[0]["path"] == "target.md"


@patch("urllib.request.urlopen")
def test_get_tasks(mock_urlopen, cli):
    """Test retrieving tasks from Vault."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = (
        b'{"tasks": [{"task": "Buy milk", "status": "todo"}]}'
    )
    mock_urlopen.return_value.__enter__.return_value = mock_response

    tasks = cli.get_tasks()
    assert len(tasks) == 1
    assert tasks[0]["task"] == "Buy milk"
