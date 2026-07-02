"""
Оркестратор гибридного поиска по знаниям (Wiki + Memory).
"""


def global_search(query: str, limit: int = 3, semantic: bool = False) -> str:
    """
    Выполняет поиск как по локальной Wiki, так и по памяти Obsidian.
    Возвращает объединенный отформатированный результат.
    """
    from tools.knowledge.memory import search_memory
    from tools.knowledge.wiki import search_wiki

    wiki_result = search_wiki(query)
    memory_result = search_memory(query, limit=limit, semantic=semantic)

    parts = []
    if wiki_result:
        parts.append(f"=== RELEVANT WIKI KNOWLEDGE ===\n{wiki_result}")
    if memory_result:
        parts.append(f"=== RELEVANT MEMORY (HANDOFFS) ===\n{memory_result}")

    if not parts:
        return "Ничего не найдено."
    return "\n\n".join(parts)
