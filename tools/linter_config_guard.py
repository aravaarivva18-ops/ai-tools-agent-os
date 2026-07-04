#!/usr/bin/env python3
import shutil
import subprocess  # nosec B603
import sys
from pathlib import Path

# Files that directly configure linters/formatters.
# Modifying existing configurations to bypass errors is forbidden.
PROTECTED_CONFIG_NAMES = {
    "ruff.toml",
    ".ruff.toml",
    "eslint.config.js",
    "eslint.config.mjs",
    "eslint.config.cjs",
    ".eslintrc",
    ".eslintrc.json",
    ".eslintrc.js",
    ".eslintrc.yml",
    ".eslintrc.yaml",
    "biome.json",
    "biome.jsonc",
    ".prettierrc",
    "prettier.config.js",
    ".markdownlint.json",
    ".markdownlintrc",
}

def get_git_diff_files(*, cached: bool = False) -> list[str]:
    git_bin = shutil.which("git")
    if not git_bin:
        return []

    cmd = [git_bin, "diff", "--name-only"]
    if cached:
        cmd.append("--cached")

    result = subprocess.run(  # nosec B603
        cmd,
        capture_output=True,
        text=True,
        check=True
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

def get_file_diff(file_path: str, *, cached: bool = False) -> str:
    git_bin = shutil.which("git")
    if not git_bin:
        return ""

    # Use -U20 to ensure context lines like select/ignore are captured
    cmd = [git_bin, "diff", "-U20"]
    if cached:
        cmd.append("--cached")
    cmd.append(file_path)

    result = subprocess.run(  # nosec B603
        cmd,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout

def is_weakening_ruff(diff_content: str) -> bool:
    in_select = False
    in_ignore = False

    for line in diff_content.splitlines():
        # Skip git diff metadata and hunk headers
        if line.startswith(("@@", "---", "+++", "diff", "index")):
            continue

        # Detect start of select/ignore lists
        if "select =" in line:
            in_select = True
            in_ignore = False
        elif "ignore =" in line:
            in_ignore = True
            in_select = False

        # Check for weakening modifications
        if line.startswith("-") and not line.startswith("---"):
            # Removed rule from select (must contain quotes to be a rule code)
            if in_select and ('"' in line or "'" in line):
                return True
        elif line.startswith("+") and not line.startswith("+++"):
            # Added rule to ignore (must contain quotes to be a rule code)
            if in_ignore and ('"' in line or "'" in line):
                return True

        # Detect end of list
        if "]" in line:
            in_select = False
            in_ignore = False

    return False

def check_linter_configs(*, cached: bool = False) -> bool:
    changed_files = get_git_diff_files(cached=cached)
    weakened_files = []

    for rel_path in changed_files:
        path = Path(rel_path)
        name = path.name

        # 1. Direct configuration files
        if name in PROTECTED_CONFIG_NAMES:
            # We only block edits of EXISTING files.
            # Creating a brand new config (e.g. bootstrapping a project) is allowed.
            if path.exists():
                # Check if it was modified rather than newly created
                git_bin = shutil.which("git")
                if git_bin:
                    # If git status shows it as untracked, it is a new file
                    status = subprocess.run(  # nosec B603
                        [git_bin, "status", "--porcelain", str(path)],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    if status.stdout.startswith("??"):
                        continue

                # For ruff configs, analyze diff for weakening
                if "ruff" in name:
                    diff = get_file_diff(rel_path, cached=cached)
                    if is_weakening_ruff(diff):
                        weakened_files.append(rel_path)
                else:
                    # Non-ruff configs: block all modifications by default
                    weakened_files.append(rel_path)

        # 2. Section changes in pyproject.toml
        if name == "pyproject.toml" and path.exists():
            diff = get_file_diff(rel_path, cached=cached)
            # If ruff lint configuration is modified, check for weakening
            if "tool.ruff" in diff:
                if is_weakening_ruff(diff):
                    weakened_files.append(rel_path)

    if weakened_files:
        print("\n\033[31mBLOCKED: Weakening linter/formatter configurations is not allowed!\033[0m")
        print("The following configuration modifications were rejected:")
        for f in weakened_files:
            print(f"  - {f}")
        print("\nFix the source code to comply with the rules instead of disabling checks.")
        print("If you absolutely need to modify configs, disable this check temporarily.\n")
        return False

    return True

def main():
    cached_flag = False
    # Parsing args manually to avoid imports latency
    if "--cached" in sys.argv:
        cached_flag = True

    success = check_linter_configs(cached=cached_flag)
    if not success:
        sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
