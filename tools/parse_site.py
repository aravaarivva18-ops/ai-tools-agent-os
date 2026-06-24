#!/usr/bin/env python3
import re

from selectolax.lexbor import LexborHTMLParser


def main():
    file_path = "/Users/rus/.gemini/antigravity-cli/brain/b9246f7a-f837-41b3-bc8f-33a42a774453/.system_generated/steps/869/content.md"
    try:
        with open(file_path, encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    parser = LexborHTMLParser(html)

    # 1. Извлекаем контакты (телефоны, почты)
    text = (
        parser.css_first("body").text(separator=" ")
        if parser.css_first("body")
        else html
    )

    phones = set(
        re.findall(r"\+?[78]\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}", text)
    )
    emails = set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text))

    print("--- КОНТАКТЫ НА САЙТЕ ---")
    print("Телефоны:")
    for p in phones:
        print(f"  {p}")
    print("Email:")
    for e in emails:
        print(f"  {e}")

    # 2. Ищем ссылки на мессенджеры и соцсети
    print("\n--- ССЫЛКИ НА СОЦСЕТИ И МЕССЕНДЖЕРЫ ---")
    for a in parser.css("a[href]"):
        href = a.attributes.get("href", "")
        if (
            "wa.me" in href
            or "whatsapp" in href
            or "t.me" in href
            or "telegram" in href
            or "vk.com" in href
        ):
            print(f"  {a.text().strip()} -> {href}")

    # 3. Заголовки сайта (H1, H2)
    print("\n--- СТРУКТУРА САЙТА (ЗАГОЛОВКИ) ---")
    for h in parser.css("h1, h2"):
        print(f"  {h.tag.upper()}: {h.text().strip()}")


if __name__ == "__main__":
    main()
