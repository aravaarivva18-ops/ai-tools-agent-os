import json
from pathlib import Path

from tools.trace_logger import TraceLogger


def test_trace_logger_lifecycle():
    # Создаем временную директорию внутри tools/tests, чтобы пройти PathJail
    tmp_dir = Path("/Users/rus/ai-tools/tools/tests/tmp_trace_dir")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger = TraceLogger(workspace_root=tmp_dir)

        # 1. Запуск трейса
        trace = logger.start_trace(
            task_id="test-task-1",
            mode="bugfix",
            phase="inspect",
            issue_type="failing_test",
        )
        assert trace["task_id"] == "test-task-1"
        assert trace["mode"] == "bugfix"
        assert trace["phase"] == "inspect"
        assert trace["validation"]["ast_ok"] is True

        # 2. Обновление контекста
        logger.update_context(tokens_in=1000, tokens_out=200, cached_tokens=500)
        assert logger.current_trace["context"]["tokens_in"] == 1000
        assert logger.current_trace["context"]["tokens_out"] == 200

        # Добавим еще токенов (инкрементация)
        logger.update_context(tokens_in=500)
        assert logger.current_trace["context"]["tokens_in"] == 1500

        # 3. Логирование вызова инструмента
        logger.log_tool_call(name="obsidian_search", ok=True, ms=50.5)
        assert len(logger.current_trace["tools"]) == 1
        assert logger.current_trace["tools"][0]["name"] == "obsidian_search"
        assert logger.current_trace["tools"][0]["ms"] == 50

        # 4. Обновление валидации и исправления
        logger.update_validation(ast_ok=True, tests_passed=False)
        logger.update_repair(
            iteration=1, max_iterations=3, last_failure_kind="assertion"
        )
        assert logger.current_trace["validation"]["tests_passed"] is False
        assert logger.current_trace["repair"]["iteration"] == 1

        # 5. Завершение трейса
        final_trace = logger.end_trace(status="success", provider="anthropic")
        assert final_trace["result"]["status"] == "success"

        # Расчет цены: Sonnet 3.5 ($3/1M input, $15/1M output)
        # 1500 * 3 / 1_000_000 = 0.0045
        # 200 * 15 / 1_000_000 = 0.003
        # Итого: 0.0075 USD
        assert final_trace["cost"]["estimated_usd"] == 0.0075

        # Проверим, что логгер сбросил текущий трейс
        assert logger.current_trace is None

        # Проверим запись в traces.jsonl
        traces_file = tmp_dir / "traces.jsonl"
        assert traces_file.exists()

        with open(traces_file, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 1

        saved_data = json.loads(lines[0])
        assert saved_data["task_id"] == "test-task-1"
        assert saved_data["cost"]["estimated_usd"] == 0.0075
        assert saved_data["prev_hash"] is None
        assert "hash" in saved_data
        first_hash = saved_data["hash"]

        # 6. Запустим и запишем второй трейс для проверки цепочки хэшей
        logger.start_trace(task_id="test-task-2", mode="patch", phase="execute")
        final_trace_2 = logger.end_trace(status="success", provider="anthropic")

        with open(traces_file, encoding="utf-8") as f:
            lines_updated = f.readlines()
        assert len(lines_updated) == 2

        saved_data_2 = json.loads(lines_updated[1])
        assert saved_data_2["task_id"] == "test-task-2"
        assert saved_data_2["prev_hash"] == first_hash
        assert "hash" in saved_data_2
        assert saved_data_2["hash"] != first_hash

    finally:
        # Очистка
        traces_file = tmp_dir / "traces.jsonl"
        if traces_file.exists():
            traces_file.unlink()
        if tmp_dir.exists():
            tmp_dir.rmdir()
