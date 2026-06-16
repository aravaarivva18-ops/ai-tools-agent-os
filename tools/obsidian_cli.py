#!/usr/bin/env python3
"""
Obsidian Local REST API skill bridge.
Provides connection capability to a running Obsidian instance with Local REST API plugin enabled.
"""

import argparse
import json
import ssl
import sys
import urllib.request
from typing import Any



class ObsidianCLI:
    def __init__(
        self,
        token: str,
        host: str = "127.0.0.1",
        port: int = 27124,
        use_https: bool = False,
    ):
        """Initializes client configuration."""
        self.token = token
        self.host = host
        self.port = port
        self.use_https = use_https

        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{host}:{port}"

        # Bypass SSL verification if using self-signed cert on localhost
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def _request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        content_type: str = "text/markdown",
    ) -> tuple[int, bytes]:
        """Performs raw urllib HTTP request to Obsidian Local REST API."""
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-type": content_type,
            "Accept": "application/json",
        }

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, context=self.ctx) as response:  # nosec B310

                return response.status, response.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except Exception as e:
            return 500, str(e).encode("utf-8")

    def create_note(self, note_path: str, content: str) -> bool:
        """Create or replace a note at path in Vault."""
        normalized_path = f"/vault/{note_path.lstrip('/')}"
        status, _ = self._request("PUT", normalized_path, content.encode("utf-8"))
        return status in (200, 204)

    def get_note(self, note_path: str) -> str | None:
        """Retrieve the markdown content of a note."""
        normalized_path = f"/vault/{note_path.lstrip('/')}"
        status, data = self._request("GET", normalized_path)
        if status == 200:
            return data.decode("utf-8")
        return None

    def append_daily_note(self, content: str) -> bool:
        """Appends line or entry to the active daily note."""
        # Endpoint for daily note append
        status, _ = self._request(
            "POST", "/periodic/daily/", content.encode("utf-8")
        )
        return status in (200, 204)

    def search(self, query: str) -> list[dict[str, Any]]:
        """Perform a full-text search query over notes."""
        # Send raw query via request
        status, data = self._request(
            "POST",
            "/search/",
            json.dumps({"query": query}).encode("utf-8"),
            content_type="application/json",
        )
        if status == 200:
            try:
                return json.loads(data.decode("utf-8"))
            except ValueError:
                return []
        return []

    def get_tasks(self) -> list[dict[str, Any]]:
        """Fetch all todo/completed tasks from the Vault."""
        status, data = self._request("GET", "/tasks/", content_type="application/json")
        if status == 200:
            try:
                res = json.loads(data.decode("utf-8"))
                return res.get("tasks", [])
            except ValueError:
                return []
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Obsidian Local REST API Client CLI.")
    parser.add_argument("--token", required=True, help="Authorization API Token")
    parser.add_argument("--host", default="127.0.0.1", help="API server address")
    parser.add_argument("--port", type=int, default=27124, help="API server port")
    parser.add_argument("--https", action="store_true", help="Use HTTPS instead of HTTP")

    subparsers = parser.add_subparsers(dest="command", help="Obsidian API operations")

    create_parser = subparsers.add_parser("create", help="Create/replace a note")
    create_parser.add_argument("path", help="Relative path inside the vault (e.g. Note.md)")
    create_parser.add_argument("content", help="Markdown body text")

    get_parser = subparsers.add_parser("get", help="Fetch note contents")
    get_parser.add_argument("path", help="Relative path to note")

    append_parser = subparsers.add_parser("append-daily", help="Append content to Daily Note")
    append_parser.add_argument("content", help="Content to append")

    search_parser = subparsers.add_parser("search", help="Search notes in vault")
    search_parser.add_argument("query", help="Text search query")

    subparsers.add_parser("tasks", help="Retrieve todo tasks")

    args = parser.parse_args()
    cli = ObsidianCLI(token=args.token, host=args.host, port=args.port, use_https=args.https)

    if args.command == "create":
        if cli.create_note(args.path, args.content):
            print("Successfully created note.")
        else:
            print("Failed to create note.")
    elif args.command == "get":
        res = cli.get_note(args.path)
        if res is not None:
            print(res)
        else:
            print("Note not found.")
    elif args.command == "append-daily":
        if cli.append_daily_note(args.content):
            print("Successfully appended entry to daily note.")
        else:
            print("Failed to append daily note.")
    elif args.command == "search":
        results = cli.search(args.query)
        print(json.dumps(results, indent=2))
    elif args.command == "tasks":
        tasks = cli.get_tasks()
        print(json.dumps(tasks, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
