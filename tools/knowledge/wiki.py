"""
Модуль для работы со справочной базой (Wiki).
Содержит тонкий ленивый фасад для RAG-запросов.
"""



def search_wiki(query_str: str, max_depth: int = 2) -> str:
    """
    Ищет информацию в локальной Wiki (tools/llm_wiki.py) по ключевым словам или нодам.
    """
    clean_query = query_str.strip()
    if not clean_query:
        return ""

    from tools.config import get_workspace_root
    from tools.llm_wiki import LLMWiki

    root = get_workspace_root()
    wiki = LLMWiki(root_dir=root)

    # Пробуем прямой запрос по ноде
    node_file = wiki.wiki_dir / f"{clean_query}.md"
    if node_file.is_file():
        return wiki.query(clean_query, max_depth=max_depth)

    # Иначе ищем вхождение ключевого слова в имена файлов
    matched_nodes = []
    for f in wiki.wiki_dir.glob("*.md"):
        if f.stem.lower() in ["index", "log"]:
            continue
        if clean_query.lower() in f.stem.lower():
            matched_nodes.append(f.stem)

    if matched_nodes:
        return wiki.query(matched_nodes[0], max_depth=max_depth)

    # Если не найдено по имени, ищем по тексту
    for f in wiki.wiki_dir.glob("*.md"):
        if f.stem.lower() in ["index", "log"]:
            continue
        try:
            content = f.read_text(encoding="utf-8")
            if clean_query.lower() in content.lower():
                matched_nodes.append(f.stem)
        except Exception:
            pass

    if matched_nodes:
        return wiki.query(matched_nodes[0], max_depth=max_depth)

    return f"В Wiki не найдено совпадений по запросу '{query_str}'"
