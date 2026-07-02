import json
import os
import re


class SEOOptimizer:
    def __init__(self, database_path=None):
        self.database_path = (
            database_path
            or "/Users/rus/ai-tools/youtube-faceless-pipeline/output/generated_scripts_db.json"
        )
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        if not os.path.exists(self.database_path):
            with open(self.database_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def check_similarity(self, new_text: str) -> float:
        """
        Вычисляет максимальное сходство по коэффициенту Жаккара с ранее сгенерированными сценариями.
        Позволяет избежать duplicate content на YouTube.
        """
        # Очищаем и токенизируем новый текст
        new_words = set(re.findall(r"\w+", new_text.lower()))
        if not new_words:
            return 0.0

        try:
            with open(self.database_path, encoding="utf-8") as f:
                past_scripts = json.load(f)
        except Exception:
            past_scripts = []

        max_similarity = 0.0
        for script_text in past_scripts:
            past_words = set(re.findall(r"\w+", script_text.lower()))
            if not past_words:
                continue

            intersection = new_words.intersection(past_words)
            union = new_words.union(past_words)
            similarity = len(intersection) / len(union)
            if similarity > max_similarity:
                max_similarity = similarity

        return max_similarity

    def save_to_database(self, text: str):
        """Сохраняет сгенерированный текст в локальную базу данных."""
        try:
            with open(self.database_path, encoding="utf-8") as f:
                past_scripts = json.load(f)
        except Exception:
            past_scripts = []

        past_scripts.append(text)

        with open(self.database_path, "w", encoding="utf-8") as f:
            json.dump(past_scripts, f, ensure_ascii=False, indent=2)

    def optimize_metadata(self, raw_script: dict) -> dict:
        """
        Оптимизирует заголовок, описание и теги под алгоритмы YouTube Shorts/Videos.
        Добавляет кликабельные элементы и хэштеги.
        """
        raw_title = raw_script.get("title", "Untitled Video")

        # Очищаем тему
        clean_title = raw_title.replace("The Future of ", "").replace("Future of ", "")

        # Парсим русские подтемы для таргетированных A/B тестов
        ru_match = re.search(r"([А-Яа-я\s:,?!\-\"0-9]+)", raw_title)
        if ru_match and len(ru_match.group(1).strip()) > 5:
            topic_ru = ru_match.group(1).strip()
            topic_ru = re.sub(r"^:\s*", "", topic_ru)
            optimized_title_a = f"ИИ Агенты 2026: {topic_ru}"
            optimized_title_b = "ИИ ведет бизнес БЕЗ человека в 2026? 😱"
        else:
            optimized_title_a = f"Autonomous AI Agents: {clean_title} 🚀"
            optimized_title_b = "Can AI Run Your Business? Agents in 2026 😱"

        if len(optimized_title_a) > 60:
            optimized_title_a = optimized_title_a[:57] + "..."
        if len(optimized_title_b) > 60:
            optimized_title_b = optimized_title_b[:57] + "..."

        # 2. Создание оптимизированного описания
        # YouTube ценит первые 2 строки описания. Они должны содержать ключевые слова.
        description_lines = [
            f"🔥 {optimized_title_a} — This is how Autonomous AI Agents will change everything in 2026!",
            "Discover the latest artificial intelligence trends and workflows.",
            "",
            "📌 TIMESTAMPS:",
            "0:00 - Introduction",
            "0:15 - Key Trends of 2026",
            "0:45 - Wrap up & Subscribe",
            "",
            "📱 FOLLOW US ON SOCIALS:",
            "Instagram: @AIFacelessShorts",
            "TikTok: @AIFacelessStudio",
            "",
            "#AI #ArtificialIntelligence #Technology #Shorts #Productivity #TechTrends",
        ]
        optimized_description = "\n".join(description_lines)

        # 3. Оптимизация тегов
        tags = raw_script.get("tags", [])
        seo_tags = list(
            {
                *tags,
                "ai agents",
                "autonomous agents",
                "tech 2026",
                "ai workflows",
                "ai shorts",
                "productivity tips",
            }
        )

        return {
            "title": optimized_title_a,
            "title_a": optimized_title_a,
            "title_b": optimized_title_b,
            "description": optimized_description,
            "tags": seo_tags,
        }

    def generate_thumbnail_prompt(self, title: str) -> str:
        """
        Генерирует промпт для яркой, высококликабельной обложки (Thumbnail).
        Использует правила высокого CTR: контрастность, крупный фокусный объект.
        """
        return (
            f"High CTR YouTube thumbnail design for '{title}'. "
            f"Featuring a giant glowing transparent futuristic holographic robot head brain, "
            f"vibrant neon purple and electric cyan lighting, dark cyberspace grid background. "
            f"Hyperrealistic, cinematic render, unreal engine 5, 8k resolution, text-free, highly contrast."
        )
