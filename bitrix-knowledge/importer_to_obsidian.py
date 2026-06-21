#!/usr/bin/env python3
"""
Bitrix Knowledge Base Importer to Obsidian.
Imports parsed markdown documents into the Obsidian Vault with incremental updates.
"""

import hashlib
import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class ObsidianImporter:
    def __init__(self, workspace_dir: str | Path | None = None):
        """Initializes importer configuration."""
        if workspace_dir is None:
            self.root = Path(os.getcwd()) / "bitrix-knowledge"
            self.vault_dir = Path(os.getcwd()) / "vault" / "bitrix-docs"
        else:
            self.root = Path(workspace_dir)
            self.vault_dir = self.root.parent / "vault" / "bitrix-docs"

        self.state_file = self.root / "import_state.json"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensures that the target vault directory exists."""
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> dict[str, str]:
        """Loads import state mapping filename to hash."""
        if self.state_file.is_file():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(
                    f"Failed to load state file: {e}. Starting with clean state."
                )
        return {}

    def _save_state(self, state: dict[str, str]) -> None:
        """Saves current import state mapping."""
        try:
            self.state_file.write_text(
                json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Failed to save state file: {e}")

    @staticmethod
    def clean_filename(title: str) -> str:
        """Sanitizes file name for Obsidian by removing illegal characters."""
        # Obsidian doesn't like: \ / : * ? " < > |
        cleaned = re.sub(r'[\\/:*?"<>|]', " ", title)
        # Compact spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or "Untitled Note"

    def import_documents(self, parsed_docs: list[dict[str, str]]) -> tuple[int, int]:
        """Imports documents incrementally to Obsidian vault.

        Args:
            parsed_docs: List of parsed document dictionaries.

        Returns:
            tuple: (written_count, skipped_count)
        """
        state = self._load_state()
        written = 0
        skipped = 0

        # Maintain a list of all documents to build the index note
        index_entries = []

        logger.info(
            f"Importing {len(parsed_docs)} documents to Obsidian at {self.vault_dir}..."
        )
        for doc in parsed_docs:
            title = doc["title"]
            content = doc["content"]
            rel_path = doc["relative_path"]

            # Compute SHA256 hash of the content to check for changes
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            # Normalize file path inside Obsidian vault
            # Retain relative directory structure if present
            sub_dir_path = Path(rel_path).parent
            safe_title = self.clean_filename(title)
            target_file_path = self.vault_dir / sub_dir_path / f"{safe_title}.md"

            # Register in index entries
            vault_relative_md_link = f"[[{sub_dir_path / safe_title}]]"
            index_entries.append((title, vault_relative_md_link, str(sub_dir_path)))

            # Check if file has changed
            state_key = str(sub_dir_path / f"{safe_title}.md")
            if target_file_path.is_file() and state.get(state_key) == content_hash:
                skipped += 1
                continue

            # Ensure subdirectories inside vault exist
            target_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepend frontmatter metadata for Obsidian
            frontmatter = (
                "---\n"
                "tags:\n"
                "  - bitrix\n"
                "  - api\n"
                "  - docs\n"
                f'title: "{title}"\n'
                f'original_path: "{rel_path}"\n'
                "---\n\n"
            )

            # Write document with frontmatter
            try:
                target_file_path.write_text(frontmatter + content, encoding="utf-8")
                state[state_key] = content_hash
                written += 1
            except Exception as e:
                logger.error(f"Failed to write note {target_file_path}: {e}")

        # Build index.md inside vault
        self._build_index_note(index_entries)

        self._save_state(state)
        logger.info(
            f"Import finished. Written: {written}, Skipped (unchanged): {skipped}"
        )
        return written, skipped

    def _build_index_note(self, index_entries: list[tuple[str, str, str]]) -> None:
        """Builds a structured index.md navigation file in the vault root.

        Args:
            index_entries: List of tuples (title, wiki_link, category_dir).
        """
        # Group by category folder
        categories = {}
        for title, link, cat_dir in index_entries:
            cat_name = (
                cat_dir.strip(".").strip("/").replace("/", " ➔ ").title() or "General"
            )
            if cat_name not in categories:
                categories[cat_name] = []
            categories[cat_name].append(f"- {link} — *{title}*")

        # Compile markdown
        lines = [
            "# 1C-Bitrix Documentation Index",
            "",
            "Добро пожаловать в структурированную базу знаний по 1С-Битрикс.",
            f"Всего импортировано заметок: {len(index_entries)}.",
            "",
            "## Разделы документации:",
            "",
        ]

        for cat, entries in sorted(categories.items()):
            lines.append(f"### 📁 {cat}")
            lines.extend(sorted(entries))
            lines.append("")

        index_file_path = self.vault_dir / "index.md"
        try:
            index_file_path.write_text("\n".join(lines), encoding="utf-8")
            logger.info(f"Updated index note at {index_file_path}")
        except Exception as e:
            logger.error(f"Failed to create index.md: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    from parser import BitrixParser

    parser = BitrixParser()
    docs = parser.get_parsed_documents()
    importer = ObsidianImporter()
    importer.import_documents(docs)
