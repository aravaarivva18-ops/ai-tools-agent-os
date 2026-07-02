#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

try:
    from tools.config import get_workspace_root, load_config
except ImportError:
    # Фолбэк на случай если запускают напрямую из папки tools/obsidian/
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.config import get_workspace_root, load_config

INDEX_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "handoffs_index.json"
)

config = load_config()
workspace_root = get_workspace_root()
VAULT_HANDOFFS_DIR = os.path.join(
    workspace_root, config.get("vault", {}).get("handoffs_dir", "vault/handoffs")
)

CACHE_FILE = os.path.join(
    workspace_root, config.get("vault", {}).get("search_cache_file", "vault/search_cache.json")
)

def get_handoffs_mtime() -> float:
    """Вычисляет максимальное mtime файлов в vault/handoffs/."""
    if not os.path.exists(VAULT_HANDOFFS_DIR):
        return 0.0
    mtimes = []
    for root, _, files in os.walk(VAULT_HANDOFFS_DIR):
        for file in files:
            if file.endswith(".md"):
                try:
                    mtimes.append(os.path.getmtime(os.path.join(root, file)))
                except Exception:
                    pass
    return max(mtimes) if mtimes else 0.0

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_model():
    """Загружает fastembed модель."""
    try:
        from fastembed import TextEmbedding

        # Подавляем лишний вывод fastembed при инициализации
        return TextEmbedding(model_name=MODEL_NAME)
    except ImportError:
        print(
            "❌ Ошибка: библиотека 'fastembed' не установлена во виртуальном окружении."
        )
        sys.exit(1)


def load_index():
    """Загружает существующий индекс."""
    if os.path.exists(INDEX_FILE):
        try:
            from tools.json_utils import safe_load_json
            with open(INDEX_FILE, encoding="utf-8") as f:
                res = safe_load_json(f.read())
                return res if isinstance(res, dict) else {}
        except Exception as e:
            print(f"⚠️ Ошибка чтения индекса, создаем новый: {e}")
    return {}


def save_index(index):
    """Сохраняет индекс на диск."""
    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка сохранения индекса: {e}")


def index_handoffs(force=False):
    """Сканирует и индексирует файлы хандоффов."""
    if not os.path.exists(VAULT_HANDOFFS_DIR):
        print(f"❌ Папка хандоффов не найдена: {VAULT_HANDOFFS_DIR}")
        return

    print("⚙️ Сканирование файлов в vault/handoffs/...")
    md_files = []
    for root, _, files in os.walk(VAULT_HANDOFFS_DIR):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))

    if not md_files:
        print("ℹ️ Файлы хандоффов не найдены.")
        return

    index = load_index()
    model = None
    updated = False

    for file_path in md_files:
        rel_path = os.path.relpath(file_path, VAULT_HANDOFFS_DIR)
        mtime = os.path.getmtime(file_path)

        # Индексируем только новые/измененные файлы
        if not force and rel_path in index and index[rel_path].get("mtime") == mtime:
            continue

        print(f"⚙️ Индексация: {rel_path}...")
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                continue

            if model is None:
                model = load_model()

            # Генерируем вектор
            vector = next(iter(model.embed([content]))).tolist()

            index[rel_path] = {"mtime": mtime, "content": content, "vector": vector}
            updated = True
        except Exception as e:
            print(f"❌ Ошибка индексации {rel_path}: {e}")

    # Удаляем из индекса файлы, которых больше нет на диске
    existing_rel_paths = {os.path.relpath(p, VAULT_HANDOFFS_DIR) for p in md_files}
    for rel_path in list(index.keys()):
        if rel_path not in existing_rel_paths:
            print(f"⚙️ Удаление устаревшего индекса: {rel_path}")
            del index[rel_path]
            updated = True

    if updated:
        save_index(index)
        print("✅ Индекс успешно обновлен!")
    else:
        print("✅ Изменений не обнаружено. Индекс актуален.")


def text_search(query, index, limit=3):
    """Ищет совпадения по ключевым словам в индексе (без загрузки FastEmbed)."""
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    if not query_words:
        query_words = [query.lower()]

    results = []
    for rel_path, data in index.items():
        content_lower = data["content"].lower()
        score = 0
        for word in query_words:
            score += content_lower.count(word)

        if score > 0:
            # Нормализуем по длине контента
            score = score / (len(content_lower) + 1) * 1000
            results.append((rel_path, score, data["content"]))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def search_handoffs(query, limit=3, semantic=False):
    """Ищет релевантные хандоффы по ключевым словам или семантическому сходству."""
    index = load_index()
    if not index:
        print("⚠️ Индекс пуст. Сначала запустите индексацию: agy search --index")
        return

    if not semantic:
        results = text_search(query, index, limit)
        if results:
            print(f"\n🔍 Результаты быстрого текстового поиска по запросу: '{query}'")
            print("=" * 60)
            for i, (rel_path, score, content) in enumerate(results, 1):
                preview = content[:200].replace("\n", " ").strip() + "..."
                print(
                    f"{i}. [{rel_path}](file://{os.path.join(VAULT_HANDOFFS_DIR, rel_path)}) (Score: {score:.2f})"
                )
                print(f"   Превью: {preview}")
                print("-" * 60)
            return

    # Семантический поиск
    model = load_model()
    query_vector = np.array(next(iter(model.embed([query]))))

    results = []
    for rel_path, data in index.items():
        if "vector" not in data:
            continue
        doc_vector = np.array(data["vector"])
        dot_product = np.dot(query_vector, doc_vector)
        norm_q = np.linalg.norm(query_vector)
        norm_d = np.linalg.norm(doc_vector)
        similarity = (
            dot_product / (norm_q * norm_d) if norm_q > 0 and norm_d > 0 else 0.0
        )
        results.append((rel_path, similarity, data["content"]))

    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\n🔍 Результаты семантического поиска по запросу: '{query}'")
    print("=" * 60)
    for i, (rel_path, similarity, content) in enumerate(results[:limit], 1):
        preview = content[:200].replace("\n", " ").strip() + "..."
        print(
            f"{i}. [{rel_path}](file://{os.path.join(VAULT_HANDOFFS_DIR, rel_path)}) (Сходство: {similarity:.4f})"
        )
        print(f"   Превью: {preview}")
        print("-" * 60)


def get_semantic_brief(query: str, limit: int = 3, semantic: bool = False) -> str:
    """Возвращает быстрый текстовый или семантический дайджест для интеграции с планировщиком (с поддержкой кэша)."""
    current_mtime = get_handoffs_mtime()
    cache = {"queries": {}}
    if os.path.exists(CACHE_FILE):
        try:
            from tools.json_utils import safe_load_json
            with open(CACHE_FILE, encoding="utf-8") as f:
                loaded = safe_load_json(f.read())
                if isinstance(loaded, dict) and "queries" in loaded:
                    cache = loaded
        except Exception:
            pass

    cache_key = f"{query}__{limit}__{semantic}"
    if cache_key in cache.get("queries", {}):
        item = cache["queries"][cache_key]
        if item.get("mtime") == current_mtime:
            return item.get("brief", "")

    index = load_index()
    if not index:
        return ""

    brief_result = ""
    # Сначала пробуем быстрый текстовый поиск
    text_results = text_search(query, index, limit)
    if text_results:
        brief_parts = []
        for rel_path, score, content in text_results:
            brief_parts.append(
                f"#### Handoff: {rel_path} (Быстрый поиск, Score: {score:.2f})\n{content.strip()}"
            )
        brief_result = "\n\n---\n\n".join(brief_parts)
    else:
        # Если текстовых совпадений нет и семантический поиск отключен, выходим без загрузки fastembed (YAGNI)
        if not semantic:
            brief_result = "ℹ️ Быстрый поиск не дал результатов. Векторный поиск отключен (YAGNI)."
        else:
            # Если текстовых совпадений нет, лениво загружаем fastembed и делаем векторный поиск
            try:
                model = load_model()
                query_vector = np.array(next(iter(model.embed([query]))))
            except Exception as e:
                return f"⚠️ Ошибка инициализации модели семантического поиска: {e}"

            results = []
            for rel_path, data in index.items():
                if "vector" not in data:
                    continue
                doc_vector = np.array(data["vector"])
                dot_product = np.dot(query_vector, doc_vector)
                norm_q = np.linalg.norm(query_vector)
                norm_d = np.linalg.norm(doc_vector)
                similarity = (
                    dot_product / (norm_q * norm_d) if norm_q > 0 and norm_d > 0 else 0.0
                )
                results.append((rel_path, similarity, data["content"]))

            results.sort(key=lambda x: x[1], reverse=True)

            brief_parts = []
            for rel_path, similarity, content in results[:limit]:
                if similarity < 0.4:
                    continue
                brief_parts.append(
                    f"#### Handoff: {rel_path} (Семантическое сходство: {similarity:.2f})\n{content.strip()}"
                )

            if brief_parts:
                brief_result = "\n\n---\n\n".join(brief_parts)
            else:
                brief_result = "ℹ️ Релевантных хэндоффов прошлых сессий не обнаружено."

    # Сохраняем в кэш
    if "queries" not in cache:
        cache["queries"] = {}
    cache["queries"][cache_key] = {
        "mtime": current_mtime,
        "brief": brief_result
    }
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return brief_result


def main():
    parser = argparse.ArgumentParser(
        description="Локальный гибридный поиск по файлам HANDOFF.md."
    )
    parser.add_argument("query", nargs="?", help="Поисковый запрос.")
    parser.add_argument(
        "--index", "-i", action="store_true", help="Обновить индекс файлов."
    )
    parser.add_argument(
        "--force", action="store_true", help="Принудительно переиндексировать всё."
    )
    parser.add_argument(
        "--semantic",
        "-s",
        action="store_true",
        help="Использовать векторный поиск вместо текстового.",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=3,
        help="Количество результатов (по умолчанию 3).",
    )
    args = parser.parse_args()

    if args.index or args.force:
        index_handoffs(force=args.force)
    elif args.query:
        search_handoffs(args.query, limit=args.limit, semantic=args.semantic)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
