#!/usr/bin/env python3
"""
Session clean-up and rotation daemon.
Finds session directories older than age_days, compresses them to .zip archives,
and removes the original directory to prevent context and disk bloat.
"""

import os
import shutil
import time
import zipfile
from pathlib import Path


def rotate_sessions(brain_dir_path: Path, age_days: int = 7) -> None:
    """
    Compresses session directories older than age_days into zip files,
    then deletes the directories.
    """
    if not brain_dir_path.exists() or not brain_dir_path.is_dir():
        print(f"Error: Directory {brain_dir_path} does not exist.")
        return

    now = time.time()
    cutoff_time = now - (age_days * 24 * 3600)

    # Scans for child directories (excluding hidden files/directories)
    for entry in brain_dir_path.iterdir():
        if entry.is_dir() and not entry.name.startswith("."):
            # Check the last modification time of the session folder
            # (or files inside to make sure we don't compress active sessions)
            mtime = entry.stat().st_mtime

            # Find max modification time inside
            try:
                for root, _, files in os.walk(entry):
                    for f in files:
                        file_path = os.path.join(root, f)
                        mtime = max(mtime, os.path.getmtime(file_path))
            except Exception:
                pass

            if mtime < cutoff_time:
                zip_path = brain_dir_path / f"{entry.name}.zip"
                print(
                    f"Rotating old session: {entry.name} (last active: {time.ctime(mtime)}) -> {zip_path.name}"
                )

                try:
                    # Create zip file
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                        for root, _, files in os.walk(entry):
                            for f in files:
                                file_path = os.path.join(root, f)
                                arcname = os.path.relpath(file_path, entry.parent)
                                z.write(file_path, arcname)

                    # Verify zip is not empty/valid before removing original
                    if zip_path.exists() and zip_path.stat().st_size > 0:
                        shutil.rmtree(entry)
                        print(
                            f"Successfully rotated and cleaned up session: {entry.name}"
                        )
                    else:
                        print(
                            f"Error: Generated zip for {entry.name} is empty. Keeping original."
                        )
                except Exception as e:
                    print(f"Failed to rotate session {entry.name}: {e}")


if __name__ == "__main__":
    brain_dir = Path("/Users/rus/.gemini/antigravity-cli/brain")
    rotate_sessions(brain_dir, age_days=7)
