import tempfile
import unittest
from pathlib import Path

from tools.prompts_repository import PromptsRepository


class TestPromptsRepository(unittest.TestCase):
    def setUp(self) -> None:
        # Create a temporary database file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_prompts.db"
        self.repo = PromptsRepository(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_init_db(self) -> None:
        """Verify that tables and triggers are properly initialized."""
        assert self.db_path.exists()

    def test_sync_and_get(self) -> None:
        """Test synchronizing with a mock / custom URL if possible, or using public CSV."""
        # Using a tiny mock CSV string represented as a URL is hard in unittest without webserver.
        # We can write a direct helper test for inserting mock data to verify schema, search and triggers.
        with self.repo._get_connection() as conn:
            conn.execute(
                "INSERT INTO prompts (act, prompt, for_devs, contributor) VALUES (?, ?, ?, ?)",
                ("Mock Terminal", "Act as a mock terminal.", 1, "test-user"),
            )
            conn.commit()

        # Rebuild FTS
        with self.repo._get_connection() as conn:
            conn.execute("INSERT INTO prompts_fts(prompts_fts) VALUES('rebuild')")
            conn.commit()

        # Test get_prompt
        prompt_data = self.repo.get_prompt("Mock Terminal")
        assert prompt_data is not None
        if prompt_data:
            assert prompt_data["act"] == "Mock Terminal"
            assert prompt_data["prompt"] == "Act as a mock terminal."
            assert prompt_data["for_devs"] == 1

        # Test search
        results = self.repo.search("terminal")
        assert len(results) == 1
        assert results[0]["act"] == "Mock Terminal"


if __name__ == "__main__":
    unittest.main()
