#!/usr/bin/env python3
from selectolax.lexbor import LexborHTMLParser


def main():
    file_path = "/Users/rus/.gemini/antigravity-cli/brain/b9246f7a-f837-41b3-bc8f-33a42a774453/.system_generated/steps/855/content.md"
    try:
        with open(file_path, encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    parser = LexborHTMLParser(html)

    # Попробуем найти описание по разным селекторам hh.ru
    desc_node = parser.css_first("[data-qa='vacancy-description']")
    if not desc_node:
        desc_node = parser.css_first(".g-user-content")

    if desc_node:
        print("--- ВАКАНСИЯ: ОПИСАНИЕ ---")
        print(desc_node.text(separator="\n").strip())
    else:
        print("Описание вакансии не найдено через стандартные селекторы.")
        # Выведем хотя бы заголовки H1-H3 для ориентира
        for h in parser.css("h1, h2, h3"):
            print(f"{h.tag}: {h.text().strip()}")

        # Попробуем вывести текстовое содержимое body
        body = parser.css_first("body")
        if body:
            print("\n--- Выдержка из body ---")
            text = body.text(separator=" ")
            # Ищем ключевые слова вокруг "Кирпич"
            idx = text.find("Кирпич")
            if idx != -1:
                start = max(0, idx - 500)
                end = min(len(text), idx + 2000)
                print(text[start:end])

if __name__ == "__main__":
    main()
