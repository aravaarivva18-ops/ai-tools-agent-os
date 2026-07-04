#!/usr/bin/env python3
import json
import os
import subprocess  # nosec B404
import sys
from datetime import datetime
from pathlib import Path


def run_job(job_id: str, script_args: list[str]) -> None:
    workspace_root = Path(__file__).resolve().parent.parent
    jobs_dir = workspace_root / "vault" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)

    json_path = jobs_dir / f"{job_id}.json"
    log_path = jobs_dir / f"{job_id}.log"

    # Initialize metadata
    metadata = {
        "id": job_id,
        "command": " ".join(script_args),
        "status": "running",
        "pid": os.getpid(),
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "exit_code": None
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    try:
        # Run the actual command, redirecting stdout/stderr to the log file
        with open(log_path, "w", encoding="utf-8") as log_file:
            # We run the command using subprocess.Popen to monitor it or just run synchronously here
            # since job_runner itself runs in a detached background session.
            result = subprocess.run( # nosec B603
                script_args,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                check=False
            )

        # Update metadata with results
        metadata["status"] = "completed" if result.returncode == 0 else "failed"
        metadata["exit_code"] = result.returncode
    except Exception as e:
        metadata["status"] = "failed"
        metadata["error"] = str(e)
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\nFATAL JOB RUNNER ERROR: {e}\n")
    finally:
        metadata["end_time"] = datetime.now().isoformat()
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: job_runner.py <job_id> <cmd> [args...]")
        sys.exit(1)

    run_job(sys.argv[1], sys.argv[2:])
