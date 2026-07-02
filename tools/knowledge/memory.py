"""
Модуль для работы с памятью Obsidian (HANDOFF.md).
Содержит тонкий ленивый фасад для гибридного поиска с recency scoring.
"""

import math
import time


def dot_product(v1, v2) -> float:
    return sum(x * y for x, y in zip(v1, v2))


def magnitude(v) -> float:
    return math.sqrt(sum(x * x for x in v))


def cosine_similarity(v1, v2) -> float:
    mag1 = magnitude(v1)
    mag2 = magnitude(v2)
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product(v1, v2) / (mag1 * mag2)


def search_memory(query: str, limit: int = 3, semantic: bool = False) -> str:
    """
    Ищет релевантные хандоффы в памяти Obsidian с учетом recency scoring.
    """
    from tools.obsidian.semantic_search import load_index, text_search

    index = load_index()
    if not index:
        return "Индекс памяти Obsidian пуст."

    results = []
    current_time = time.time()

    if not semantic:
        # Быстрый текстовый поиск
        text_results = text_search(query, index, limit=10)
        for rel_path, text_score, content in text_results:
            mtime = index[rel_path].get("mtime", current_time)
            # Recency factor: затухание от возраста в днях
            age_days = (current_time - mtime) / (24 * 3600)
            recency_multiplier = math.exp(-age_days / 30.0)  # характерное время 30 дней

            final_score = text_score * (0.5 + 0.5 * recency_multiplier)
            results.append((rel_path, final_score, content))
    else:
        # Семантический (векторный) поиск
        try:
            from tools.obsidian.semantic_search import load_model
            model = load_model()
            raw_vector = next(iter(model.embed([query])))
            if hasattr(raw_vector, "tolist"):
                query_vector = raw_vector.tolist()
            else:
                query_vector = list(raw_vector)
        except Exception as e:
            return f"Ошибка при загрузке модели семантического поиска: {e}"

        for rel_path, data in index.items():
            if "vector" not in data:
                continue
            doc_vector = data["vector"]
            similarity = cosine_similarity(query_vector, doc_vector)

            mtime = data.get("mtime", current_time)
            age_days = (current_time - mtime) / (24 * 3600)
            recency_multiplier = math.exp(-age_days / 30.0)

            final_score = similarity * (0.5 + 0.5 * recency_multiplier)
            results.append((rel_path, final_score, data["content"]))

    # Сортируем результаты по итоговому скору
    results.sort(key=lambda x: x[1], reverse=True)

    # Формируем ответ
    brief_parts = []
    for rel_path, score, content in results[:limit]:
        brief_parts.append(
            f"#### Handoff: {rel_path} (Recency Score: {score:.4f})\n{content.strip()}"
        )

    if brief_parts:
        return "\n\n---\n\n".join(brief_parts)
    return "Релевантных логов сессий не найдено."
