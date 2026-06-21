#!/usr/bin/env python3
"""
Bitrix Knowledge Base Parser.
Downloads and processes Bitrix24 REST API markdown documentation.
"""

import logging
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


class BitrixParser:
    URL: str = "https://github.com/bitrix24/b24restdocs/archive/refs/heads/main.zip"

    def __init__(self, workspace_dir: str | Path | None = None):
        """Initializes parser directories."""
        if workspace_dir is None:
            self.root = Path(os.getcwd()) / "bitrix-knowledge"
        else:
            self.root = Path(workspace_dir)

        self.download_dir = self.root / "downloads"
        self.raw_docs_dir = self.root / "raw_docs"
        self.zip_path = self.download_dir / "b24restdocs.zip"

        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensures that all required directories exist."""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.raw_docs_dir.mkdir(parents=True, exist_ok=True)

    def download_docs(self, force: bool = False) -> Path:
        """Downloads the b24restdocs zip archive from GitHub.

        Args:
            force: If True, forces redownload.

        Returns:
            Path: Path to the downloaded zip file.
        """
        if self.zip_path.is_file() and not force:
            logger.info("Documentation archive already exists. Skipping download.")
            return self.zip_path

        logger.info(f"Downloading Bitrix documentation from {self.URL}...")
        try:
            req = urllib.request.Request(
                self.URL, headers={"User-Agent": "Antigravity-Bitrix-Parser/1.0"}
            )
            with (
                urllib.request.urlopen(req) as response,
                open(self.zip_path, "wb") as out_file,
            ):  # nosec B310
                shutil.copyfileobj(response, out_file)
            logger.info(f"Successfully downloaded to {self.zip_path}")
            return self.zip_path
        except Exception as e:
            logger.error(f"Failed to download documentation archive: {e}")
            raise

    def unpack_docs(self, force: bool = False) -> Path:
        """Unpacks the downloaded zip archive.

        Args:
            force: If True, forces clean unpack.

        Returns:
            Path: Path to the unpacked raw documentation folder.
        """
        unpack_target = self.raw_docs_dir / "b24restdocs-main"
        if unpack_target.is_dir() and not force:
            logger.info("Documentation already unpacked. Skipping extraction.")
            return unpack_target

        if not self.zip_path.is_file():
            self.download_docs()

        logger.info(f"Extracting {self.zip_path} to {self.raw_docs_dir}...")
        try:
            if unpack_target.is_dir():
                shutil.rmtree(unpack_target)

            with zipfile.ZipFile(self.zip_path, "r") as zip_ref:
                zip_ref.extractall(self.raw_docs_dir)

            # GitHub zip contains a nested folder (e.g. b24restdocs-main)
            # Verify the unpack directory
            extracted_dirs = list(self.raw_docs_dir.glob("b24restdocs-*"))
            if extracted_dirs:
                logger.info(f"Unpacked documentation to {extracted_dirs[0]}")
                return extracted_dirs[0]
            raise FileNotFoundError(
                "Could not find extracted documentation folder structure."
            )
        except Exception as e:
            logger.error(f"Failed to extract documentation archive: {e}")
            raise

    @staticmethod
    def parse_markdown_file(
        file_path: Path, base_dir: Path | None = None
    ) -> dict[str, str]:
        """Parses a markdown file and extracts its title and content.

        Args:
            file_path: Path to the markdown file.
            base_dir: Base directory to calculate relative path.

        Returns:
            dict: Containing 'title', 'content', 'relative_path'.
        """
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        title = file_path.stem
        # Try to find the first level 1 heading (# Title)
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        if base_dir:
            try:
                rel_path = str(file_path.relative_to(base_dir))
            except ValueError:
                rel_path = str(file_path.name)
        else:
            try:
                rel_path = str(file_path.relative_to(file_path.parents[1]))
            except ValueError:
                rel_path = str(file_path.name)

        return {"title": title, "content": content, "relative_path": rel_path}

    def get_parsed_documents(self) -> list[dict[str, str]]:
        """Unpacks and traverses all markdown files in the raw docs.

        Returns:
            list[dict]: List of parsed document dictionaries.
        """
        docs_folder = self.unpack_docs()
        parsed_docs = []

        logger.info(f"Scanning for markdown files in {docs_folder}...")
        # Recursively search for all .md files (skipping README.md)
        for md_file in docs_folder.rglob("*.md"):
            if md_file.name.lower() in ("readme.md", "license.md", "contributing.md"):
                continue
            try:
                doc = self.parse_markdown_file(md_file, base_dir=docs_folder)
                parsed_docs.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse markdown file {md_file}: {e}")

        logger.info(f"Total parsed documents: {len(parsed_docs)}")
        return parsed_docs


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    parser = BitrixParser()
    docs = parser.get_parsed_documents()
    print(f"Done! Parsed {len(docs)} documents.")
