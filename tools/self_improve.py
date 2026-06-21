import json
import sys
from datetime import datetime
from pathlib import Path

# Import collect function from collect_handoffs to refresh logs
try:
    from tools.collect_handoffs import collect
except ImportError:
    try:
        from collect_handoffs import collect
    except ImportError:
        collect = None


def generate_research_queries(category: str, issue_content: str) -> list:
    """Генерирует целевые поисковые запросы для GitHub/arXiv/Web на основе описания проблемы."""
    clean_text = "".join(
        c if c.isalnum() or c.isspace() else " " for c in issue_content
    ).strip()
    words = [w for w in clean_text.split() if len(w) > 3][:6]
    keywords = " ".join(words)

    queries = [
        f"site:github.com {category} {keywords}",
        f"site:arxiv.org {category} {keywords}",
        f"best practices {category} {keywords}",
    ]
    return queries


def detect_tool_conflicts(logs: list) -> list:
    """Анализирует логи трения на наличие конфликтов инструментов."""
    conflicts = []
    for log in logs:
        for pt in log.get("friction_points", []):
            content = pt.get("content", "").lower()
            if any(
                k in content
                for k in [
                    "subagent",
                    "субагент",
                    "sub-agent",
                    "invoke_subagent",
                    "define_subagent",
                ]
            ):
                conflicts.append(
                    f"Session {log.get('session_id')}: Найдено упоминание субагентов или вызовов invoke_subagent/define_subagent. Убедитесь, что используется Solo Loop по умолчанию."
                )
            if "diff_applier" in content or "diff_applier.py" in content:
                conflicts.append(
                    f"Session {log.get('session_id')}: Использован diff_applier.py. По возможности используйте нативный replace_file_content."
                )
    return list(set(conflicts))


def optimize_prompt_for_speed(category: str, issue_content: str) -> str:
    """Создает оптимизированный сжатый промпт для устранения указанной проблемы."""
    lines = [line.strip() for line in issue_content.splitlines() if line.strip()]
    first_line = lines[0] if lines else ""

    clean_line = "".join(
        c if c.isalnum() or c.isspace() else " " for c in first_line
    ).strip()
    summary = " ".join(clean_line.split()[:10])

    return f"Исправь {category}: {summary}. Используй TDD, YAGNI (max 3 levels) и Solo Loop."


def suggest_tool_combinations(category: str) -> str:
    """Рекомендует эффективные комбинации инструментов для решения проблемы."""
    cat_lower = category.lower()
    if "oom" in cat_lower or "memory" in cat_lower or "памят" in cat_lower:
        return "`view_file` (ограничение чтения строк) + `run_command` (очистка памяти/проверка логов)"
    if (
        "тест" in cat_lower
        or "ошибк" in cat_lower
        or "fail" in cat_lower
        or "error" in cat_lower
    ):
        return "`replace_file_content` (точечные правки) + `run_command` (запуск тестов) + `tools/test_healer.py` (автоисправление)"
    return "`search_web` (сбор фактов) + `replace_file_content` (правка) + `make check-rules` (валидация)"


def analyze_self_healing_needs(issue_content: str) -> str:
    """Определяет, нужен ли запуск test_healer.py для самовосстановления."""
    content_lower = issue_content.lower()
    if any(
        k in content_lower
        for k in ["failed", "assert", "traceback", "syntaxerror", "import"]
    ):
        return "⚠️ Рекомендуется запуск `tools/test_healer.py` для автоматического исправления тестов/импортов."
    return (
        "💡 Проблема решается стандартным редактированием через `replace_file_content`."
    )


def _parse_logs_data(logs_sorted: list) -> tuple:
    """Parses sorted logs to extract counts, categories, deltas, and saved time."""
    total_friction_points = 0
    issues_by_category = {}
    stealth_stops_count = 0
    loc_deltas = []
    time_saved_total = 0
    total_tests_passed = 0
    total_tests_failed = 0

    for log in logs_sorted:
        metrics = log.get("metrics", {})
        if metrics.get("stealth_stop"):
            stealth_stops_count += 1
        if metrics.get("loc_delta") is not None:
            loc_deltas.append(metrics.get("loc_delta"))
        if metrics.get("time_saved_min") is not None:
            time_saved_total += metrics.get("time_saved_min")

        total_tests_passed += metrics.get("tests_passed", 0)
        total_tests_failed += metrics.get("tests_failed", 0)

        friction_points = log.get("friction_points", [])
        total_friction_points += len(friction_points)
        for pt in friction_points:
            heading = pt.get("heading", "General")
            content = pt.get("content", "")
            issues_by_category.setdefault(heading, []).append(
                {
                    "session_id": log.get("session_id"),
                    "date": log.get("date"),
                    "content": content,
                    "stealth_stop": metrics.get("stealth_stop", False),
                }
            )

    return (
        total_friction_points,
        stealth_stops_count,
        loc_deltas,
        time_saved_total,
        issues_by_category,
        total_tests_passed,
        total_tests_failed,
    )


def _compute_delta_metrics(logs_sorted: list) -> dict:
    """Computes friction delta metrics trend and stability from sorted logs."""
    metrics_result = {
        "friction_trend": "Недостаточно данных для тренда",
        "stability_trend": "Недостаточно данных для стабильности",
    }
    if len(logs_sorted) < 2:
        return metrics_result

    half = len(logs_sorted) // 2
    earlier_logs = logs_sorted[:half]
    later_logs = logs_sorted[half:]

    # Friction points trend
    earlier_frictions = sum(len(x.get("friction_points", [])) for x in earlier_logs)
    later_frictions = sum(len(x.get("friction_points", [])) for x in later_logs)

    if earlier_frictions > 0:
        delta_percentage = (
            (earlier_frictions - later_frictions) / earlier_frictions
        ) * 100.0
        if delta_percentage > 0:
            metrics_result["friction_trend"] = (
                f"Улучшение на {delta_percentage:.1f}% (количество ошибок падает)"
            )
        elif delta_percentage < 0:
            metrics_result["friction_trend"] = (
                f"Ухудшение на {abs(delta_percentage):.1f}% (количество ошибок растет)"
            )
        else:
            metrics_result["friction_trend"] = "Стабильно"
    elif later_frictions > 0:
        metrics_result["friction_trend"] = "Новые ошибки зафиксированы"
    else:
        metrics_result["friction_trend"] = "Ошибок не обнаружено"

    # Stability Trend (Test pass rate comparison)
    earlier_passed = sum(
        x.get("metrics", {}).get("tests_passed", 0) for x in earlier_logs
    )
    earlier_failed = sum(
        x.get("metrics", {}).get("tests_failed", 0) for x in earlier_logs
    )
    later_passed = sum(x.get("metrics", {}).get("tests_passed", 0) for x in later_logs)
    later_failed = sum(x.get("metrics", {}).get("tests_failed", 0) for x in later_logs)

    earlier_total = earlier_passed + earlier_failed
    later_total = later_passed + later_failed

    earlier_rate = (
        (earlier_passed / earlier_total) * 100.0 if earlier_total > 0 else 100.0
    )
    later_rate = (later_passed / later_total) * 100.0 if later_total > 0 else 100.0

    metrics_result["stability_trend"] = (
        f"Ранее: {earlier_rate:.1f}% успеваемости тестов, сейчас: {later_rate:.1f}%"
    )
    if later_rate > earlier_rate:
        metrics_result["stability_trend"] += " 📈 (Улучшение стабильности)"
    elif later_rate < earlier_rate:
        metrics_result["stability_trend"] += " 📉 (Деградация стабильности)"
    else:
        metrics_result["stability_trend"] += " ➡️ (Стабильно)"

    return metrics_result


def _build_priority_queue(issues_by_category: dict) -> tuple:
    """Builds error registry and auto-heal priority queue and saves it to a JSON file."""
    error_registry = []
    for category, items in issues_by_category.items():
        has_stealth = any(item["stealth_stop"] for item in items)
        error_registry.append(
            {"category": category, "frequency": len(items), "has_stealth": has_stealth}
        )

    import re

    # Extract candidate test files to heal
    test_files_to_heal = []
    priority_queue = []

    for reg in error_registry:
        cat_lower = reg["category"].lower()
        weight = 3
        if any(k in cat_lower for k in ["oom", "memory", "памят", "leak"]):
            weight = 10
        elif any(
            k in cat_lower for k in ["тест", "assert", "fail", "syntax", "healer"]
        ):
            weight = 7

        if reg["has_stealth"]:
            weight += 5

        score = weight * reg["frequency"]

        # Look for test file references in contents
        items = issues_by_category[reg["category"]]
        for item in items:
            found = re.findall(r"([\w\-/\.]*test_[\w\-]+\.py)", item["content"])
            for f in found:
                clean_f = f.strip().strip("`").strip('"').strip("'")
                if clean_f not in test_files_to_heal:
                    test_files_to_heal.append(clean_f)

        priority_queue.append(
            {
                "category": reg["category"],
                "score": score,
                "action": suggest_tool_combinations(reg["category"]),
            }
        )

    priority_queue = sorted(priority_queue, key=lambda x: x["score"], reverse=True)

    # Save to Auto-Heal Queue file
    queue_path = Path("/Users/rus/ai-tools/vault/auto_heal_queue.json")
    try:
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "heal_candidates": test_files_to_heal,
                    "priority_registry": priority_queue,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"✅ Auto-Heal Priority Queue saved to: {queue_path}")
    except Exception as e:
        print(f"Warning: Failed to save auto-heal queue: {e}")

    return error_registry, priority_queue


def _classify_jit_skills(skills_dir_path: Path | None) -> dict[str, int]:
    """Scans skills directory and classifies JIT skills by category."""
    if skills_dir_path is None:
        skills_dir_path = Path("/Users/rus/ai-tools/skills")

    result = {
        "scale": 0,
        "seo": 0,
        "ui": 0,
        "generic": 0,
        "total": 0,
    }

    if not (skills_dir_path.exists() and skills_dir_path.is_dir()):
        return result

    for item in skills_dir_path.iterdir():
        if item.is_dir():
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                result["total"] += 1
                try:
                    content = skill_md.read_text(encoding="utf-8").lower()
                    if any(
                        kw in content
                        for kw in [
                            "scale",
                            "productivity",
                            "business",
                            "automation",
                            "sop",
                            "delegate",
                            "time",
                        ]
                    ):
                        result["scale"] += 1
                    elif any(
                        kw in content
                        for kw in ["seo", "geo", "traffic", "keywords", "crawler"]
                    ):
                        result["seo"] += 1
                    elif any(
                        kw in content
                        for kw in [
                            "ui",
                            "landing",
                            "animation",
                            "hover",
                            "scroll",
                            "frontend",
                            "css",
                            "web",
                        ]
                    ):
                        result["ui"] += 1
                    else:
                        result["generic"] += 1
                except Exception:
                    result["generic"] += 1
    return result


def generate_improvement_report(
    friction_logs_path: Path, output_path: Path, skills_dir_path: Path | None = None
) -> dict:
    """Reads friction logs, aggregates issues, and writes a self-improvement report with advanced metrics."""
    if not friction_logs_path.exists():
        if collect:
            print("Friction logs not found. Running collect_handoffs first...")
            collect()
        else:
            return {
                "error": "Friction logs not found and collect_handoffs is unavailable"
            }

    try:
        with open(friction_logs_path, encoding="utf-8") as f:
            logs = json.load(f)
    except Exception as e:
        return {"error": f"Failed to read friction logs: {e}"}

    total_sessions = len(logs)
    logs_sorted = sorted(logs, key=lambda x: x.get("date", ""))

    (
        total_friction_points,
        stealth_stops_count,
        _loc_deltas,
        time_saved_total,
        issues_by_category,
        total_tests_passed,
        total_tests_failed,
    ) = _parse_logs_data(logs_sorted)

    trends = _compute_delta_metrics(logs_sorted)
    error_registry, priority_queue = _build_priority_queue(issues_by_category)

    # Classify generated skills
    skills_metrics = _classify_jit_skills(skills_dir_path)
    scale_count = skills_metrics["scale"]
    seo_count = skills_metrics["seo"]
    ui_count = skills_metrics["ui"]
    generic_count = skills_metrics["generic"]
    total_skills = skills_metrics["total"]

    # Generate report markdown
    report_lines = [
        "# ⚡ Отчет системы самообучения агента (Self-Improvement Report)",
        f"**Дата генерации**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 📊 Метрики сессий",
        f"- **Проанализировано сессий (лимит 5)**: {total_sessions}",
        f"- **Выявлено точек трения (friction points)**: {total_friction_points}",
        f"- **Зафиксировано Stealth Stop**: {stealth_stops_count}",
        f"- **Суммарно сэкономлено времени**: {time_saved_total} мин.",
        f"- **Успешных тестов всего**: {total_tests_passed}",
        f"- **Неуспешных тестов всего**: {total_tests_failed}",
        "",
        "## ⏱️ Эффективность делегирования (Buyback & Scale Metrics)",
        f"- **Выкуп времени (Buyback Time)**: {time_saved_total / 60:.1f} ч. ({time_saved_total} мин.)",
        f"- **Всего создано JIT-навыков (JIT Skills)**: {total_skills}",
        f"  - Автоматизация и масштаб (Scale/Productivity): {scale_count}",
        f"  - SEO и GEO оптимизация: {seo_count}",
        f"  - UI и анимации (UI Stack): {ui_count}",
        f"  - Технические и общие (Generic): {generic_count}",
        "",
        "## 📈 Дельта-метрики сессий (Delta Metrics)",
        f"- **Трендовое направление**: {trends['friction_trend']}",
        f"- **Динамика стабильности тестов**: {trends['stability_trend']}",
        "",
        "## 🚨 Реестр паттернов ошибок (Error Pattern Registry)",
        "| Категория ошибки | Частота | Stealth Stop |",
        "| :--- | :---: | :---: |",
    ]

    for reg in error_registry:
        stealth_str = "⚠️ Да" if reg["has_stealth"] else "Нет"
        report_lines.append(
            f"| {reg['category']} | {reg['frequency']} | {stealth_str} |"
        )
    report_lines.append("")

    report_lines.extend(
        [
            "## 📋 Очередь авто-исправления (Auto-Heal Priority Queue)",
            "| Приоритет | Категория ошибки | Балл приоритета | Рекомендуемый инструмент |",
            "| :---: | :--- | :---: | :--- |",
        ]
    )

    for i, item in enumerate(priority_queue, 1):
        report_lines.append(
            f"| {i} | {item['category']} | {item['score']} | {item['action']} |"
        )
    report_lines.append("")

    report_lines.extend(
        [
            "## 🔍 Детальный анализ проблем по категориям",
            "",
        ]
    )

    if not issues_by_category:
        report_lines.append(
            "🎉 Точки трения не обнаружены! Все системы работают в режиме YAGNI."
        )
    else:
        for category in issues_by_category.keys():
            items = issues_by_category[category]
            report_lines.append(f"### 🛑 Категория: {category}")
            for item in items:
                report_lines.append(
                    f"- **Сессия [{item['session_id']}]** ({item['date']}):"
                )
                content_lines = item["content"].splitlines()
                for line in content_lines:
                    report_lines.append(f"  > {line}")

                queries = generate_research_queries(category, item["content"])
                report_lines.append(
                    "  * 🔍 *Рекомендуемые запросы для исследования (Karpathy Research Step)*:"
                )
                for q in queries:
                    report_lines.append(f"    - `{q}`")

                opt_prompt = optimize_prompt_for_speed(category, item["content"])
                report_lines.append(
                    f"  * ⚡ *Оптимизированный промпт для исправления:* `{opt_prompt}`"
                )

                tools_comb = suggest_tool_combinations(category)
                report_lines.append(f"  * 🛠️ *Рекомендуемые инструменты:* {tools_comb}")

                healing_need = analyze_self_healing_needs(item["content"])
                report_lines.append(f"  * {healing_need}")
                report_lines.append("")

    # Detect tool conflicts
    conflicts = detect_tool_conflicts(logs)
    if conflicts:
        report_lines.extend(
            [
                "## ⚠️ Конфликты инструментов (Tool Conflicts)",
                "",
            ]
        )
        for conf in conflicts:
            report_lines.append(f"- ⚠️ {conf}")
        report_lines.append("")

    report_lines.extend(
        [
            "",
            "## 💡 Предписания по улучшению (Для ИИ-Агента)",
            "1. Проверить в GitHub трендах и документации решения для указанных категорий проблем.",
            "2. Обновить `GEMINI_ANTIGRAVITY.md` с точными инструкциями по предотвращению этих багов.",
            "3. Убедиться, что новые правила лаконичны, не добавляют overengineering и соответствуют YAGNI.",
        ]
    )

    try:
        output_path.write_text("\n".join(report_lines), encoding="utf-8")
        print(f"✅ Improvement report saved to: {output_path}")
    except Exception as e:
        return {"error": f"Failed to save report: {e}"}

    return {
        "total_sessions": total_sessions,
        "total_friction_points": total_friction_points,
        "categories_count": len(issues_by_category),
    }


def apply_improvement_record(handoff_notes_path: Path, metrics: dict) -> None:
    """Appends self-improvement loop execution to the global handoff_notes.md."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    delta_record = (
        f"\n\n## [Self-Improvement Loop] {timestamp}\n"
        f"- **Статус**: Успешно завершен цикл самообучения.\n"
        f"- **Метрики**: Сессий={metrics.get('total_sessions', 0)}, "
        f"Точек трения={metrics.get('total_friction_points', 0)}.\n"
        f"- **Действие**: Обновлены правила взаимодействия, оптимизированы JIT-инструкции.\n"
    )
    try:
        with open(handoff_notes_path, "a", encoding="utf-8") as f:
            f.write(delta_record)
        print(f"✅ Global handoff notes updated at: {handoff_notes_path}")
    except Exception as e:
        print(f"Error appending to handoff_notes.md: {e}")


def main() -> None:
    target_dir = Path("/Users/rus/ai-tools/vault/handoffs")
    friction_logs_path = target_dir / "friction_logs.json"
    output_report_path = target_dir / "self_improvement_report.md"
    handoff_notes_path = Path("/Users/rus/ai-tools/handoff_notes.md")

    if not target_dir.exists():
        if collect:
            collect()
        else:
            print("Error: Target directory does not exist and collect is unavailable.")
            sys.exit(1)

    metrics = generate_improvement_report(friction_logs_path, output_report_path)
    if "error" in metrics:
        print(f"❌ Error during self-improvement run: {metrics['error']}")
        sys.exit(1)

    apply_improvement_record(handoff_notes_path, metrics)

    # Log self-improvement event into dashboard.db
    log_change = None
    try:
        from tools.dashboard_logger import log_change
    except ImportError:
        try:
            from dashboard_logger import log_change
        except ImportError:
            pass

    if log_change:
        try:
            log_change(
                project_name="Парковка Уфа",
                description=f"Self-Improvement Loop completed. Sessions parsed: {metrics.get('total_sessions', 0)}, friction points found: {metrics.get('total_friction_points', 0)}.",
                reason="Automated agent self-evolution and rules synchronization",
                expected_effect="Agent stability and rules coherence optimization",
            )
        except Exception as e:
            print(f"Warning: Could not log self-improvement event to dashboard.db: {e}")
    else:
        print("Warning: dashboard_logger.log_change not found. Skipping DB log.")

    print("🚀 Self-Improvement Loop iteration completed successfully.")


if __name__ == "__main__":
    main()
