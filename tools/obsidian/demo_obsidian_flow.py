#!/usr/bin/env python3
"""Demo script showing full cycle: Scrape, Convert, Audit and Sync to Obsidian Vault."""

import os
import sys
from pathlib import Path

# Ensure worktree is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.obsidian_sync import ObsidianVaultManager


def run_demo():
    # Detect vault path (fallback to local project directory)
    vault_path_str = os.environ.get("OBSIDIAN_VAULT_PATH", "vault")
    vault_path = Path(vault_path_str)

    # Ensure vault root folder exists
    vault_path.mkdir(parents=True, exist_ok=True)

    print(f"Инициализация Obsidian Vault по пути: {vault_path.resolve()}")
    manager = ObsidianVaultManager(vault_path)

    # 1. Симулируем получение данных лида (например, спарсили с карт)
    lead_name = "Стоматология Зубной Стандарт"
    lead_data = {
        "name": lead_name,
        "url": "https://zubnoy-standart.ru",
        "phone": "+7 (495) 123-45-67",
        "status": "New",
        "geo_visibility": "68%",
        "review_count": 142,
        "rating": "4.7",
        "notes": "Карточка на картах заполнена хорошо, но есть проблемы с мобильной версией сайта.",
    }

    print(f"Создаем карточку лида: {lead_name}...")
    lead_file = manager.register_lead(lead_data)
    print(f"Успешно создано: {lead_file.relative_to(vault_path.parent)}")

    # 2. Симулируем проведение технического SEO-аудита
    audit_results = {
        "ssl": True,
        "mobile_friendly": False,
        "lcp": "4.2",  # Медленная загрузка
        "recommendations": """### 💡 Рекомендации по оптимизации:
1. **Ускорить LCP (4.2 сек):** Оптимизировать тяжелые изображения на главном экране (конвертировать баннеры в WebP/AVIF).
2. **Исправить мобильную верстку:** Элементы меню перекрывают текст на экранах шириной 320px. Области клика кнопок в шапке меньше 44px.
3. **Оптимизация карт:** Добавить ключевое слово "стоматология на карте" в описание профиля на Яндекс.Картах для повышения ранжирования.
""",
    }

    print("Создаем отчет по аудиту и связываем с лидом...")
    audit_file = manager.register_audit_report(lead_name, audit_results)
    print(f"Успешно создано: {audit_file.relative_to(vault_path.parent)}")

    print("\n✅ Демо-данные успешно синхронизированы!")
    print("Откройте папку 'ai-tools/vault' в Obsidian, чтобы увидеть граф связей!")


if __name__ == "__main__":
    run_demo()
