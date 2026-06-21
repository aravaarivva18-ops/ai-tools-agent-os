import json
from pathlib import Path

from tools.self_improve import (
    apply_improvement_record,
    generate_improvement_report,
    maintain_constitution,
)


def test_generate_improvement_report(tmp_path):
    # Prepare dummy friction logs JSON
    friction_logs_path = tmp_path / "friction_logs.json"
    output_report_path = tmp_path / "self_improvement_report.md"

    dummy_logs = [
        {
            "session_id": "session123",
            "date": "2026-06-20",
            "source_file": "handoff_1.md",
            "friction_points": [
                {
                    "heading": "Ошибка OOM",
                    "content": "Out of memory error occurred when processing 20k tokens.",
                }
            ],
            "metrics": {"stealth_stop": False, "loc_delta": 10, "time_saved_min": 15},
        },
        {
            "session_id": "session456",
            "date": "2026-06-21",
            "source_file": "handoff_2.md",
            "friction_points": [
                {"heading": "Ошибка OOM", "content": "Another memory allocation fail."},
                {
                    "heading": "Зависание тестов",
                    "content": "pytest hanging on database cleanup.",
                },
            ],
            "metrics": {"stealth_stop": False, "loc_delta": -25, "time_saved_min": 30},
        },
    ]

    # Prepare mock skills directory
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Scale skill
    scale_skill = skills_dir / "automation-task"
    scale_skill.mkdir()
    (scale_skill / "SKILL.md").write_text(
        "---\nname: automation-task\n---\nScale and productivity", encoding="utf-8"
    )

    # SEO skill
    seo_skill = skills_dir / "seo-campaign"
    seo_skill.mkdir()
    (seo_skill / "SKILL.md").write_text(
        "---\nname: seo-campaign\n---\nSEO crawler strategy", encoding="utf-8"
    )

    with open(friction_logs_path, "w", encoding="utf-8") as f:
        json.dump(dummy_logs, f)

    metrics = generate_improvement_report(
        friction_logs_path, output_report_path, skills_dir_path=skills_dir
    )

    assert metrics["total_sessions"] == 2
    assert metrics["total_friction_points"] == 3
    assert metrics["categories_count"] == 2

    # Verify report is created and has correct markdown content
    assert output_report_path.exists()
    report_content = output_report_path.read_text(encoding="utf-8")
    assert "# ⚡ Отчет системы самообучения агента" in report_content
    assert "**Проанализировано сессий (лимит 5)**: 2" in report_content
    assert "**Выявлено точек трения (friction points)**: 3" in report_content
    assert "Категория: Ошибка OOM" in report_content
    assert "Категория: Зависание тестов" in report_content
    assert "Реестр паттернов ошибок" in report_content
    assert "Очередь авто-исправления" in report_content
    assert "Дельта-метрики сессий" in report_content
    assert "Эффективность делегирования (Buyback & Scale Metrics)" in report_content
    assert "**Выкуп времени (Buyback Time)**: 0.8 ч." in report_content
    assert "**Всего создано JIT-навыков (JIT Skills)**: 2" in report_content
    assert "Автоматизация и масштаб (Scale/Productivity): 1" in report_content
    assert "SEO и GEO оптимизация: 1" in report_content


def test_stealth_stop_boosts_priority(tmp_path):
    # negative test to verify stealth stop is caught and raises priority score
    friction_logs_path = tmp_path / "friction_logs.json"
    output_report_path = tmp_path / "self_improvement_report.md"

    dummy_logs = [
        {
            "session_id": "session_stealth",
            "date": "2026-06-22",
            "source_file": "handoff_stealth.md",
            "friction_points": [
                {
                    "heading": "Зависание тестов",
                    "content": "Stealth stop triggered because test failed 3 times.",
                }
            ],
            "metrics": {"stealth_stop": True, "loc_delta": 5, "time_saved_min": 5},
        }
    ]

    with open(friction_logs_path, "w", encoding="utf-8") as f:
        json.dump(dummy_logs, f)

    generate_improvement_report(friction_logs_path, output_report_path)
    report_content = output_report_path.read_text(encoding="utf-8")

    # 7 (base weight for test error) + 5 (stealth stop boost) = 12 score
    # Score is 12 * 1 (freq) = 12
    assert "Зависание тестов" in report_content
    assert "12" in report_content
    assert "⚠️ Да" in report_content


def test_apply_improvement_record(tmp_path):
    handoff_notes_path = tmp_path / "handoff_notes.md"
    handoff_notes_path.write_text("# Handoff Notes\n", encoding="utf-8")

    metrics = {"total_sessions": 5, "total_friction_points": 12}

    apply_improvement_record(handoff_notes_path, metrics)

    content = handoff_notes_path.read_text(encoding="utf-8")
    assert "[Self-Improvement Loop]" in content
    assert "Сессий=5" in content
    assert "Точек трения=12" in content


def test_delta_stability_metrics(tmp_path):
    """Тестирует расчет тренда стабильности тестов по сессиям."""
    friction_logs_path = tmp_path / "friction_logs.json"
    output_report_path = tmp_path / "self_improvement_report.md"

    dummy_logs = [
        {
            "session_id": "session1",
            "date": "2026-06-20",
            "source_file": "handoff_1.md",
            "friction_points": [
                {"heading": "Ошибка тестов", "content": "test_failed_db.py failure"}
            ],
            "metrics": {
                "stealth_stop": False,
                "loc_delta": 10,
                "time_saved_min": 15,
                "tests_passed": 8,
                "tests_failed": 2,
            },
        },
        {
            "session_id": "session2",
            "date": "2026-06-21",
            "source_file": "handoff_2.md",
            "friction_points": [
                {"heading": "Ошибка тестов", "content": "test_failed_db.py again"}
            ],
            "metrics": {
                "stealth_stop": False,
                "loc_delta": 20,
                "time_saved_min": 25,
                "tests_passed": 10,
                "tests_failed": 0,
            },
        },
    ]

    with open(friction_logs_path, "w", encoding="utf-8") as f:
        json.dump(dummy_logs, f)

    generate_improvement_report(friction_logs_path, output_report_path)
    assert output_report_path.exists()
    report_content = output_report_path.read_text(encoding="utf-8")

    # Проверяем, что в отчете рассчитались стабильность и пройденные тесты
    assert "Успешных тестов всего**: 18" in report_content
    assert "Неуспешных тестов всего**: 2" in report_content
    assert "Динамика стабильности тестов" in report_content
    assert "Ранее: 80.0% успеваемости тестов, сейчас: 100.0%" in report_content
    assert "📈 (Улучшение стабильности)" in report_content


def test_auto_heal_queue_generation(tmp_path):
    """Тестирует извлечение тестовых файлов и генерацию auto_heal_queue.json."""
    friction_logs_path = tmp_path / "friction_logs.json"
    output_report_path = tmp_path / "self_improvement_report.md"
    queue_path = Path("/Users/rus/ai-tools/vault/auto_heal_queue.json")

    # Remove existing file if any
    if queue_path.exists():
        queue_path.unlink()

    dummy_logs = [
        {
            "session_id": "session_test",
            "date": "2026-06-20",
            "source_file": "handoff.md",
            "friction_points": [
                {
                    "heading": "Ошибка тестов",
                    "content": "Failed testing in tools/tests/test_rules_audit.py and tools/test_healer.py",
                }
            ],
            "metrics": {
                "stealth_stop": False,
                "loc_delta": 5,
                "time_saved_min": 10,
                "tests_passed": 1,
                "tests_failed": 1,
            },
        }
    ]

    with open(friction_logs_path, "w", encoding="utf-8") as f:
        json.dump(dummy_logs, f)

    generate_improvement_report(friction_logs_path, output_report_path)

    # Проверяем, что файл auto_heal_queue.json создался и содержит кандидатов
    assert queue_path.exists()
    with open(queue_path, encoding="utf-8") as f:
        queue_data = json.load(f)

    assert "tools/tests/test_rules_audit.py" in queue_data["heal_candidates"]
    assert "tools/test_healer.py" in queue_data["heal_candidates"]
    assert len(queue_data["priority_registry"]) == 1


def test_maintain_constitution_flow(tmp_path):
    """Проверяет сквозной процесс нормализации и создания бэкапа в maintain_constitution."""
    constitution_file = tmp_path / "GEMINI_ANTIGRAVITY.md"
    content = (
        "# GEMINI_ANTIGRAVITY\n"
        "\n"
        "## 🏛️ 5. Раздел один\n"
        "Текст один\n"
        "\n"
        "## 🧠 9. Раздел два\n"
        "Текст два\n"
    )
    constitution_file.write_text(content, encoding="utf-8")

    # Выполняем нормализацию
    maintain_constitution(constitution_file)

    # Проверяем, что заголовки перенумерованы
    fixed_content = constitution_file.read_text(encoding="utf-8")
    assert "## 🏛️ 1. Раздел один" in fixed_content
    assert "## 🧠 2. Раздел два" in fixed_content
    assert "## 🏛️ Ядро (Core Imperatives)" in fixed_content

    # Проверяем, что создался бэкап
    backups = list(tmp_path.glob("GEMINI_ANTIGRAVITY.md.bak.*"))
    assert len(backups) == 1
    assert "## 🏛️ 5. Раздел один" in backups[0].read_text(encoding="utf-8")

