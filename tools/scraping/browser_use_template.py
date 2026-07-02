#!/usr/bin/env python3
"""
Шаблон ИИ-агента для автоматизации браузера с помощью browser-use.
Адаптирован под стек Google Gemini (используется ChatGoogleGenAI).
Позволяет давать ИИ текстовые команды (например, "авторизуйся на сайте X и скачай отчет Y"),
которые ИИ выполняет, анализируя интерфейс страницы (Vision).
"""

import asyncio
import os

from dotenv import load_dotenv

# Загружаем переменные окружения (.env)
load_dotenv()

try:
    from browser_use import Agent
    from langchain_google_genai import ChatGoogleGenAI
except ImportError:
    print("❌ Ошибка: библиотеки 'browser-use' или 'langchain-google-genai' не установлены.")
    print("Запустите: uv sync --all-packages")
    import sys
    sys.exit(1)

async def run_ai_browser_task(task_description: str, headless: bool = True):
    """
    Запускает ИИ-агента для выполнения задачи в браузере.
    
    Args:
        task_description (str): Описание задачи для ИИ (например, "Зайди на avito.ru и...")
        headless (bool): Запускать ли браузер в фоновом режиме (без вывода окна)
    """
    # Инициализируем модель Gemini (требуется GEMINI_API_KEY в .env)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ Предупреждение: GEMINI_API_KEY не найден в переменных окружения.")
        print("Пожалуйста, добавьте его в файл .env в корне проекта.")
        return None

    # Используем gemini-2.0-flash — идеальный выбор по скорости, цене и Vision для браузера
    llm = ChatGoogleGenAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0.0
    )

    print(f"🚀 Запуск ИИ-агента с задачей: '{task_description}'...")

    # Создаем агента
    agent = Agent(
        task=task_description,
        llm=llm,
    )

    # Запускаем выполнение
    try:
        history = await agent.run()
        print("\n✅ Выполнение успешно завершено!")

        # Получаем финальный результат
        final_result = history.final_result()
        print(f"📊 Финальный ответ ИИ:\n{final_result}")
        return final_result
    except Exception as e:
        print(f"❌ Произошла ошибка во время выполнения агента: {e}")
        return None

if __name__ == "__main__":
    # Пример простой тестовой задачи
    test_task = (
        "Зайди на google.com, найди погоду в Москве на сегодня, "
        "сделай скриншот первой страницы результатов поиска и верни мне температуру."
    )

    # Запуск асинхронного цикла
    asyncio.run(run_ai_browser_task(test_task, headless=False))
