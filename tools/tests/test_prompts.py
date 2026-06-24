import tempfile
from pathlib import Path

import pytest

from tools.prompts import PromptsRepository


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_prompts.db"
        repo = PromptsRepository(db_path)
        yield repo, db_path


def test_init_db(temp_repo):
    """Verify that tables and triggers are properly initialized."""
    _, db_path = temp_repo
    assert db_path.exists()


def test_sync_and_get(temp_repo):
    """Test inserting mock data to verify schema, search and triggers."""
    repo, _ = temp_repo
    with repo._get_connection() as conn:
        conn.execute(
            "INSERT INTO prompts (act, prompt, for_devs, contributor) VALUES (?, ?, ?, ?)",
            ("Mock Terminal", "Act as a mock terminal.", 1, "test-user"),
        )
        conn.commit()

    # Rebuild FTS
    with repo._get_connection() as conn:
        conn.execute("INSERT INTO prompts_fts(prompts_fts) VALUES('rebuild')")
        conn.commit()

    # Test get_prompt
    prompt_data = repo.get_prompt("Mock Terminal")
    assert prompt_data is not None
    assert prompt_data["act"] == "Mock Terminal"
    assert prompt_data["prompt"] == "Act as a mock terminal."
    assert prompt_data["for_devs"] == 1

    # Test search
    results = repo.search("terminal")
    assert len(results) == 1
    assert results[0]["act"] == "Mock Terminal"
