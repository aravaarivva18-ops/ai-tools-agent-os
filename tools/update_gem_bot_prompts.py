#!/usr/bin/env python3
"""Script to import/update gem bot prompts from Desktop into vault/prompts.db."""

import sqlite3
from pathlib import Path

DESKTOP_DIR = Path("/Users/rus/Desktop")
DB_PATH = Path("/Users/rus/ai-tools/vault/prompts.db")


def main() -> None:
    if not DB_PATH.exists():
        print(f"Error: Database {DB_PATH} not found.")
        return

    # Check source files on Desktop
    files_to_import = {
        "gemini_universal_bot.md": [
            "Gemini Universal Bot",
            "Gemini Bot Knowledge Base",
            "Gemini Bot System Prompt",
        ],
        "gemini_bot_instructions.md": [
            "Gemini Bot Instructions",
            "Gemini Bot Usage Instructions",
        ],
    }

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        for filename, role_names in files_to_import.items():
            file_path = DESKTOP_DIR / filename
            if not file_path.exists():
                print(f"Warning: File {file_path} not found. Skipping.")
                continue

            content = file_path.read_text(encoding="utf-8")

            for role_name in role_names:
                cursor.execute(
                    "INSERT OR REPLACE INTO prompts (act, prompt, for_devs, contributor) VALUES (?, ?, ?, ?)",
                    (role_name, content, 1, "rus"),
                )
                print(f"Imported/Updated: {role_name}")

        # Import Antigravity Constitution
        constitution_path = Path("/Users/rus/GEMINI_ANTIGRAVITY.md")
        if constitution_path.exists():
            content = constitution_path.read_text(encoding="utf-8")
            cursor.execute(
                "INSERT OR REPLACE INTO prompts (act, prompt, for_devs, contributor) VALUES (?, ?, ?, ?)",
                ("Antigravity Constitution", content, 1, "rus"),
            )
            print("Imported/Updated: Antigravity Constitution")
        else:
            print(f"Warning: Constitution not found at {constitution_path}")

        # Import ADR files from vault/adr/
        adr_dir = Path("/Users/rus/ai-tools/vault/adr")
        if adr_dir.exists():
            for adr_file in adr_dir.glob("*.md"):
                content = adr_file.read_text(encoding="utf-8")
                # Parse header
                lines = content.splitlines()
                first_line = lines[0] if lines else ""
                title = (
                    first_line.replace("#", "").strip()
                    if first_line.startswith("#")
                    else adr_file.stem
                )

                role_name = f"ADR: {title}"
                cursor.execute(
                    "INSERT OR REPLACE INTO prompts (act, prompt, for_devs, contributor) VALUES (?, ?, ?, ?)",
                    (role_name, content, 1, "rus"),
                )
                print(f"Imported/Updated: {role_name}")

        conn.commit()

        # Rebuild FTS index
        cursor.execute("INSERT INTO prompts_fts(prompts_fts) VALUES('rebuild')")
        conn.commit()
        print("Successfully rebuilt FTS index.")

    except Exception as e:
        conn.rollback()
        print(f"Error during import: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
