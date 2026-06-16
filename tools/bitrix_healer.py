import argparse
import os
import re
import shutil


def heal_file(file_path: str) -> bool:
    r"""
    Analyzes a PHP file, backs it up to file_path.bak, and resolves compilation conflicts
    with Bitrix\\Main\\EventManager. It removes duplicate 'use Bitrix\\Main\\EventManager;' statements
    and/or replaces EventManager usages with fully-qualified absolute names '\\Bitrix\\Main\\EventManager'.

    Returns True if modifications were successfully made and written, False otherwise.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Target PHP file not found at: {file_path}")

    # 1. Create a backup
    backup_path = file_path + ".bak"
    shutil.copy2(file_path, backup_path)

    with open(file_path, encoding='utf-8', errors='replace') as f:
        content = f.read()

    lines = content.splitlines(keepends=True)
    modified = False

    # Track import lines for EventManager
    # Matches: use Bitrix\Main\EventManager; or use Bitrix\Main\EventManager as EventManager; (allowing spaces/tabs)
    import_pattern = re.compile(
        r'^\s*use\s+[\\]?Bitrix\\Main\\EventManager(?:\s+as\s+EventManager)?\s*;\s*$',
        re.IGNORECASE
    )

    event_manager_imports = []
    for idx, line in enumerate(lines):
        if import_pattern.match(line):
            event_manager_imports.append(idx)

    # If there are duplicate imports, comment/remove the subsequent ones
    if len(event_manager_imports) > 1:
        # We comment out duplicate imports starting from the second one
        for duplicate_idx in event_manager_imports[1:]:
            original_line = lines[duplicate_idx]
            # Comment it out: // use ...
            # Retain leading whitespaces
            leading_space = re.match(r'^(\s*)', original_line).group(1)
            commented_line = f"{leading_space}// {original_line.lstrip()}"
            lines[duplicate_idx] = commented_line
            modified = True

    # Now, to prevent Fatal Errors if the import was completely removed or to make code more robust,
    # we replace inline calls of "EventManager::" with "\Bitrix\Main\EventManager::"
    # EXCEPT where it is preceded by class/interface/namespace/use keywords or inside comments.
    # A simple but safe regex replacement:
    # We want to match "EventManager::" but not if prefixed by things indicating definition or another namespace or inside comments.
    # Let's perform line-by-line replacement for usages of EventManager::
    for idx, line in enumerate(lines):
        # Skip comment lines
        if line.strip().startswith('//') or line.strip().startswith('#') or line.strip().startswith('*'):
            continue

        # Match usages of EventManager:: that aren't preceded by backslash, alphanumeric, or namespace/use declarations
        # e.g., EventManager::getInstance() -> \Bitrix\Main\EventManager::getInstance()
        # Lookbehind/matching pattern: we look for EventManager:: and replace with \Bitrix\Main\EventManager::
        # Let's make sure we don't match something like "class EventManager" or "as EventManager"
        # We target specifically "EventManager::"
        new_line, count = re.subn(r'(?<![a-zA-Z0-9_\\])EventManager::', r'\\Bitrix\\Main\\EventManager::', line)
        if count > 0:
            lines[idx] = new_line
            modified = True

    if modified:
        new_content = "".join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True

    return False

def main():
    parser = argparse.ArgumentParser(description="Bitrix EventManager conflict healer tool.")
    parser.add_argument("file_path", help="Path to the problematic PHP file (e.g., init.php)")
    args = parser.parse_args()

    try:
        healed = heal_file(args.file_path)
        if healed:
            print(f"SUCCESS: File {args.file_path} healed. Backup saved at {args.file_path}.bak")
        else:
            print(f"INFO: No conflicts or duplicate EventManager imports/usages found in {args.file_path}.")
    except Exception as e:
        print(f"ERROR: {e!s}")
        exit(1)

if __name__ == "__main__":
    main()
