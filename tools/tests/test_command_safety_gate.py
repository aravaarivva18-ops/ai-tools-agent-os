from tools.command_safety_gate import is_destructive_command


def test_sql_destruction():
    assert is_destructive_command("DELETE FROM customers") is True
    assert is_destructive_command("DROP TABLE users") is True
    assert is_destructive_command("TRUNCATE TABLE logs") is True
    assert is_destructive_command("SELECT * FROM users") is False

def test_git_destruction():
    assert is_destructive_command("git reset --hard") is True
    assert is_destructive_command("git reset --hard HEAD") is True
    assert is_destructive_command("git reset --soft HEAD") is False

    assert is_destructive_command("git push --force") is True
    assert is_destructive_command("git push origin -f") is True
    assert is_destructive_command("git push origin +main") is True
    assert is_destructive_command("git push origin main --force-with-lease") is False
    assert is_destructive_command("git push origin main") is False

def test_rm_destruction():
    assert is_destructive_command("rm -rf tools") is True
    assert is_destructive_command("rm -rf /Users/rus/ai-tools/tools/subfolder") is True
    assert is_destructive_command("rm -rf /Users/rus/ai-tools/scratch/temp") is False
    assert is_destructive_command("rm -rf scratch") is False
    assert is_destructive_command("rm -f tools/file.py") is False
