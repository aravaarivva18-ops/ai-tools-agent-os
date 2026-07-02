import os
import re

try:
    from tools.config import get_workspace_root
except ImportError:
    from config import get_workspace_root

html_file = os.path.join(get_workspace_root(), "vault", "raw_playerok.html")

with open(html_file, encoding="utf-8") as f:
    content = f.read()

print("HTML length:", len(content))

# Ищем любые вхождения слов на русском языке
russian_words = re.findall(r"[А-Яа-яЁё]{4,}", content)
print("Total Russian words found:", len(russian_words))
print("First 50 Russian words:", russian_words[:50])

# Ищем слово Gemini
gemini_indices = [m.start() for m in re.finditer(r"gemini", content, re.IGNORECASE)]
print("Gemini occurrences:", len(gemini_indices))
for idx in gemini_indices:
    # Печатаем контекст вокруг вхождения
    print(
        f"Context at {idx}: {content[max(0, idx - 100) : min(len(content), idx + 100)]!r}"
    )
