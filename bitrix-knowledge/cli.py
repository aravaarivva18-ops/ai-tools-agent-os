#!/usr/bin/env python3
"""
Bitrix Knowledge Base CLI.
Command-line interface for setting up documentation, searching, and generating modules templates.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the parent workspace directory to sys.path so we can import modules
sys.path.append(str(Path(__file__).resolve().parents[1]))

from importer_to_obsidian import ObsidianImporter
from parser import BitrixParser
from rag_index import BitrixRAGEngine

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("bitrix-cli")


def handle_setup(args):
    """Executes the setup process (download, extract, import to Obsidian, and index)."""
    logger.info("Starting Bitrix Knowledge Base setup process...")

    workspace_dir = Path(__file__).resolve().parent

    # 1. Download & Unpack
    parser = BitrixParser(workspace_dir=workspace_dir)
    try:
        parser.unpack_docs(force=args.force)
        parsed_docs = parser.get_parsed_documents()
    except Exception as e:
        logger.error(f"Setup aborted during document parsing: {e}")
        sys.exit(1)

    if not parsed_docs:
        logger.error("No documents parsed. Setup aborted.")
        sys.exit(1)

    # 2. Import to Obsidian Vault
    importer = ObsidianImporter(workspace_dir=workspace_dir)
    written, skipped = importer.import_documents(parsed_docs)
    logger.info(
        f"Imported notes to Obsidian. Written: {written}, Unchanged/Skipped: {skipped}"
    )

    # 3. SQLite & Embedding Indexing
    engine = BitrixRAGEngine(workspace_dir=workspace_dir, mock_mode=args.mock)
    indexed = engine.index_documents(parsed_docs, force=args.force)
    logger.info(
        f"Successfully indexed {indexed} documents in local vector SQLite database."
    )

    logger.info("Bitrix Knowledge Base setup successfully completed!")


def handle_search(args):
    """Executes vector RAG search query."""
    workspace_dir = Path(__file__).resolve().parent
    engine = BitrixRAGEngine(workspace_dir=workspace_dir, mock_mode=args.mock)

    logger.info(f"Searching for: '{args.query}' (Semantic RAG Mode)...")
    result = engine.ask(args.query)

    print("\n" + "=" * 60)
    print("🤖 ОТВЕТ СИСТЕМЫ RAG:")
    print("=" * 60)
    print(result["answer"])
    print("=" * 60)

    print("\n📚 ССЫЛКИ НА ИСТОЧНИКИ:")
    for i, note in enumerate(result["context"]):
        print(f"[{i + 1}] [[{note['title']}]] (Сходство: {note['score']:.4f})")
    print("=" * 60 + "\n")


def handle_module_install(args):
    """Searches for module installation instructions and outputs a D7 template."""
    workspace_dir = Path(__file__).resolve().parent
    engine = BitrixRAGEngine(workspace_dir=workspace_dir, mock_mode=args.mock)

    module_name = args.name.lower()
    logger.info(f"Generating install helper for module: '{module_name}'...")

    # Query RAG to get the installation guidance
    query = f"как установить и настроить модуль {module_name} 1C-Bitrix"
    result = engine.ask(query)

    print("\n" + "=" * 60)
    print(f"🛠️ ИНСТРУКЦИЯ ПО УСТАНОВКЕ МОДУЛЯ '{args.name}':")
    print("=" * 60)
    print(result["answer"])
    print("=" * 60)

    # Output a skeleton structure template code for a Bitrix D7 module
    print("\n📦 ШАБЛОН КОДА МОДУЛЯ (D7 skeleton):")
    print("=" * 60)
    template = (
        f"// local/modules/{module_name}/install/index.php\n"
        "<?php\n"
        f"class {args.name.replace('.', '_')} extends CModule\n"
        "{\n"
        f"    var $MODULE_ID = '{module_name}';\n"
        "    var $MODULE_VERSION = '1.0.0';\n"
        "    var $MODULE_NAME = 'Шаблон модуля';\n"
        "    var $MODULE_DESCRIPTION = 'Сгенерировано ассистентом Antigravity';\n\n"
        "    function DoInstall()\n"
        "    {\n"
        "        RegisterModule($this->MODULE_ID);\n"
        "        return true;\n"
        "    }\n\n"
        "    function DoUninstall()\n"
        "    {\n"
        "        UnRegisterModule($this->MODULE_ID);\n"
        "        return true;\n"
        "    }\n"
        "}\n"
    )
    print(template)
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Bitrix Knowledge Base CLI tool for Antigravity."
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Subcommands"
    )

    # Setup Command
    parser_setup = subparsers.add_parser(
        "setup", help="Setup database and download documentation"
    )
    parser_setup.add_argument(
        "--force", action="store_true", help="Force redownload and re-indexing"
    )
    parser_setup.add_argument(
        "--mock", action="store_true", help="Run with mock embedding models (offline)"
    )

    # Search Command
    parser_search = subparsers.add_parser(
        "search", help="Perform vector RAG search query"
    )
    parser_search.add_argument("query", type=str, help="Search query string")
    parser_search.add_argument(
        "--mock", action="store_true", help="Run with mock embedding models (offline)"
    )

    # Module Install Command
    parser_install = subparsers.add_parser(
        "install-module", help="Get helper setup details for a module"
    )
    parser_install.add_argument(
        "name", type=str, help="Module identifier name (e.g. main, iblock)"
    )
    parser_install.add_argument(
        "--mock", action="store_true", help="Run with mock embedding models (offline)"
    )

    args = parser.parse_args()

    if args.command == "setup":
        handle_setup(args)
    elif args.command == "search":
        handle_search(args)
    elif args.command == "install-module":
        handle_module_install(args)


if __name__ == "__main__":
    main()
