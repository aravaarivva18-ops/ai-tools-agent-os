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
        "gemini_bot_knowledge_base.md": "Gemini Bot Knowledge Base",
        "gem_bot_audit_specialist.md": "Gem Bot Audit Specialist",
        "gem_bot_prompt_architect.md": "Gem Bot Prompt Architect",
        "gem_bot_prompt_generator.md": "Gem Bot Prompt Generator",
    }

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        for filename, role_name in files_to_import.items():
            file_path = DESKTOP_DIR / filename
            if not file_path.exists():
                print(f"Warning: File {file_path} not found. Skipping.")
                continue

            content = file_path.read_text(encoding="utf-8")

            # For gemini_bot_knowledge_base.md, we also extract the System Prompt section
            if filename == "gemini_bot_knowledge_base.md":
                # Save the whole knowledge base
                cursor.execute(
                    "INSERT OR REPLACE INTO prompts (act, prompt, for_devs, contributor) VALUES (?, ?, ?, ?)",
                    (role_name, content, 1, "rus"),
                )
                print(f"Imported/Updated: {role_name}")

                # Extract and save only the System Instructions (Section 6)
                sys_prompt_match = content.split(
                    "## ⚙️ 6. Системная инструкция для внешнего Gemini-бота (System Prompt)"
                )
                if len(sys_prompt_match) > 1:
                    # Get content after heading, strip leading markdown code blocks if any
                    sys_prompt_content = sys_prompt_match[1].strip()
                    # If it contains code block markers, let's clean it up slightly or keep it as is
                    # Keep everything from ```markdown to ``` at the end (or just the content inside)
                    # Let's extract the markdown code block content if it exists
                    import re

                    code_block_match = re.search(
                        r"```markdown\s+(.*?)\s+```", sys_prompt_content, re.DOTALL
                    )
                    if code_block_match:
                        sys_prompt_content = code_block_match.group(1).strip()

                    cursor.execute(
                        "INSERT OR REPLACE INTO prompts (act, prompt, for_devs, contributor) VALUES (?, ?, ?, ?)",
                        ("Gemini Bot System Prompt", sys_prompt_content, 1, "rus"),
                    )
                    print("Imported/Updated: Gemini Bot System Prompt")
            else:
                # Save standard role
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
