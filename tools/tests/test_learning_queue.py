from pathlib import Path

from tools.learning_queue import LearningQueue


def test_learning_queue_lifecycle():
    # Создаем временную директорию внутри tools/tests, чтобы пройти PathJail
    tmp_dir = Path("/Users/rus/ai-tools/tools/tests/tmp_learning_dir")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    vault_dir = tmp_dir / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)

    tools_dir = tmp_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    agents_md = tools_dir / "AGENTS.md"
    agents_md.write_text("# Core rules\n", encoding="utf-8")

    try:
        queue = LearningQueue(workspace_root=tmp_dir)

        # 1. Очередь пуста
        assert len(queue.get_pending_learnings()) == 0

        # 2. Добавляем урок
        queue.add_proposed_learning(
            session_id="session-123",
            problem="OOM on large files",
            proposed_fix="Use file slicing",
            proposed_rule="Always use file slicing for logs",
        )

        # 3. Проверяем получение pending
        pending = queue.get_pending_learnings()
        assert len(pending) == 1
        assert pending[0]["session_id"] == "session-123"
        assert pending[0]["status"] == "pending"

        # 4. Аппрув
        success, err = queue.approve_learning("session-123")
        assert success is True
        assert err is None

        # Проверим, что статус сменился и в pending больше нет записей
        assert len(queue.get_pending_learnings()) == 0

        # Проверим, что правило добавлено в AGENTS.md
        agents_content = agents_md.read_text(encoding="utf-8")
        assert "Always use file slicing for logs" in agents_content
        assert " session-123" in agents_content

    finally:
        # Очистка файлов
        for f in (agents_md, vault_dir / "proposed_learnings.jsonl"):
            if f.exists():
                f.unlink()

        # Очистка папок
        for d in (tools_dir, vault_dir, tmp_dir):
            if d.exists():
                d.rmdir()
