import yaml

from tools.run_benchmarks import BenchmarkRunner


def test_load_benchmarks(tmp_path):
    # Создаем фиктивный каталог бенчмарков
    bench_dir = tmp_path / "tests" / "benchmarks"
    bench_dir.mkdir(parents=True, exist_ok=True)

    # Записываем тестовый YAML
    bench_data = {
        "id": "test_bench_1",
        "name": "Test Benchmark",
        "target_file": "scratch/test_target.py",
        "initial_code": "def hello(): pass",
        "expected_code": "def hello():\n    return 'world'",
        "rubric": ["Must use early return"],
    }

    yaml_file = bench_dir / "test_bench.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(bench_data, f)

    runner = BenchmarkRunner(workspace_root=tmp_path)
    loaded = runner.load_benchmarks()

    assert len(loaded) == 1
    assert loaded[0]["id"] == "test_bench_1"
    assert loaded[0]["name"] == "Test Benchmark"


def test_evaluate_code_syntax_error(tmp_path):
    runner = BenchmarkRunner(workspace_root=tmp_path)
    benchmark = {
        "id": "test_bench",
        "expected_code": "def foo()",
        "rubric": [],
    }

    # Некорректный синтаксис
    success, warnings = runner.evaluate_code("def foo(:", benchmark)
    assert success is False
    assert any("Syntax Error" in w for w in warnings)


def test_evaluate_code_logic_and_rubric(tmp_path):
    runner = BenchmarkRunner(workspace_root=tmp_path)
    benchmark = {
        "id": "test_bench",
        "expected_code": "return 'success'",
        "rubric": ["Must not use else block"],
    }

    # Идеальный код
    code_ok = """def handle():
    if not val:
        return 'success'
    return 'failed'
"""
    success, warnings = runner.evaluate_code(code_ok, benchmark)
    assert success is True
    assert len(warnings) == 0

    # Код без ожидаемой строки
    code_bad_logic = """def handle():
    return 'failed'
"""
    success, warnings = runner.evaluate_code(code_bad_logic, benchmark)
    assert success is False
    assert any("Logic Error" in w for w in warnings)

    # Код с использованием else (нарушение рубрики)
    code_bad_else = """def handle():
    if not val:
        return 'success'
    else:
        return 'failed'
"""
    success, warnings = runner.evaluate_code(code_bad_else, benchmark)
    assert success is False
    assert any("Rubric Violation" in w for w in warnings)


def test_run_suite_success(tmp_path):
    bench_dir = tmp_path / "tests" / "benchmarks"
    bench_dir.mkdir(parents=True, exist_ok=True)

    bench_data = {
        "id": "bench_1",
        "name": "Benchmark 1",
        "target_file": "scratch/target_1.py",
        "initial_code": "def func(): pass",
        "expected_code": "return 42",
        "rubric": [],
    }

    with open(bench_dir / "bench_1.yaml", "w", encoding="utf-8") as f:
        yaml.dump(bench_data, f)

    runner = BenchmarkRunner(workspace_root=tmp_path)

    # Симулируем успешное решение
    mock_solutions = {"bench_1": "def func():\n    return 42\n"}

    metrics = runner.run_suite(mock_solutions=mock_solutions)

    assert metrics["total"] == 1
    assert metrics["passed"] == 1
    assert metrics["task_success_rate"] == 1.0
    assert metrics["results"][0]["success"] is True
