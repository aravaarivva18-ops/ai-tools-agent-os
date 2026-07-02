import json
import os
from pathlib import Path

import yaml

try:
    from tools.checker_review import CheckerReview
    from tools.trace_logger import TraceLogger
except ImportError:
    from checker_review import CheckerReview
    from trace_logger import TraceLogger


class BenchmarkRunner:
    """
    YAML Benchmark Suite & LLM-as-a-Judge.
    Запускает наборы бенчмарков и оценивает качество решений по метрикам
    YAGNI, Stop-Slop, корректности логики и структуры.
    """

    def __init__(self, workspace_root: Path | None = None):
        if workspace_root is None:
            self.workspace_root = Path(os.getcwd())
        else:
            self.workspace_root = workspace_root

        self.benchmarks_dir = self.workspace_root / "tests" / "benchmarks"
        self.trace_logger = TraceLogger(workspace_root=self.workspace_root)

    def load_benchmarks(self) -> list[dict]:
        """Загружает все YAML бенчмарки из папки."""
        benchmarks = []
        if not self.benchmarks_dir.exists():
            return []

        for yaml_path in self.benchmarks_dir.glob("*.yaml"):
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data:
                        benchmarks.append(data)
            except Exception:
                pass
        return benchmarks

    def evaluate_code(self, code: str, benchmark: dict) -> tuple[bool, list[str]]:
        """
        Judge-оценка сгенерированного кода на соответствие рубрике,
        Stop-Slop, YAGNI и синтаксическим критериям.
        """
        warnings = []

        # 1. Проверяем AST
        import ast

        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax Error: {e}"]

        # 2. Проверяем Stop-Slop и YAGNI через CheckerReview
        checker = CheckerReview(workspace_root=self.workspace_root)

        # Временно запишем код, чтобы проверить
        temp_file = self.workspace_root / "scratch" / "temp_eval.py"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            temp_file.write_text(code, encoding="utf-8")
            ok, checker_warnings = checker.review_file(str(temp_file))
            if not ok:
                warnings.extend(checker_warnings)
        finally:
            if temp_file.exists():
                temp_file.unlink()

        # 3. Проверяем ожидаемый фрагмент кода (expected_code)
        expected = benchmark.get("expected_code", "")
        if expected and expected not in code:
            warnings.append(
                f"Logic Error: в коде отсутствует ожидаемый фрагмент '{expected}'."
            )

        # 4. Проверяем текстовые критерии рубрики
        rubrics = benchmark.get("rubric", [])
        code_lower = code.lower()
        for rule in rubrics:
            rule_lower = rule.lower()
            # Простые эвристические проверки рубрик
            if "early return" in rule_lower and "return" not in code_lower:
                warnings.append(f"Rubric Violation: не выполнен критерий '{rule}'")
            if "else" in rule_lower and "else" in code_lower:
                # В правилах запрещено использовать else
                # Проверим, есть ли else (исключая комментарии)
                clean_lines = [
                    line_str.split("#")[0].strip() for line_str in code.splitlines()
                ]
                if any(
                    line.startswith("else:") or line.strip() == "else:"
                    for line in clean_lines
                ):
                    warnings.append(f"Rubric Violation: не выполнен критерий '{rule}'")

        return len(warnings) == 0, warnings

    def run_suite(self, mock_solutions: dict[str, str] | None = None) -> dict:
        """Запускает все бенчмарки и рассчитывает результирующие метрики."""
        benchmarks = self.load_benchmarks()
        results = []
        total_benchmarks = len(benchmarks)
        passed_benchmarks = 0

        # Инициализируем сессию трассировки
        self.trace_logger.start_trace(
            task_id="benchmark-suite-run",
            mode="verify",
            phase="verify",
        )

        for bench in benchmarks:
            bench_id = bench["id"]
            target_path = self.workspace_root / bench["target_file"]
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 1. Записываем начальный код
            target_path.write_text(bench["initial_code"], encoding="utf-8")

            # 2. Получаем решение (симулированное или реальное)
            solution = mock_solutions.get(bench_id) if mock_solutions else None
            if not solution:
                # Если решение не предоставлено, симулируем падение
                solution = bench["initial_code"]

            # Записываем решение в файл
            target_path.write_text(solution, encoding="utf-8")

            # 3. Оцениваем
            success, warnings = self.evaluate_code(solution, bench)

            # Логируем вызов
            self.trace_logger.log_tool_call(
                name=f"evaluate_{bench_id}", ok=success, ms=10.0
            )

            if success:
                passed_benchmarks += 1

            results.append(
                {
                    "id": bench_id,
                    "name": bench["name"],
                    "success": success,
                    "warnings": warnings,
                }
            )

            # Очистка
            if target_path.exists():
                target_path.unlink()

        # Рассчитываем метрики
        success_rate = (
            (passed_benchmarks / total_benchmarks) if total_benchmarks > 0 else 1.0
        )

        suite_metrics = {
            "total": total_benchmarks,
            "passed": passed_benchmarks,
            "task_success_rate": round(success_rate, 4),
            "results": results,
        }

        # Завершаем трассировку
        self.trace_logger.end_trace(
            status="success" if success_rate == 1.0 else "failed"
        )

        return suite_metrics


if __name__ == "__main__":
    runner = BenchmarkRunner()
    metrics = runner.run_suite()
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
