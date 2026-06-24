#!/usr/bin/env python3
"""
Prompts management library and CLI tool.
Manages a local SQLite database containing AI prompts from prompts.chat.
Provides fast full-text search (FTS5) and remote synchronization.
Uses WAL mode for robust, concurrent transactional performance.
"""

import argparse
import csv
import sqlite3
import sys
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).parent.parent / "vault" / "prompts.db"


class PromptsRepository:
    """Manages SQLite-based prompts storage and FTS5 indexing."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a connection with sqlite3.Row row factory, WAL mode and timeout."""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
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


def main() -> None:
    parser = argparse.ArgumentParser(description="prompts.chat SQLite CLI tool")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="Path to SQLite database file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser(
        "act", help="Show all commands"
    )  # Subparsers require at least one subcommand
    subparsers.add_parser("sync", help="Synchronize database with remote prompts.csv")

    find_parser = subparsers.add_parser(
        "find", help="Search prompts using full-text search"
    )
    find_parser.add_argument("query", help="Search query (e.g. 'linux' or 'UX')")

    get_parser = subparsers.add_parser("get", help="Get exact prompt text by role")
    get_parser.add_argument(
        "act", help="Exact name of the role (e.g. 'Linux Terminal')"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    repo = PromptsRepository(args.db)

    if args.command == "sync":
        print("Synchronizing prompts database with GitHub...")
        try:
            count = repo.sync()
            print(f"Success! Imported {count} prompts into {repo.db_path.name}")
        except Exception as e:
            print(f"Error during synchronization: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "find":
        results = repo.search(args.query)
        if not results:
            print("No matching prompts found.")
            return

        print(f"Found {len(results)} matches:")
        print("-" * 60)
        for row in results:
            dev_badge = " [DEV]" if row["for_devs"] else ""
            print(f"* \033[1m{row['act']}\033[0m{dev_badge} (by {row['contributor']})")
        print("-" * 60)

    elif args.command == "get":
        prompt_data = repo.get_prompt(args.act)
        if not prompt_data:
            print(f"Error: Prompt for role '{args.act}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"--- ROLE: {prompt_data['act']} ---")
        print(prompt_data["prompt"])


if __name__ == "__main__":
    main()
