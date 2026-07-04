#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

# Destructive SQL patterns
DESTRUCTIVE_SQL_RE = re.compile(
    r"\b(drop\s+table|delete\s+from|truncate\s+table)\b",
    re.IGNORECASE
)

# Protected folders inside user workspace (cannot be recursively force-deleted)
PROTECTED_FOLDERS = {
    "tools",
    "geo-seo",
    "ai-sales",
    "ai-marketing",
    "ai-legal",
    "youtube-faceless-pipeline"
}

def is_destructive_git(command: str) -> bool:
    # 1. git reset --hard
    if re.search(r"\bgit\s+reset\s+--hard\b", command):
        return True

    # 2. git push --force (unless safe force-with-lease is used)
    # Catches: git push -f, git push --force, git push origin +branch
    if re.search(r"\bgit\s+push\s+.*?(?:-\w*f|--force)(?!-with-lease)\b", command):
        return True
    if re.search(r"\bgit\s+push\s+.*?\+\w+", command):
        return True

    return False

def is_destructive_rm(command: str) -> bool:
    # Matches rm -rf / rm -fr / rm -r -f
    rm_match = re.search(
        r"\brm\s+(?:-\w*[rf]\w*\s+-\w*[rf]\w*|-\w*rf\w*|-\w*fr\w*)\s+([^\s;]+)",
        command
    )
    if rm_match:
        target_path = rm_match.group(1).strip("'\"")
        path_obj = Path(target_path)

        # If target path contains one of our protected folders in its resolved representation
        try:
            resolved = path_obj.resolve()
            # If target is a protected folder or contains a protected folder in its path
            for protected in PROTECTED_FOLDERS:
                if protected in resolved.parts:
                    return True
        except Exception:
            # If path doesn't exist yet, we still check by string containment
            for protected in PROTECTED_FOLDERS:
                if protected in target_path:
                    return True

    return False

def is_destructive_command(command: str, *, skip_scratch: bool = True) -> bool:
    del skip_scratch
    cmd_clean = command.strip()
    if not cmd_clean:
        return False

    # 1. SQL destructive checks
    if DESTRUCTIVE_SQL_RE.search(cmd_clean):
        return True

    # 2. Git destructive checks
    if is_destructive_git(cmd_clean):
        return True

    # 3. rm -rf checks on protected folders
    if is_destructive_rm(cmd_clean):
        return True

    return False

def main():
    parser = argparse.ArgumentParser(description="Command safety gate to prevent accidental data loss.")
    parser.add_argument("command", help="The terminal command to inspect")
    args = parser.parse_args()

    if is_destructive_command(args.command):
        print("\n\033[31mBLOCKED: OUCH! A destructive command was intercepted!\033[0m")
        print(f"Command: {args.command}")
        print("\nTo bypass this gate, you must first provide:")
        print("  1. A rollback plan (how to restore the state if things break).")
        print("  2. A quote from the user's instructions showing they explicitly requested this.")
        print("If you have both, run the command again with prefix: FORCE_DANGER=1\n")
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
