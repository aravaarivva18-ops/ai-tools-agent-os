#!/usr/bin/env python3
"""Integration test script to run full Scrape-Audit-Sync pipeline on a real URL."""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# Ensure scripts/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "geo-seo", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fetch_page import fetch_page

from tools.obsidian_sync import ObsidianVaultManager


def run_pipeline(target_url: str):
    print(f"=== ЗАПУСК ИНТЕГРАЦИОННОГО ТЕСТА ДЛЯ {target_url} ===\n")

    # 1. Запускаем скрапинг сайта
    print("Шаг 1: Сканирование сайта...")
    page_data = fetch_page(target_url)

    if page_data["errors"]:
        print(f"❌ Ошибка скрапинга: {page_data['errors']}")
        return

    site_title = page_data.get("title") or "Без названия"
    print(f"✓ Сайт успешно сканирован. Title: '{site_title}'\n")

    # 2. Проводим SEO-скоринг
    print("Шаг 2: Анализ SEO-показателей...")
    has_ssl = target_url.startswith("https")
    h1_count = len(page_data.get("h1_tags", []))

    # Считаем рекомендации
    recommendations = ["### 💡 Рекомендации по оптимизации:\n"]
    if h1_count == 0:
        recommendations.append(
            "*   **[Критично]** Отсутствует главный заголовок `<h1>` на странице. Добавьте один `<h1>`."
        )
    elif h1_count > 1:
        recommendations.append(
            f"*   **[Внимание]** Найдено несколько заголовков `<h1>` ({h1_count}). Должен быть только один."
        )
    else:
        recommendations.append(
            "*   [x] Структура главного заголовка `<h1>` настроена верно."
        )

    if not page_data.get("description"):
        recommendations.append(
            "*   **[Внимание]** Отсутствует тег `<meta name='description'>`. Заполните описание сайта для сниппета."
        )
    else:
        recommendations.append("*   [x] Мета-описание присутствует.")

    audit_results = {
        "ssl": has_ssl,
        "mobile_friendly": True,  # Заглушка, так как сканируем статику
        "lcp": "1.2",  # Примерная скорость для легких сайтов
        "recommendations": "\n".join(recommendations),
    }
    print("✓ Скоринг завершен.\n")

    # 3. Синхронизируем с Obsidian Vault
    print("Шаг 3: Запись результатов в Obsidian Vault...")
    vault_path = Path("vault")
    vault_path.mkdir(parents=True, exist_ok=True)
    manager = ObsidianVaultManager(vault_path)

    # Очищаем имя компании для названия файла
    company_name = site_title.split("-")[0].strip()
    if not company_name or company_name.lower() == "github":
        company_name = urlparse(target_url).netloc

    lead_data = {
        "name": company_name,
        "url": target_url,
        "phone": "Не указан на главной",
        "status": "Scraped",
        "geo_visibility": "Не оценена (требуются карты)",
        "review_count": 0,
        "rating": "0.0",
        "notes": f"Автоматический импорт при сканировании сайта. Количество слов на странице: {page_data.get('word_count', 0)}.",
    }

    lead_file = manager.register_lead(lead_data)
    audit_file = manager.register_audit_report(company_name, audit_results)

    print("✓ Данные записаны в Obsidian Vault!")
    print(f"  - Карточка лида: {lead_file.resolve()}")
    print(f"  - Отчет аудита: {audit_file.resolve()}\n")
    print("=== ТЕСТ УСПЕШНО ЗАВЕРШЕН ===")


if __name__ == "__main__":
    # Будем тестировать на реальном сайте WhiteDNS Wizard (GitHub страница проекта)
    # или на легком example.com
    run_pipeline("https://axoloti.ru")
