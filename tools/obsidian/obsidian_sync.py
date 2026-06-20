"""Module to synchronize scraper results and audits directly into Obsidian Vault."""

import os
import re
from pathlib import Path
from typing import Any


class ObsidianVaultManager:
    """Manages creation, linking, and structure of markdown files in Obsidian Vault."""

    def __init__(self, vault_path: str | os.PathLike[str]) -> None:
        self.vault_path = Path(vault_path)

    def _sanitize_filename(self, filename: str) -> str:
        """Removes characters that are forbidden in Obsidian filenames."""
        return re.sub(r'[\\/:*?"<>|#^]', "", filename).strip()

    def create_note(
        self, folder_name: str, title: str, content: str, tags: list[str] | None = None
    ) -> Path:
        """Creates a markdown note inside the specified vault folder."""
        # Ensure target folder exists
        target_dir = self.vault_path / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_title = self._sanitize_filename(title)
        filepath = target_dir / f"{safe_title}.md"

        # Construct metadata header (YAML frontmatter)
        metadata = ["---"]
        metadata.append(f"title: {title}")
        metadata.append(
            f"created: {Path(filepath).stat().st_ctime if filepath.exists() else 'now'}"
        )
        if tags:
            metadata.append("tags:")
            for tag in tags:
                metadata.append(f"  - {tag}")
        metadata.append("---\n")

        full_content = "\n".join(metadata) + content

        # Write file with UTF-8 encoding
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)

        return filepath

    def link_notes(self, source_path: Path, target_title: str) -> None:
        """Appends a markdown link [[target_title]] to the source note."""
        if not source_path.exists():
            return

        with open(source_path, "a", encoding="utf-8") as f:
            f.write(f"\n\nСвязанная информация: [[{target_title}]]\n")

    def register_lead(self, lead_data: dict[str, Any]) -> Path:
        """Generates a structured Obsidian note for a sales/SEO lead."""
        name = lead_data.get("name", "Unknown Lead")
        url = lead_data.get("url", "No URL")
        phone = lead_data.get("phone", "No Phone")
        status = lead_data.get("status", "New")

        content = f"""# Карточка Лида: {name}

## 📞 Контактные данные
*   **Сайт:** [{url}]({url})
*   **Телефон:** {phone}
*   **Текущий статус:** `{status}`

## 🔍 SEO показатели (GEO)
*   **Индекс видимости на картах:** {lead_data.get("geo_visibility", "Не сканировался")}
*   **Количество отзывов:** {lead_data.get("review_count", 0)}
*   **Средняя оценка:** {lead_data.get("rating", "0.0")}

## 📝 Заметки ассистента
{lead_data.get("notes", "Заметки отсутствуют.")}
"""
        return self.create_note(
            folder_name="Leads",
            title=name,
            content=content,
            tags=["lead", f"status/{status.lower()}"],
        )

    def register_audit_report(
        self, lead_name: str, audit_results: dict[str, Any]
    ) -> Path:
        """Generates an SEO/Technical audit note and links it back to the Lead."""
        title = f"Аудит - {lead_name}"

        content = f"""# Отчет по аудиту: {lead_name}

## 🛠️ Выявленные технические ошибки
*   **SSL/HTTPS:** {"[x] Настроен" if audit_results.get("ssl") else "[ ] Отсутствует SSL-сертификат"}
*   **Мобильная верстка:** {"[x] Оптимизирован под мобильные" if audit_results.get("mobile_friendly") else "[ ] Проблемы с адаптивностью"}
*   **Скорость загрузки (LCP):** {audit_results.get("lcp", "Неизвестно")} сек.

## 📈 SEO Оценки и Рекомендации
{audit_results.get("recommendations", "Рекомендации не сформированы.")}
"""
        report_path = self.create_note(
            folder_name="Audits",
            title=title,
            content=content,
            tags=["audit", "seo"],
        )

        # Create bidirectional link: link Audit back to Lead
        self.link_notes(report_path, lead_name)

        # Also link Lead back to Audit
        lead_path = (
            self.vault_path / "Leads" / f"{self._sanitize_filename(lead_name)}.md"
        )
        self.link_notes(lead_path, title)

        return report_path
