#!/usr/bin/env python3
import argparse
import json
import os
import sys

import numpy as np

INDEX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "handoffs_index.json")
VAULT_HANDOFFS_DIR = "/Users/rus/ai-tools/vault/handoffs"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def load_model():
    """Загружает fastembed модель."""
    try:
        from fastembed import TextEmbedding
        # Подавляем лишний вывод fastembed при инициализации
        return TextEmbedding(model_name=MODEL_NAME)
    except ImportError:
        print("❌ Ошибка: библиотека 'fastembed' не установлена во виртуальном окружении.")
        sys.exit(1)

def load_index():
    """Загружает существующий индекс."""
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, encoding="utf-8") as f:
                return json.load(f)
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

            index[rel_path] = {
                "mtime": mtime,
                "content": content,
                "vector": vector
            }
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

def search_handoffs(query, limit=3):
    """Ищет релевантные хандоффы по семантическому сходству."""
    index = load_index()
    if not index:
        print("⚠️ Индекс пуст. Сначала запустите индексацию: python semantic_search.py --index")
        return

    model = load_model()
    # Получаем вектор запроса
    query_vector = np.array(next(iter(model.embed([query]))))

    results = []
    for rel_path, data in index.items():
        doc_vector = np.array(data["vector"])

        # Вычисляем косинусное сходство
        dot_product = np.dot(query_vector, doc_vector)
        norm_q = np.linalg.norm(query_vector)
        norm_d = np.linalg.norm(doc_vector)

        similarity = dot_product / (norm_q * norm_d) if norm_q > 0 and norm_d > 0 else 0.0
        results.append((rel_path, similarity, data["content"]))

    # Сортируем по убыванию сходства
    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\n🔍 Результаты поиска по запросу: '{query}'")
    print("=" * 60)
    for i, (rel_path, similarity, content) in enumerate(results[:limit], 1):
        # Берем первые 200 символов для превью
        preview = content[:200].replace("\n", " ").strip() + "..."
        print(f"{i}. [{rel_path}](file://{os.path.join(VAULT_HANDOFFS_DIR, rel_path)}) (Сходство: {similarity:.4f})")
        print(f"   Превью: {preview}")
        print("-" * 60)

def main():
    parser = argparse.ArgumentParser(description="Локальный семантический поиск по файлам HANDOFF.md.")
    parser.add_argument("query", nargs="?", help="Поисковый запрос.")
    parser.add_argument("--index", "-i", action="store_true", help="Обновить индекс файлов.")
    parser.add_argument("--force", action="store_true", help="Принудительно переиндексировать всё.")
    parser.add_argument("--limit", "-l", type=int, default=3, help="Количество результатов (по умолчанию 3).")
    args = parser.parse_args()

    if args.index or args.force:
        index_handoffs(force=args.force)
    elif args.query:
        search_handoffs(args.query, limit=args.limit)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
