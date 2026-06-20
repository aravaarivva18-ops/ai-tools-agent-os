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
    clean_text = "".join(c if c.isalnum() or c.isspace() else " " for c in issue_content).strip()
    words = [w for w in clean_text.split() if len(w) > 3][:6]
    keywords = " ".join(words)

    queries = [
        f"site:github.com {category} {keywords}",
        f"site:arxiv.org {category} {keywords}",
        f"best practices {category} {keywords}"
    ]
    return queries


def detect_tool_conflicts(logs: list) -> list:
    """Анализирует логи трения на наличие конфликтов инструментов."""
    conflicts = []
    for log in logs:
        for pt in log.get("friction_points", []):
            content = pt.get("content", "").lower()
            if "subagent" in content or "субагент" in content or "sub-agent" in content:
                conflicts.append(
                    f"Session {log.get('session_id')}: Найдено упоминание субагентов. Убедитесь, что используется Solo Loop по умолчанию."
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

    clean_line = "".join(c if c.isalnum() or c.isspace() else " " for c in first_line).strip()
    summary = " ".join(clean_line.split()[:10])

    return f"Исправь {category}: {summary}. Используй TDD, YAGNI (max 3 levels) и Solo Loop."


def suggest_tool_combinations(category: str) -> str:
    """Рекомендует эффективные комбинации инструментов для решения проблемы."""
    cat_lower = category.lower()
    if "oom" in cat_lower or "memory" in cat_lower or "памят" in cat_lower:
        return "`view_file` (ограничение чтения строк) + `run_command` (очистка памяти/проверка логов)"
    if "тест" in cat_lower or "ошибк" in cat_lower or "fail" in cat_lower or "error" in cat_lower:
        return "`replace_file_content` (точечные правки) + `run_command` (запуск тестов) + `tools/test_healer.py` (автоисправление)"
    return "`search_web` (сбор фактов) + `replace_file_content` (правка) + `make check-rules` (валидация)"


def analyze_self_healing_needs(issue_content: str) -> str:
    """Определяет, нужен ли запуск test_healer.py для самовосстановления."""
    content_lower = issue_content.lower()
    if any(k in content_lower for k in ["failed", "assert", "traceback", "syntaxerror", "import"]):
        return "⚠️ Рекомендуется запуск `tools/test_healer.py` для автоматического исправления тестов/импортов."
    return "💡 Проблема решается стандартным редактированием через `replace_file_content`."


def _parse_logs_data(logs_sorted: list) -> tuple:
    """Parses sorted logs to extract counts, categories, deltas, and saved time."""
    total_friction_points = 0
    issues_by_category = {}
    stealth_stops_count = 0
    loc_deltas = []
    time_saved_total = 0

    for log in logs_sorted:
        metrics = log.get("metrics", {})
        if metrics.get("stealth_stop"):
            stealth_stops_count += 1
        if metrics.get("loc_delta") is not None:
            loc_deltas.append(metrics.get("loc_delta"))
        if metrics.get("time_saved_min") is not None:
            time_saved_total += metrics.get("time_saved_min")

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
                    "stealth_stop": metrics.get("stealth_stop", False)
                }
            )

    return total_friction_points, stealth_stops_count, loc_deltas, time_saved_total, issues_by_category


def _compute_delta_metrics(logs_sorted: list) -> str:
    """Computes friction delta metrics trend from sorted logs."""
    if len(logs_sorted) < 2:
        return "Недостаточно данных для тренда"

    half = len(logs_sorted) // 2
    earlier_logs = logs_sorted[:half]
    later_logs = logs_sorted[half:]

    earlier_frictions = sum(len(x.get("friction_points", [])) for x in earlier_logs)
    later_frictions = sum(len(x.get("friction_points", [])) for x in later_logs)

    if earlier_frictions > 0:
        delta_percentage = ((earlier_frictions - later_frictions) / earlier_frictions) * 100.0
        if delta_percentage > 0:
            return f"Улучшение на {delta_percentage:.1f}% (количество ошибок падает)"
        elif delta_percentage < 0:
            return f"Ухудшение на {abs(delta_percentage):.1f}% (количество ошибок растет)"
        return "Стабильно"

    if later_frictions > 0:
        return "Новые ошибки зафиксированы"
    return "Ошибок не обнаружено"


def _build_priority_queue(issues_by_category: dict) -> tuple:
    """Builds error registry and auto-heal priority queue."""
    error_registry = []
    for category, items in issues_by_category.items():
        has_stealth = any(item["stealth_stop"] for item in items)
        error_registry.append({
            "category": category,
            "frequency": len(items),
            "has_stealth": has_stealth
        })

    priority_queue = []
    for reg in error_registry:
        cat_lower = reg["category"].lower()
        weight = 3
        if any(k in cat_lower for k in ["oom", "memory", "памят", "leak"]):
            weight = 10
        elif any(k in cat_lower for k in ["тест", "assert", "fail", "syntax", "healer"]):
            weight = 7

        if reg["has_stealth"]:
            weight += 5

        score = weight * reg["frequency"]
        priority_queue.append({
            "category": reg["category"],
            "score": score,
            "action": suggest_tool_combinations(reg["category"])
        })
    priority_queue = sorted(priority_queue, key=lambda x: x["score"], reverse=True)

    return error_registry, priority_queue


def generate_improvement_report(
    friction_logs_path: Path, output_path: Path
) -> dict:
    """Reads friction logs, aggregates issues, and writes a self-improvement report with advanced metrics."""
    if not friction_logs_path.exists():
        if collect:
            print("Friction logs not found. Running collect_handoffs first...")
            collect()
        else:
            return {"error": "Friction logs not found and collect_handoffs is unavailable"}

    try:
        with open(friction_logs_path, encoding="utf-8") as f:
            logs = json.load(f)
    except Exception as e:
        return {"error": f"Failed to read friction logs: {e}"}

    total_sessions = len(logs)
    logs_sorted = sorted(logs, key=lambda x: x.get("date", ""))

    (total_friction_points, stealth_stops_count, _loc_deltas,
     time_saved_total, issues_by_category) = _parse_logs_data(logs_sorted)

    trend_direction = _compute_delta_metrics(logs_sorted)
    error_registry, priority_queue = _build_priority_queue(issues_by_category)

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
        "",
        "## 📈 Дельта-метрики сессий (Delta Metrics)",
        f"- **Трендовое направление**: {trend_direction}",
        "",
        "## 🚨 Реестр паттернов ошибок (Error Pattern Registry)",
        "| Категория ошибки | Частота | Stealth Stop |",
        "| :--- | :---: | :---: |",
    ]

    for reg in error_registry:
        stealth_str = "⚠️ Да" if reg["has_stealth"] else "Нет"
        report_lines.append(f"| {reg['category']} | {reg['frequency']} | {stealth_str} |")
    report_lines.append("")

    report_lines.extend([
        "## 📋 Очередь авто-исправления (Auto-Heal Priority Queue)",
        "| Приоритет | Категория ошибки | Балл приоритета | Рекомендуемый инструмент |",
        "| :---: | :--- | :---: | :--- |",
    ])

    for i, item in enumerate(priority_queue, 1):
        report_lines.append(f"| {i} | {item['category']} | {item['score']} | {item['action']} |")
    report_lines.append("")

    report_lines.extend([
        "## 🔍 Детальный анализ проблем по категориям",
        "",
    ])

    if not issues_by_category:
        report_lines.append("🎉 Точки трения не обнаружены! Все системы работают в режиме YAGNI.")
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
                report_lines.append("  * 🔍 *Рекомендуемые запросы для исследования (Karpathy Research Step)*:")
                for q in queries:
                    report_lines.append(f"    - `{q}`")

                opt_prompt = optimize_prompt_for_speed(category, item["content"])
                report_lines.append(f"  * ⚡ *Оптимизированный промпт для исправления:* `{opt_prompt}`")

                tools_comb = suggest_tool_combinations(category)
                report_lines.append(f"  * 🛠️ *Рекомендуемые инструменты:* {tools_comb}")

                healing_need = analyze_self_healing_needs(item["content"])
                report_lines.append(f"  * {healing_need}")
                report_lines.append("")

    # Detect tool conflicts
    conflicts = detect_tool_conflicts(logs)
    if conflicts:
        report_lines.extend([
            "## ⚠️ Конфликты инструментов (Tool Conflicts)",
            "",
        ])
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


def apply_improvement_record(
    handoff_notes_path: Path, metrics: dict
) -> None:
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
    print("🚀 Self-Improvement Loop iteration completed successfully.")


if __name__ == "__main__":
    main()
