import json

from tools.self_improve import apply_improvement_record, generate_improvement_report


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
                    "content": "Out of memory error occurred when processing 20k tokens."
                }
            ],
            "metrics": {
                "stealth_stop": False,
                "loc_delta": 10,
                "time_saved_min": 15
            }
        },
        {
            "session_id": "session456",
            "date": "2026-06-21",
            "source_file": "handoff_2.md",
            "friction_points": [
                {
                    "heading": "Ошибка OOM",
                    "content": "Another memory allocation fail."
                },
                {
                    "heading": "Зависание тестов",
                    "content": "pytest hanging on database cleanup."
                }
            ],
            "metrics": {
                "stealth_stop": False,
                "loc_delta": -25,
                "time_saved_min": 30
            }
        }
    ]

    with open(friction_logs_path, "w", encoding="utf-8") as f:
        json.dump(dummy_logs, f)

    metrics = generate_improvement_report(friction_logs_path, output_report_path)

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
                    "content": "Stealth stop triggered because test failed 3 times."
                }
            ],
            "metrics": {
                "stealth_stop": True,
                "loc_delta": 5,
                "time_saved_min": 5
            }
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

    metrics = {
        "total_sessions": 5,
        "total_friction_points": 12
    }

    apply_improvement_record(handoff_notes_path, metrics)

    content = handoff_notes_path.read_text(encoding="utf-8")
    assert "[Self-Improvement Loop]" in content
    assert "Сессий=5" in content
    assert "Точек трения=12" in content
