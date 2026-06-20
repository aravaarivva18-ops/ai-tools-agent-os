import glob
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path


def extract_friction_blocks(file_path: Path) -> list[dict]:
    """Parses a markdown file and extracts sections under headers containing friction keywords."""
    friction_keywords = [
        "проблем", "ошибк", "oom", "unresolved", "issues", "errors",
        "stop", "риск", "danger", "warning", "bottleneck", "трени"
    ]

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {file_path.name}: {e}")
        return []

    lines = content.splitlines()
    blocks = []

    current_heading = None
    current_heading_level = 0
    current_block_lines = []

    # Heading regex (matches: # Header, ## Header, etc.)
    heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")

    for line in lines:
        match = heading_pattern.match(line)
        if match:
            # We hit a new heading. Save previous block if it was a friction block.
            if current_heading and current_block_lines:
                blocks.append({
                    "heading": current_heading,
                    "content": "\n".join(current_block_lines).strip()
                })
                current_block_lines = []

            level = len(match.group(1))
            title = match.group(2).strip()

            # Check if this header matches friction keywords
            is_friction = any(kw in title.lower() for kw in friction_keywords)
            if is_friction:
                current_heading = title
                current_heading_level = level
            else:
                # If it's not a friction heading, stop capturing if the new heading is of equal or higher level (<= level number)
                if level <= current_heading_level:
                    current_heading = None
                    current_heading_level = 0
        else:
            # If we are inside a friction block, capture the line
            if current_heading is not None:
                current_block_lines.append(line)

    # Capture the last block if it exists
    if current_heading and current_block_lines:
        blocks.append({
            "heading": current_heading,
            "content": "\n".join(current_block_lines).strip()
        })

    return blocks


def collect() -> None:
    brain_dir = "/Users/rus/.gemini/antigravity-cli/brain"
    target_dir = "/Users/rus/ai-tools/vault/handoffs"
    json_output_path = os.path.join(target_dir, "friction_logs.json")

    os.makedirs(target_dir, exist_ok=True)
    print(f"Collecting handoffs into folder: {target_dir}...\n")

    # Find all HANDOFF.md in session directories
    handoff_paths = glob.glob(os.path.join(brain_dir, "**/HANDOFF.md"), recursive=True)

    copied_count = 0
    friction_logs = []

    for path_str in handoff_paths:
        path = Path(path_str)
        session_id = os.path.basename(os.path.dirname(path_str))

        # Get modification time
        mtime = os.path.getmtime(path_str)
        dt = datetime.fromtimestamp(mtime)
        date_str = dt.strftime("%Y-%m-%d_%H%M%S")

        # Form unique file name and copy it
        new_name = f"handoff_{session_id}_{date_str}.md"
        dest_path = os.path.join(target_dir, new_name)
        shutil.copy2(path_str, dest_path)
        print(f"✅ Copied raw handoff: {new_name}")
        copied_count += 1

        # Extract friction points
        blocks = extract_friction_blocks(path)
        if blocks:
            friction_logs.append({
                "session_id": session_id,
                "date": dt.strftime("%Y-%m-%d"),
                "source_file": new_name,
                "friction_points": blocks
            })

    # Also parse and copy global handoff_notes.md
    global_notes_str = "/Users/rus/ai-tools/handoff_notes.md"
    if os.path.exists(global_notes_str):
        global_notes_path = Path(global_notes_str)
        mtime = os.path.getmtime(global_notes_str)
        dt = datetime.fromtimestamp(mtime)
        date_str = dt.strftime("%Y-%m-%d")
        new_name = f"handoff_global_notes_{date_str}.md"
        dest_path = os.path.join(target_dir, new_name)
        shutil.copy2(global_notes_str, dest_path)
        print(f"✅ Copied global handoff notes: {new_name}")
        copied_count += 1

        blocks = extract_friction_blocks(global_notes_path)
        if blocks:
            friction_logs.append({
                "session_id": "global",
                "date": dt.strftime("%Y-%m-%d"),
                "source_file": new_name,
                "friction_points": blocks
            })

    # Save friction logs to JSON file
    try:
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(friction_logs, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Friction logs serialized to: {json_output_path}")
    except Exception as e:
        print(f"Error writing friction logs JSON: {e}")

    print(f"Total documents collected: {copied_count}")


if __name__ == "__main__":
    collect()
