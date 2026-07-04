#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load workspace env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / "ai-sales" / ".env")

def analyze_competitors(company: str, industry: str, competitors_list: list[str] = None) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("API-ключ Gemini не найден. Пожалуйста, укажите GEMINI_API_KEY в файле .env.")

    import google.generativeai as genai
    genai.configure(api_key=api_key)

    # We use gemini-1.5-flash
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Step 1: Identify competitors if not provided
    if not competitors_list:
        prompt_identify = f"Перечисли ровно 3 главных конкурента для компании '{company}' в сфере '{industry}'. Выведи их только в виде списка через запятую. Никакого другого текста."
        response = model.generate_content(prompt_identify)
        competitors_list = [c.strip() for c in response.text.split(",") if c.strip()]

    competitors_str = ", ".join(competitors_list)

    # Step 2: Generate the final strategic report
    prompt_report = f"""Ты опытный стратегический бизнес-консультант.
Проведи конкурентный анализ для компании '{company}' в сфере '{industry}'.
Основные конкуренты: {competitors_str}.

Подготовь отчет, содержащий следующие разделы:
1. **Обзор конкурентной среды**: Краткое описание текущего состояния рынка (3 предложения).
2. **SWOT-анализ конкурентов**: Для каждого конкурента ({competitors_str}) укажи:
   - Сильные стороны (2)
   - Слабые стороны (2)
   - Способ позиционирования/ценообразование
3. **Карта рыночных окон (Gaps & Opportunities)**: Выяви 3 незанятые ниши или возможности на рынке.
4. **Стратегические рекомендации для '{company}'**: Сформулируй 5 конкретных шагов для укрепления позиций на рынке.
"""
    response_report = model.generate_content(prompt_report)
    return response_report.text.strip()

def main():
    parser = argparse.ArgumentParser(description="Competitive Analysis Agent")
    parser.add_argument("--company", required=True, help="Имя вашей компании")
    parser.add_argument("--industry", required=True, help="Отрасль/сфера деятельности")
    parser.add_argument("--competitors", default="", help="Список конкурентов через запятую (опционально)")
    args = parser.parse_args()

    competitors_list = [c.strip() for c in args.competitors.split(",") if c.strip()] if args.competitors else None

    print(f"🔍 Запуск конкурентного анализа для: {args.company}")
    print(f"🏭 Отрасль: {args.industry}")
    if competitors_list:
        print(f"👥 Указанные конкуренты: {', '.join(competitors_list)}")
    print("-" * 60)

    try:
        report = analyze_competitors(args.company, args.industry, competitors_list)
        print("\n📊 СТРАТЕГИЧЕСКИЙ ОТЧЕТ")
        print("=" * 60)
        print(report)
        print("=" * 60)
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
