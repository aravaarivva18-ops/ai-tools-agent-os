#!/usr/bin/env python3
"""
CLI wrapper for PromptsRepository.
Allows syncing, searching, and viewing prompts from the terminal.
"""

import argparse
import sys
from pathlib import Path

from tools.prompts_repository import PromptsRepository

DEFAULT_DB_PATH = Path(__file__).parent.parent / "vault" / "prompts.db"


def main() -> None:
    parser = argparse.ArgumentParser(description="prompts.chat SQLite CLI tool")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="Path to SQLite database file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Sync command
    subparsers.add_parser("sync", help="Synchronize database with remote prompts.csv")

    # Find command
    find_parser = subparsers.add_parser(
        "find", help="Search prompts using full-text search"
    )
    find_parser.add_argument("query", help="Search query (e.g. 'linux' or 'UX')")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get exact prompt text by role")
    get_parser.add_argument("act", help="Exact name of the role (e.g. 'Linux Terminal')")

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
