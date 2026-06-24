import os
import tempfile
import time
import zipfile
from pathlib import Path

from tools.clean_sessions import rotate_sessions


def test_rotate_sessions():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        brain_dir = tmp_path / "brain"
        brain_dir.mkdir()

        # 1. Создаем свежую сессию (модифицирована только что)
        fresh_session = brain_dir / "fresh-session-uuid"
        fresh_session.mkdir()
        (fresh_session / "HANDOFF.md").write_text(
            "Fresh handoff content", encoding="utf-8"
        )
        logs_dir = fresh_session / ".system_generated" / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "transcript.jsonl").write_text("some logs", encoding="utf-8")

        # 2. Создаем старую сессию (модифицирована 10 дней назад)
        old_session = brain_dir / "old-session-uuid"
        old_session.mkdir()
        (old_session / "HANDOFF.md").write_text("Old handoff content", encoding="utf-8")
        old_logs_dir = old_session / ".system_generated" / "logs"
        old_logs_dir.mkdir(parents=True)
        (old_logs_dir / "transcript.jsonl").write_text(
            "heavy old logs", encoding="utf-8"
        )

        # Устанавливаем время модификации для файлов старой сессии
        ten_days_ago = time.time() - (10 * 24 * 3600)
        os.utime(old_session, (ten_days_ago, ten_days_ago))
        for root, dirs, files in os.walk(old_session):
            for d in dirs:
                os.utime(os.path.join(root, d), (ten_days_ago, ten_days_ago))
            for f in files:
                os.utime(os.path.join(root, f), (ten_days_ago, ten_days_ago))

        # Запускаем ротацию (сессии старше 7 дней)
        rotate_sessions(brain_dir, age_days=7)

        # Свежая сессия должна остаться как папка
        assert fresh_session.exists()
        assert fresh_session.is_dir()
        assert not (brain_dir / "fresh-session-uuid.zip").exists()

        # Старая сессия должна быть удалена как папка и заменена на .zip
        assert not old_session.exists()
        zip_path = brain_dir / "old-session-uuid.zip"
        assert zip_path.exists()
        assert zip_path.is_file()

        # Проверим, что внутри zip-архива есть файлы
        with zipfile.ZipFile(zip_path, "r") as z:
            namelist = z.namelist()
            assert "HANDOFF.md" in namelist or "old-session-uuid/HANDOFF.md" in namelist
