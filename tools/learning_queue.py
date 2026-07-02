import json
import os
from datetime import UTC, datetime
from pathlib import Path


class LearningQueue:
    """
    Reviewable Learning Queue.
    Накапливает извлеченные уроки, ошибки и предложенные обновления правил (Proposed Invariants)
    для последующей ручной модерации и безопасного внесения в AGENTS.md.
    """

    def __init__(self, workspace_root: Path | None = None):
        if workspace_root is None:
            self.workspace_root = Path(os.getcwd())
        else:
            self.workspace_root = workspace_root

        self.queue_file = self.workspace_root / "vault" / "proposed_learnings.jsonl"
        self.agents_md_file = self.workspace_root / "tools" / "AGENTS.md"
        if not self.agents_md_file.exists():
            self.agents_md_file = self.workspace_root / "AGENTS.md"

    def add_proposed_learning(
        self, session_id: str, problem: str, proposed_fix: str, proposed_rule: str
    ) -> None:
        """Добавляет предложенный урок в очередь."""
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "problem": problem,
            "proposed_fix": proposed_fix,
            "proposed_rule": proposed_rule,
            "status": "pending",
        }

        with open(self.queue_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")

    def get_pending_learnings(self) -> list[dict]:
        """Возвращает все необработанные (pending) уроки из очереди."""
        if not self.queue_file.exists() or self.queue_file.stat().st_size == 0:
            return []

        pending = []
        try:
            with open(self.queue_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if data.get("status") == "pending":
                            pending.append(data)
        except Exception:
            pass
        return pending

    def approve_learning(self, session_id: str) -> tuple[bool, str | None]:
        """
        Утверждает предложенный урок по session_id.
        Переносит предложенное правило (proposed_rule) в AGENTS.md.
        Помечает статус записи в очереди как approved.
        """
        # 1. Читаем и обновляем статус в proposed_learnings.jsonl
        if not self.queue_file.exists():
            return False, "Proposed learnings file not found."

        all_entries = []
        target_entry = None

        with open(self.queue_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if (
                        data.get("session_id") == session_id
                        and data.get("status") == "pending"
                    ):
                        data["status"] = "approved"
                        target_entry = data
                    all_entries.append(data)

        if not target_entry:
            return (
                False,
                f"Pending proposed learning with session_id {session_id} not found.",
            )

        # Записываем обновленный файл обратно
        with open(self.queue_file, "w", encoding="utf-8") as f:
            for entry in all_entries:
                f.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")

        # 2. Добавляем proposed_rule в AGENTS.md
        if not self.agents_md_file.exists():
            return False, "AGENTS.md file not found."

        try:
            content = self.agents_md_file.read_text(encoding="utf-8")

            # Добавляем в конец файла
            rule_block = f"\n\n## 📝 Добавленное правило (Сессия {session_id})\n{target_entry['proposed_rule'].strip()}\n"

            self.agents_md_file.write_text(content + rule_block, encoding="utf-8")
            return True, None
        except Exception as e:
            return False, f"Failed to modify AGENTS.md: {e}"
