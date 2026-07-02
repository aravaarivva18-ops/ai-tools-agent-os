import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path


class TraceLogger:
    """
    Класс локальной структурированной трассировки (traces.jsonl).
    Записывает метрики выполнения задач, вызовов инструментов и токенов.
    """

    def __init__(self, workspace_root: Path | None = None):
        if workspace_root is None:
            self.workspace_root = Path(os.getcwd())
        else:
            self.workspace_root = workspace_root

        self.traces_file = self.workspace_root / "traces.jsonl"
        self.current_trace = None

    def start_trace(
        self,
        task_id: str,
        mode: str,
        phase: str,
        repo: str = "ai-tools",
        issue_type: str = "general",
        ruleset: list[str] | None = None,
    ) -> dict:
        """Инициализирует новый трейс для текущей сессии."""
        self.current_trace = {
            "ts": datetime.now(UTC).isoformat(),
            "task_id": task_id,
            "mode": mode,
            "phase": phase,
            "repo": repo,
            "issue_type": issue_type,
            "ruleset": ruleset or ["core"],
            "context": {
                "tokens_in": 0,
                "tokens_out": 0,
                "cached_tokens": 0,
                "files_read": 0,
                "file_slices": 0,
                "lines_loaded": 0,
            },
            "tools": [],
            "validation": {
                "ast_ok": True,
                "placeholder_ok": True,
                "ast_grep_ok": True,
                "semgrep_ok": True,
                "tests_passed": True,
            },
            "repair": {
                "iteration": 0,
                "max_iterations": 5,
                "last_failure_kind": None,
            },
            "cost": {
                "provider": "anthropic",
                "estimated_usd": 0.0,
            },
            "result": {
                "status": "started",
                "manual_review_required": False,
            },
        }
        return self.current_trace

    def log_tool_call(self, name: str, ok: bool, ms: float) -> None:
        """Добавляет информацию о вызове инструмента."""
        if not self.current_trace:
            return
        self.current_trace["tools"].append({"name": name, "ok": ok, "ms": int(ms)})

    def update_context(
        self,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cached_tokens: int = 0,
        files_read: int = 0,
        file_slices: int = 0,
        lines_loaded: int = 0,
    ) -> None:
        """Обновляет информацию об использовании контекста."""
        if not self.current_trace:
            return
        ctx = self.current_trace["context"]
        if tokens_in:
            ctx["tokens_in"] += tokens_in
        if tokens_out:
            ctx["tokens_out"] += tokens_out
        if cached_tokens:
            ctx["cached_tokens"] += cached_tokens
        if files_read:
            ctx["files_read"] += files_read
        if file_slices:
            ctx["file_slices"] += file_slices
        if lines_loaded:
            ctx["lines_loaded"] += lines_loaded

    def update_validation(
        self,
        ast_ok: bool | None = None,
        placeholder_ok: bool | None = None,
        ast_grep_ok: bool | None = None,
        semgrep_ok: bool | None = None,
        tests_passed: bool | None = None,
    ) -> None:
        """Обновляет состояние валидаторов."""
        if not self.current_trace:
            return
        val = self.current_trace["validation"]
        if ast_ok is not None:
            val["ast_ok"] = ast_ok
        if placeholder_ok is not None:
            val["placeholder_ok"] = placeholder_ok
        if ast_grep_ok is not None:
            val["ast_grep_ok"] = ast_grep_ok
        if semgrep_ok is not None:
            val["semgrep_ok"] = semgrep_ok
        if tests_passed is not None:
            val["tests_passed"] = tests_passed

    def update_repair(
        self,
        iteration: int | None = None,
        max_iterations: int | None = None,
        last_failure_kind: str | None = None,
    ) -> None:
        """Обновляет данные цикла самоисправления."""
        if not self.current_trace:
            return
        rep = self.current_trace["repair"]
        if iteration is not None:
            rep["iteration"] = iteration
        if max_iterations is not None:
            rep["max_iterations"] = max_iterations
        if last_failure_kind is not None:
            rep["last_failure_kind"] = last_failure_kind

    def end_trace(
        self,
        status: str,
        provider: str = "anthropic",
        manual_review_required: bool = False,
    ) -> dict:
        """Завершает трейс, рассчитывает стоимость и записывает его в traces.jsonl."""
        if not self.current_trace:
            raise ValueError("No active trace to end.")

        self.current_trace["result"]["status"] = status
        self.current_trace["result"]["manual_review_required"] = manual_review_required
        self.current_trace["cost"]["provider"] = provider

        # Расчет стоимости
        tokens_in = self.current_trace["context"]["tokens_in"]
        tokens_out = self.current_trace["context"]["tokens_out"]

        # Примерный тариф: Anthropic Sonnet 3.5 ($3/1M input, $15/1M output)
        if provider == "anthropic":
            cost = (tokens_in * 3.0 / 1_000_000) + (tokens_out * 15.0 / 1_000_000)
        elif provider == "openai":
            cost = (tokens_in * 5.0 / 1_000_000) + (tokens_out * 15.0 / 1_000_000)
        else:
            cost = 0.0

        self.current_trace["cost"]["estimated_usd"] = round(cost, 5)

        # Читаем prev_hash последней записи в traces.jsonl
        prev_hash = None
        if self.traces_file.exists() and self.traces_file.stat().st_size > 0:
            try:
                with open(self.traces_file, encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last_trace = json.loads(lines[-1].strip())
                        prev_hash = last_trace.get("hash")
            except Exception:
                pass

        self.current_trace["prev_hash"] = prev_hash

        # Вычисляем SHA256 хэш текущей записи (детерминированная сериализация)
        serialized = json.dumps(self.current_trace, sort_keys=True, ensure_ascii=False)
        sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self.current_trace["hash"] = sha256

        # Запись в traces.jsonl
        # Убедимся, что родительские папки созданы (если traces.jsonl лежит глубже)
        self.traces_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.traces_file, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(self.current_trace, sort_keys=True, ensure_ascii=False)
                + "\n"
            )

        trace_copy = self.current_trace
        self.current_trace = None
        return trace_copy
