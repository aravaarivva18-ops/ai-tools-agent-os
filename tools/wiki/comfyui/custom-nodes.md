# 🛠️ Разработка Custom Nodes для ComfyUI

Кастомные ноды (Custom Nodes) расширяют стандартный функционал ComfyUI, добавляя поддержку новых моделей, методов обработки изображений, видео или текста.

---

## 📁 1. Структура проекта и шаблонизация

Для создания новой ноды рекомендуется использовать встроенный в `comfy-cli` генератор шаблонов:

```bash
cd ComfyUI/custom_nodes
comfy node scaffold
```
CLI задаст несколько вопросов (имя автора, название ноды, лицензия) и сгенерирует готовую структуру файлов.

### Минимальная структура директории ноды:
```text
my-custom-node/
├── __init__.py           # Экспорт нод для реестра ComfyUI
├── my_node.py            # Логика выполнения на Python
└── js/                   # (Опционально) JavaScript-код для кастомизации UI
```

---

## 🧬 2. Анатомия Python-класса ноды

Каждая нода в ComfyUI представляет собой класс Python, который должен соответствовать определенному контракту.

### Ключевые атрибуты класса:

1.  **`INPUT_TYPES` (класс-метод):**
    Определяет входные параметры, типы данных (IMAGE, MASK, LATENT, MODEL, CLIP, VAE, STRING, INT, FLOAT) и их значения по умолчанию.
    Параметры делятся на `required` (обязательные) и `optional` (необязательные).

2.  **`RETURN_TYPES` (кортеж):**
    Определяет возвращаемые типы данных.

3.  **`RETURN_NAMES` (кортеж, опционально):**
    Человекочитаемые названия выходных коннекторов на плашке ноды.

4.  **`FUNCTION` (строка):**
    Имя метода класса, который вызывается при выполнении ноды.

5.  **`CATEGORY` (строка):**
    Раздел в контекстном меню добавления нод, где будет отображаться данная нода.

---

## 📝 3. Пример кода кастомной ноды

Ниже приведен пример реализации простой ноды, принимающей строку и выводящей её с префиксом:

### Код модуля `my_node.py`:
```python
class TextPrefixNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
                "prefix": ("STRING", {"default": "Prefix: "}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("modified_text",)
    FUNCTION = "apply_prefix"
    CATEGORY = "Example/Text"

    def apply_prefix(self, text: str, prefix: str) -> tuple[str]:
        # Логика работы ноды
        new_text = f"{prefix}{text}"
        return (new_text,)
```

### Код файла инициализации `__init__.py`:
Чтобы ComfyUI распознал ваши ноды, экспортируйте их через словари `NODE_CLASS_MAPPINGS` и `NODE_DISPLAY_NAME_MAPPINGS` в `__init__.py`:

```python
from .my_node import TextPrefixNode

NODE_CLASS_MAPPINGS = {
    "TextPrefixNode": TextPrefixNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextPrefixNode": "✍️ Text Prefix Addon"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
```

---

## 🎨 4. Взаимодействие Frontend и Backend

*   **Backend (Python):** Отвечает за вычисления, работу с PyTorch, инференс нейросетей, сохранение и загрузку файлов.
*   **Frontend (JavaScript):** Рисует интерфейс в браузере, управляет подключением нод друг к другу и отображает превью (изображения, текст) на плашках. Скрипты помещаются в папку `js/` кастомной ноды и автоматически загружаются веб-клиентом ComfyUI.
