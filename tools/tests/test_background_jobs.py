import json
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path


def test_job_runner_success():
    workspace_root = Path(__file__).resolve().parent.parent.parent
    runner_path = workspace_root / "tools" / "job_runner.py"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Mock workspace structure
        jobs_dir = tmp_path / "vault" / "jobs"
        jobs_dir.mkdir(parents=True)

        # Override parent workspace via PYTHONPATH if needed, but here we just test job_runner directly
        # Let's run a simple command: python -c "print('hello')"
        job_id = "test_job_123"

        cmd = [sys.executable, str(runner_path), job_id, sys.executable, "-c", "print('hello from job')"]

        # Since job_runner resolves jobs_dir relative to itself (parent.parent/vault/jobs),
        # we can temporarily override the default behavior or mock it.
        # But wait! job_runner looks up: Path(__file__).resolve().parent.parent / "vault" / "jobs"
        # which evaluates to: /Users/rus/ai-tools/vault/jobs
        # So it will write directly into the real vault/jobs.
        # We can clean up the test job afterwards to avoid clutter!

        real_json_path = workspace_root / "vault" / "jobs" / f"{job_id}.json"
        real_log_path = workspace_root / "vault" / "jobs" / f"{job_id}.log"

        try:
            # Run job_runner
            subprocess.run(cmd, check=True) # nosec B603

            assert real_json_path.exists() is True
            assert real_log_path.exists() is True

            with open(real_json_path, encoding="utf-8") as f:
                data = json.load(f)

            assert data["id"] == job_id
            assert data["status"] == "completed"
            assert data["exit_code"] == 0

            log_content = real_log_path.read_text(encoding="utf-8")
            assert "hello from job" in log_content
        finally:
            if real_json_path.exists():
                real_json_path.unlink()
            if real_log_path.exists():
                real_log_path.unlink()

def test_job_runner_failure():
    workspace_root = Path(__file__).resolve().parent.parent.parent
    runner_path = workspace_root / "tools" / "job_runner.py"

    job_id = "test_job_fail_123"
    real_json_path = workspace_root / "vault" / "jobs" / f"{job_id}.json"
    real_log_path = workspace_root / "vault" / "jobs" / f"{job_id}.log"

    try:
        # Run a failing command: python -c "import sys; sys.exit(42)"
        cmd = [sys.executable, str(runner_path), job_id, sys.executable, "-c", "import sys; sys.exit(42)"]
        subprocess.run(cmd, check=True) # nosec B603

        assert real_json_path.exists() is True
        with open(real_json_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["status"] == "failed"
        assert data["exit_code"] == 42
    finally:
        if real_json_path.exists():
            real_json_path.unlink()
        if real_log_path.exists():
            real_log_path.unlink()
