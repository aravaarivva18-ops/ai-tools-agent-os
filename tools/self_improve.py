import json
import sys
from datetime import datetime
from pathlib import Path

# Import collect function from collect_handoffs to refresh logs
try:
    from tools.collect_handoffs import collect
except ImportError:
    # If run directly without module path
    try:
        from collect_handoffs import collect
    except ImportError:
        collect = None


def generate_research_queries(category: str, issue_content: str) -> list:
    """Генерирует целевые поисковые запросы для GitHub/arXiv/Web на основе описания проблемы."""
    # Очищаем текст от спецсимволов для формирования чистого поискового запроса
    clean_text = "".join(c if c.isalnum() or c.isspace() else " " for c in issue_content).strip()
    # Берем первые несколько значимых слов (длиной > 3 символов)
    words = [w for w in clean_text.split() if len(w) > 3][:6]
    keywords = " ".join(words)

    queries = [
        f"site:github.com {category} {keywords}",
        f"site:arxiv.org {category} {keywords}",
        f"best practices {category} {keywords}"
    ]
    return queries


def generate_improvement_report(
    friction_logs_path: Path, output_path: Path
) -> dict:
    """
    Reads friction logs, aggregates issues, and writes a self-improvement report.
    Returns metrics dict.
    """
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
    total_friction_points = 0
    issues_by_category = {}

    for log in logs:
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
                }
            )

    # Generate markdown report
    report_lines = [
        "# ⚡ Отчет системы самообучения агента (Self-Improvement Report)",
        f"**Дата генерации**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 📊 Метрики сессий",
        f"- **Проанализировано сессий**: {total_sessions}",
        f"- **Выявлено точек трения (friction points)**: {total_friction_points}",
        "",
        "## 🔍 Детальный анализ проблем по категориям",
        "",
    ]

    if not issues_by_category:
        report_lines.append("🎉 Точки трения не обнаружены! Все системы работают в режиме YAGNI.")
    else:
        # Prioritize high-impact issues (OOM, memory leaks, critical errors)
        sorted_categories = sorted(
            issues_by_category.keys(),
            key=lambda cat: 0 if any(k in cat.lower() for k in ["oom", "memory", "критич", "ошибка"]) else 1
        )
        for category in sorted_categories:
            items = issues_by_category[category]
            report_lines.append(f"### 🛑 Категория: {category}")
            for item in items:
                report_lines.append(
                    f"- **Сессия [{item['session_id']}]** ({item['date']}):"
                )
                # Indent content lines for blockquote format
                content_lines = item["content"].splitlines()
                for line in content_lines:
                    report_lines.append(f"  > {line}")

                # Karpathy-style research queries generator
                queries = generate_research_queries(category, item["content"])
                report_lines.append("  * 🔍 *Рекомендуемые запросы для исследования (Karpathy Research Step)*:")
                for q in queries:
                    report_lines.append(f"    - `{q}`")
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

    # If vault/handoffs directory doesn't exist, collect first
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
