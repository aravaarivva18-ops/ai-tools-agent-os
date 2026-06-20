"""
PromptsRepository manages a local SQLite database containing AI prompts from prompts.chat.
Provides fast full-text search and synchronization capabilities.
"""

import csv
import sqlite3
import urllib.request
from pathlib import Path
from typing import Any


class PromptsRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a connection with sqlite3.Row row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Creates the prompts table and FTS index if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    act TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    for_devs INTEGER DEFAULT 0,
                    contributor TEXT
                )
            """)
            # Create FTS5 virtual table for efficient search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS prompts_fts USING fts5(
                    act,
                    prompt,
                    content='prompts',
                    content_rowid='rowid'
                )
            """)
            # Create triggers to keep FTS index synchronized
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS prompts_ai AFTER INSERT ON prompts BEGIN
                    INSERT INTO prompts_fts(rowid, act, prompt) VALUES (new.rowid, new.act, new.prompt);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS prompts_ad AFTER DELETE ON prompts BEGIN
                    INSERT INTO prompts_fts(prompts_fts, rowid, act, prompt) VALUES('delete', old.rowid, old.act, old.prompt);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS prompts_au AFTER UPDATE ON prompts BEGIN
                    INSERT INTO prompts_fts(prompts_fts, rowid, act, prompt) VALUES('delete', old.rowid, old.act, old.prompt);
                    INSERT INTO prompts_fts(rowid, act, prompt) VALUES (new.rowid, new.act, new.prompt);
                END
            """)
            conn.commit()

    def sync(
        self,
        csv_url: str = "https://raw.githubusercontent.com/f/awesome-chatgpt-prompts/main/prompts.csv",
    ) -> int:
        """Downloads the prompts CSV from GitHub and updates the local SQLite database.

        Returns:
            The number of imported prompts.
        """
        req = urllib.request.Request(
            csv_url,
            headers={"User-Agent": "Mozilla/5.0 (Antigravity AI Agent)"},
        )
        with urllib.request.urlopen(req) as response:  # nosec B310
            csv_data = response.read().decode("utf-8")

        # Increase field size limit to support long prompts
        csv.field_size_limit(10 * 1024 * 1024)
        reader = csv.DictReader(csv_data.splitlines())

        imported = 0
        with self._get_connection() as conn:
            # Clear old records to avoid duplication/stale data
            conn.execute("DELETE FROM prompts")
            conn.execute("DELETE FROM prompts_fts")

            for row in reader:
                act = row.get("act")
                prompt = row.get("prompt")
                if not act or not prompt:
                    continue

                # Parse boolean flag for devs
                for_devs_raw = str(row.get("for_devs", "FALSE")).upper()
                for_devs = 1 if for_devs_raw in ("TRUE", "1") else 0
                contributor = row.get("contributor", "")

                conn.execute(
                    """
                    INSERT INTO prompts (act, prompt, for_devs, contributor)
                    VALUES (?, ?, ?, ?)
                """,
                    (act, prompt, for_devs, contributor),
                )
                imported += 1

            conn.commit()

        # Rebuild FTS index just in case
        with self._get_connection() as conn:
            conn.execute("INSERT INTO prompts_fts(prompts_fts) VALUES('rebuild')")
            conn.commit()

        return imported

    def search(self, query: str) -> list[dict[str, Any]]:
        """Performs full-text search on prompts.

        Returns:
            List of dictionaries matching the query.
        """
        if not query.strip():
            return []

        # Sanitize query for FTS5 (avoid syntax errors with raw quotes or operators)
        clean_query = query.replace('"', '""')

        sql = """
            SELECT p.act, p.prompt, p.for_devs, p.contributor
            FROM prompts p
            JOIN prompts_fts f ON p.rowid = f.rowid
            WHERE prompts_fts MATCH ?
            ORDER BY f.rank
            LIMIT 20
        """
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (clean_query,))
            return [dict(row) for row in cursor.fetchall()]

    def get_prompt(self, act: str) -> dict[str, Any] | None:
        """Retrieves a single prompt by its exact role name (case-insensitive)."""
        sql = """
            SELECT act, prompt, for_devs, contributor
            FROM prompts
            WHERE LOWER(act) = LOWER(?)
        """
        with self._get_connection() as conn:
            cursor = conn.execute(sql, (act,))
            row = cursor.fetchone()
            return dict(row) if row else None
