#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load workspace env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / "ai-sales" / ".env")

def generate_posts(topic: str, brand: str = "", platforms: list[str] = None) -> dict[str, str]:
    if not platforms:
        platforms = ["telegram", "linkedin", "twitter"]

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("API-ключ Gemini не найден. Пожалуйста, укажите GEMINI_API_KEY в файле .env.")

    import google.generativeai as genai
    genai.configure(api_key=api_key)

    # We use gemini-1.5-flash for general fast generation
    model = genai.GenerativeModel("gemini-1.5-flash")

    results = {}
    brand_text = f" для бренда '{brand}'" if brand else ""

    for platform in platforms:
        p_name = platform.strip().lower()

        prompt = f"""Ты профессиональный SMM-копирайтер. Напиши вовлекающий пост на тему: '{topic}'{brand_text}.
Адаптируй формат под платформу {p_name.upper()}:
"""
        if p_name == "telegram":
            prompt += "- Добавь яркий цепляющий заголовок.\n- Используй эмодзи для структуры.\n- Напиши структурированный, легко читаемый текст.\n- В конце добавь призыв к действию и 3-5 хэштегов."
        elif p_name == "linkedin":
            prompt += "- Тон профессиональный, экспертный.\n- Используй формат storytelling (история из практики/опыт).\n- Разделяй абзацы пустой строкой.\n- Добавь 3 профессиональных хэштега в конце."
        elif p_name == "twitter" or p_name == "x":
            prompt += "- Напиши 2 варианта коротких твитов (каждый строго до 280 символов).\n- Стиль лаконичный, емкий, вирусный.\n- Добавь по 1-2 хэштега к каждому."
        else:
            prompt += "- Напиши стандартный пост для соцсети (150-200 слов) с абзацами и хэштегами."

        response = model.generate_content(prompt)
        results[p_name] = response.text.strip()

    return results

def main():
    parser = argparse.ArgumentParser(description="Social Media Content Generator Agent")
    parser.add_argument("--topic", required=True, help="Тема или описание контента")
    parser.add_argument("--brand", default="", help="Имя бренда (опционально)")
    parser.add_argument("--platforms", default="telegram,linkedin,twitter", help="Список платформ через запятую")
    args = parser.parse_args()

    platforms_list = [p.strip() for p in args.platforms.split(",")]

    print(f"📱 Генерация контента для платформ: {', '.join(platforms_list)}")
    print(f"📌 Тема: {args.topic}")
    if args.brand:
        print(f"🏢 Бренд: {args.brand}")
    print("-" * 60)

    try:
        posts = generate_posts(args.topic, args.brand, platforms_list)
        for platform, text in posts.items():
            print(f"\n✍️  ПОСТ ДЛЯ {platform.upper()}:")
            print("=" * 60)
            print(text)
            print("=" * 60)
    except Exception as e:
        print(f"❌ Ошибка генерации: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
