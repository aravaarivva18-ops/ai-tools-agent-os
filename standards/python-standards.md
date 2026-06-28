# Глобальный стандарт: Разработка на Python (macOS / Python 3.14+)

Этот стандарт обязателен для выполнения всеми ИИ-агентами при написании и рефакторинге Python-кода в локальном окружении.

---

## 🛡️ 1. Безопасность вызова процессов (Subprocess & Bandit)
Для предотвращения уязвимостей выполнения команд (правила B603, B607 в линтере Bandit):
*   **Абсолютные пути:** Всегда определяйте абсолютный путь исполняемой команды с помощью `shutil.which()`.
*   **Аннотация отключения предупреждений:** Добавляйте комментарий `# nosec B603` в строках вызова `subprocess.run` или `subprocess.Popen`.

*Пример корректного кода:*
```python
import subprocess
import shutil

# 1. Находим абсолютный путь к утилите
ffmpeg_path = shutil.which("ffmpeg")
if not ffmpeg_path:
    raise FileNotFoundError("FFmpeg не найден в системе")

# 2. Вызываем процесс с аннотацией
result = subprocess.run(
    [ffmpeg_path, "-i", "input.mp4", "output.mp3"],
    capture_output=True,
    text=True,
    check=True
)  # nosec B603
```

---

## ⚡️ 2. Оптимизация генераторов (Ruff RUF015)
Запрещено преобразовывать весь генератор или итератор в список только для того, чтобы взять первый элемент. Это неэффективно расходует память.

*   *Плохо:* `first_item = list(my_generator)[0]`
*   *Хорошо:* `first_item = next(iter(my_generator))`

---

## 📦 3. Различие имен импортов и pip-пакетов
Никогда не предполагайте, что имя пакета при установке через `pip` совпадает с именем модуля в `import`. 

*Список известных расхождений:*
*   `pip install stable-ts` ──► `import stable_whisper`
*   `pip install pyyaml` ──► `import yaml`
*   `pip install pillow` ──► `import PIL`
*   `pip install scikit-learn` ──► `import sklearn`
*   `pip install opencv-python` ──► `import cv2`
*   `pip install beautifulsoup4` ──► `import bs4`

---

## 🎙️ 4. Локальный TTS (Синтез речи) на macOS (Python 3.14+)
*   Из-за несовместимости библиотеки `spacy/blis` на Python 3.14+ под macOS библиотека `kokoro` падает при сборке.
*   **Решение:** Для локального синтеза речи (TTS) всегда используйте **`piper-tts`** и готовые модели Nabu Casa (загружаемые с Hugging Face).
