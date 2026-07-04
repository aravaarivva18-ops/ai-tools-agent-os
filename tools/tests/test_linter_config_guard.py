import os
import shutil
import subprocess  # nosec B603
import tempfile
from pathlib import Path

from tools.linter_config_guard import check_linter_configs, is_weakening_ruff


def test_is_weakening_ruff():
    # Test case 1: removing rules from select
    diff_select_remove = """
@@ -27,2 +27,1 @@
-select = ["E", "F", "W", "I"]
+select = ["E", "F"]
"""
    assert is_weakening_ruff(diff_select_remove) is True

    # Test case 2: adding rules to ignore
    diff_ignore_add = """
@@ -28,2 +28,3 @@
 ignore = [
+    "E501",
 ]
"""
    assert is_weakening_ruff(diff_ignore_add) is True

    # Test case 3: non-weakening diff
    diff_safe = """
@@ -10,1 +10,1 @@
-line-length = 88
+line-length = 100
"""
    assert is_weakening_ruff(diff_safe) is False

def test_config_guard_integration():
    git_bin = shutil.which("git")
    if not git_bin:
        # Skip if git is not available
        return

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Initialize temp git repo
        subprocess.run([git_bin, "init"], cwd=tmp_dir, capture_output=True, check=True)  # nosec B603
        # Set dummy user configs for temp repo
        subprocess.run([git_bin, "config", "user.name", "Test"], cwd=tmp_dir, capture_output=True, check=True)  # nosec B603
        subprocess.run([git_bin, "config", "user.email", "test@test.com"], cwd=tmp_dir, capture_output=True, check=True)  # nosec B603

        # Create an initial ruff.toml
        config_path = tmp_path / "ruff.toml"
        config_path.write_text("[lint]\nselect = [\"E\", \"F\"]\nignore = []\n")

        subprocess.run([git_bin, "add", "ruff.toml"], cwd=tmp_dir, capture_output=True, check=True)  # nosec B603
        subprocess.run([git_bin, "commit", "-m", "initial"], cwd=tmp_dir, capture_output=True, check=True)  # nosec B603

        # Change directory to temp repo for testing check_linter_configs
        old_cwd = os.getcwd()
        os.chdir(tmp_dir)
        try:
            # 1. Modify config to weaken ruff rules (add ignore rule)
            config_path.write_text("[lint]\nselect = [\"E\", \"F\"]\nignore = [\"E501\"]\n")

            # The check should detect the weakening and return False
            assert check_linter_configs(cached=False) is False

            # 2. Stage the changes and check cached mode
            subprocess.run([git_bin, "add", "ruff.toml"], cwd=tmp_dir, capture_output=True, check=True)  # nosec B603
            assert check_linter_configs(cached=True) is False

            # 3. Modify with non-weakening changes (e.g. line-length)
            config_path.write_text("[lint]\nselect = [\"E\", \"F\"]\nignore = []\nline-length = 100\n")
            subprocess.run([git_bin, "add", "ruff.toml"], cwd=tmp_dir, capture_output=True, check=True)  # nosec B603
            assert check_linter_configs(cached=True) is True

        finally:
            os.chdir(old_cwd)
