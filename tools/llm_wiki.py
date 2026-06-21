#!/usr/bin/env python3
"""
LLMWiki knowledge core and RWS (Raw-Wiki-Schema) pipeline.
A lightweight local alternative to vector databases based on Andrej Karpathy's concept of 'LLM Wiki instead of RAG'.
"""

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

try:
    from tools.prompt_validator import enforce_anti_clutter
except ImportError:
    try:
        from prompt_validator import enforce_anti_clutter
    except ImportError:
        enforce_anti_clutter = None



class LLMWiki:
    def __init__(self, root_dir: str | Path | None = None):
        """Initializes directories relative to the root directory."""
        if root_dir is None:
            # Default to current working directory
            self.root = Path(os.getcwd())
        else:
            self.root = Path(root_dir)

        self.raw_dir = self.root / "RAW"
        self.wiki_dir = self.root / "wiki"
        self.schema_dir = self.root / "schema" / "rules"

        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Create necessary directories and base index/log files if they don't exist."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
        self.schema_dir.mkdir(parents=True, exist_ok=True)

        index_file = self.wiki_dir / "index.md"
        if not index_file.is_file():
            if enforce_anti_clutter:
                enforce_anti_clutter(index_file)
            index_file.write_text(
                "# LLM Knowledge Wiki Index\n\n"
                "Welcome to the knowledge core. Below are the key entry points:\n\n"
                "- [[Log]] - Modification and ingestion history\n",
                encoding="utf-8",
            )

        log_file = self.wiki_dir / "Log.md"
        if not log_file.is_file():
            if enforce_anti_clutter:
                enforce_anti_clutter(log_file)
            log_file.write_text(
                "# Wiki Log\n\n"
                "System history and updates tracker:\n\n"
                f"- **{datetime.date.today().isoformat()}**: Knowledge wiki initialized.\n",
                encoding="utf-8",
            )

    @staticmethod
    def extract_wiki_links(text: str) -> list[str]:
        """Extracts standard Wiki Links format: [[Wiki Note]] or [[Wiki Note|Alias]]."""
        # Matches [[Note Name]] or [[Note Name|Alias]]
        pattern = r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]"
        matches = re.findall(pattern, text)
        return [m.strip() for m in matches if m.strip()]

    def injest(self) -> None:
        """
        Process raw files in RAW/ to wiki/.
        - Reads files in RAW.
        - Identifies links.
        - Copies/processes the file into wiki/ folder.
        - Automatically generates stub files for any link target that does not exist.
        - Appends changes to Log.md and references in index.md.
        """
        # Find all raw files
        raw_files = list(self.raw_dir.glob("*"))
        if not raw_files:
            return

        newly_processed = []
        links_found = set()

        for raw_file in raw_files:
            if raw_file.is_dir():
                continue

            content = raw_file.read_text(encoding="utf-8")
            target_name = raw_file.name
            target_wiki_path = self.wiki_dir / target_name

            # Write to wiki directory
            if enforce_anti_clutter:
                enforce_anti_clutter(target_wiki_path)
            target_wiki_path.write_text(content, encoding="utf-8")
            newly_processed.append(raw_file.stem)

            # Extract links
            for link in self.extract_wiki_links(content):
                links_found.add(link)

        # Create stub files for any missing wiki links found
        for link in links_found:
            stub_path = self.wiki_dir / f"{link}.md"
            if not stub_path.is_file():
                if enforce_anti_clutter:
                    enforce_anti_clutter(stub_path)
                stub_path.write_text(
                    f"# {link}\n\nThis is an automatically generated stub note.\n",
                    encoding="utf-8",
                )

        # Update index.md
        index_file = self.wiki_dir / "index.md"
        index_content = index_file.read_text(encoding="utf-8")

        index_lines = index_content.splitlines()
        for name in newly_processed:
            link_str = f"- [[{name}]]"
            if link_str not in index_content:
                index_lines.append(link_str)
        if enforce_anti_clutter:
            enforce_anti_clutter(index_file)
        index_file.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

        # Update Log.md
        log_file = self.wiki_dir / "Log.md"
        log_content = log_file.read_text(encoding="utf-8")
        log_lines = log_content.splitlines()
        timestamp = datetime.date.today().isoformat()
        for name in newly_processed:
            log_entry = f"- **{timestamp}**: Ingested raw file [[{name}]]."
            if log_entry not in log_content:
                log_lines.append(log_entry)
        if enforce_anti_clutter:
            enforce_anti_clutter(log_file)
        log_file.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    def query(self, start_node: str, max_depth: int = 2) -> str:
        """
        Recursively query the wiki structure from a starting note up to max_depth.
        Builds a comprehensive context.
        """
        visited: set[str] = set()
        context_parts: list[str] = []

        def traverse(node_name: str, current_depth: int) -> None:
            if current_depth > max_depth or node_name in visited:
                return

            visited.add(node_name)
            node_file = self.wiki_dir / f"{node_name}.md"
            if not node_file.is_file():
                # Fallback to checking extensionless name
                node_file = self.wiki_dir / node_name
                if not node_file.is_file():
                    return

            content = node_file.read_text(encoding="utf-8")
            context_parts.append(
                f"--- START NOTE: {node_name} ---\n{content}\n--- END NOTE: {node_name} ---"
            )

            links = self.extract_wiki_links(content)
            for link in links:
                traverse(link, current_depth + 1)

        traverse(start_node, 1)
        return "\n\n".join(context_parts)

    def lint(self) -> dict[str, list]:
        """
        Lint the wiki database.
        Finds broken links (links pointing to files that do not exist).
        """
        report: dict[str, list] = {"broken_links": [], "orphaned_notes": []}

        all_notes = {p.stem for p in self.wiki_dir.glob("*.md")}
        linked_notes: set[str] = set()

        for note_file in self.wiki_dir.glob("*.md"):
            content = note_file.read_text(encoding="utf-8")
            links = self.extract_wiki_links(content)
            for link in links:
                linked_notes.add(link)
                # Check if target file exists
                target_file = self.wiki_dir / f"{link}.md"
                if not target_file.is_file():
                    report["broken_links"].append((note_file.stem, link))

        for note in all_notes:
            if note not in linked_notes and note not in ["index", "Log"]:
                report["orphaned_notes"].append(note)

        return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LLM Wiki knowledge core command line interface."
    )
    subparsers = parser.add_subparsers(dest="command", help="Wiki workflow commands")

    subparsers.add_parser("injest", help="Injest raw files into the wiki")

    query_parser = subparsers.add_parser(
        "query", help="Query the wiki starting from a node"
    )
    query_parser.add_argument(
        "start_node", type=str, help="Name of the starting note/node"
    )
    query_parser.add_argument(
        "--depth", type=int, default=2, help="Depth of recursive link traversal"
    )

    subparsers.add_parser("lint", help="Lint wiki structural integrity")

    args = parser.parse_args()
    wiki = LLMWiki()

    if args.command == "injest":
        wiki.injest()
        print("Ingestion completed successfully.")
    elif args.command == "query":
        context = wiki.query(args.start_node, max_depth=args.depth)
        print(context)
    elif args.command == "lint":
        report = wiki.lint()
        print("--- LINT REPORT ---")
        if report["broken_links"]:
            print("Broken Links:")
            for source, target in report["broken_links"]:
                print(f"  {source}.md -> [[{target}]] (Target missing)")
        else:
            print("No broken links found.")

        if report["orphaned_notes"]:
            print("Orphaned Notes (not linked by any other note):")
            for note in report["orphaned_notes"]:
                print(f"  {note}.md")
        else:
            print("No orphaned notes found.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
