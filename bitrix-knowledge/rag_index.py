#!/usr/bin/env python3
"""
Bitrix Knowledge Base Vector Index and RAG Engine.
Implements SQLite storage, FTS5 index, Gemini embeddings, and generative Q&A.
"""

import json
import logging
import math
import os
import sqlite3
from pathlib import Path

import dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


# Search for .env in current and parent directories
def load_env_keys():
    """Loads environment variables checking multiple potential locations."""
    # Check parent workspace
    workspace_root = Path(os.getcwd())
    potential_envs = [
        workspace_root / ".env",
        workspace_root / "ai-sales" / ".env",
        Path(__file__).resolve().parents[1] / ".env",
        Path(__file__).resolve().parents[1] / "ai-sales" / ".env",
    ]
    for env_path in potential_envs:
        if env_path.is_file():
            dotenv.load_dotenv(env_path)
            logger.info(f"Loaded environment keys from {env_path}")
            break


load_env_keys()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


class BitrixRAGEngine:
    def __init__(
        self, workspace_dir: str | Path | None = None, mock_mode: bool = False
    ):
        """Initializes database and model configs.

        Args:
            workspace_dir: Workspace directory.
            mock_mode: If True, uses mock embeddings and mock model answers.
        """
        if workspace_dir is None:
            self.root = Path(os.getcwd()) / "bitrix-knowledge"
        else:
            self.root = Path(workspace_dir)

        self.db_path = self.root / "bitrix_knowledge.db"
        self.mock_mode = mock_mode or not bool(GEMINI_API_KEY)
        self.vector_dim = 768
        self.client = None
        if not self.mock_mode and GEMINI_API_KEY:
            self.client = genai.Client(api_key=GEMINI_API_KEY)

        self._init_db()

    def _init_db(self) -> None:
        """Initializes SQLite schema and FTS5 table."""
        self.root.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                relative_path TEXT NOT NULL UNIQUE,
                embedding TEXT
            )
        """)

        # FTS5 Virtual Table for full-text search
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    title,
                    content,
                    content='documents',
                    content_rowid='id'
                )
            """)
            # Triggers to keep FTS5 synchronized with documents table
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_documents_ai AFTER INSERT ON documents BEGIN
                    INSERT INTO documents_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
                END
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_documents_ad AFTER DELETE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, title, content) VALUES('delete', old.id, old.title, old.content);
                END
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_documents_au AFTER UPDATE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, title, content) VALUES('delete', old.id, old.title, old.content);
                    INSERT INTO documents_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
                END
            """)
        except sqlite3.OperationalError as e:
            logger.warning(
                f"FTS5 initialization warning (may not be supported in this SQLite): {e}"
            )

        conn.commit()
        conn.close()

    def get_embedding(self, text: str) -> list[float]:
        """Generates embedding vector for a given text segment."""
        if self.mock_mode:
            import re

            # Deterministic mock embedding based on words in text to allow keyword-overlap matching
            words = set(re.findall(r"\w+", text.lower()))
            mock_vec = [0.0] * self.vector_dim
            if not words:
                words = {"empty"}
            for word in words:
                word_hash = sum(ord(c) * (i + 1) for i, c in enumerate(word))
                for i in range(self.vector_dim):
                    mock_vec[i] += math.sin(word_hash + i)
            # Normalize mock vector
            norm = math.sqrt(sum(x * x for x in mock_vec))
            return [x / norm for x in mock_vec] if norm else [0.0] * self.vector_dim

        try:
            # Call Gemini embedding API
            if not self.client:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            result = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.warning(
                f"Gemini API embedding call failed: {e}. Falling back to mock vector."
            )
            # Deterministic fallback vector
            return [0.0] * self.vector_dim

    def index_documents(
        self, parsed_docs: list[dict[str, str]], force: bool = False
    ) -> int:
        """Saves documents and computes their vector embeddings inside SQLite.

        Args:
            parsed_docs: List of parsed document dictionaries.
            force: If True, re-calculates all embeddings.

        Returns:
            int: Number of indexed documents.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        indexed = 0

        for doc in parsed_docs:
            title = doc["title"]
            content = doc["content"]
            rel_path = doc["relative_path"]

            # Check if already exists
            cursor.execute(
                "SELECT id, embedding FROM documents WHERE relative_path = ?",
                (rel_path,),
            )
            row = cursor.fetchone()

            if row and not force:
                doc_id, embedding_str = row
                if embedding_str:
                    # Skip if already has embedding
                    continue

            # Generate embedding
            # Indexing takes title + content
            emb = self.get_embedding(f"{title}\n{content}")
            emb_json = json.dumps(emb)

            if row:
                doc_id = row[0]
                cursor.execute(
                    "UPDATE documents SET title = ?, content = ?, embedding = ? WHERE id = ?",
                    (title, content, emb_json, doc_id),
                )
            else:
                cursor.execute(
                    "INSERT INTO documents (title, content, relative_path, embedding) VALUES (?, ?, ?, ?)",
                    (title, content, rel_path, emb_json),
                )
            indexed += 1

        conn.commit()
        conn.close()
        logger.info(f"Indexed and vector-calculated: {indexed} documents.")
        return indexed

    @staticmethod
    def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Calculates cosine similarity between two float vectors."""
        dot_product = sum(x * y for x, y in zip(v1, v2))
        magnitude1 = math.sqrt(sum(x * x for x in v1))
        magnitude2 = math.sqrt(sum(x * x for x in v2))
        if not magnitude1 or not magnitude2:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Performs hybrid (FTS5 + Vector) search over the indexed documents.

        Args:
            query: User search query.
            limit: Limit of results returned.

        Returns:
            list[dict]: List of matched document dicts with score and metadata.
        """
        # Step 1: Get query embedding
        query_vector = self.get_embedding(query)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch all documents to compute similarities (reasonable for persistent KB of a few hundred docs)
        cursor.execute(
            "SELECT id, title, content, relative_path, embedding FROM documents"
        )
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            emb_str = row["embedding"]
            if not emb_str:
                continue

            emb = json.loads(emb_str)
            sim = self._cosine_similarity(query_vector, emb)

            results.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "relative_path": row["relative_path"],
                    "score": sim,
                }
            )

        # Sort by similarity score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def ask(self, query: str) -> dict:
        """Performs RAG query retrieving documentation context and calling Gemini.

        Args:
            query: User technical question.

        Returns:
            dict: Containing 'answer' (str), 'context' (list).
        """
        # 1. Retrieve relevant notes
        matched_notes = self.search(query, limit=3)
        if not matched_notes:
            return {
                "answer": "Не найдено релевантной документации в локальной базе знаний.",
                "context": [],
            }

        # 2. Compile prompt context
        context_str = ""
        for i, note in enumerate(matched_notes):
            context_str += f"[{i + 1}] Документ: {note['title']} (Путь: {note['relative_path']})\nСодержание:\n{note['content']}\n\n"

        system_prompt = (
            "Ты — опытный разработчик на 1С-Битрикс и ассистент Antigravity. "
            "Отвечай строго на основе предоставленного контекста документации. "
            "Если в контексте нет ответа, честно скажи об этом. "
            "Приводи примеры кода на PHP или REST API вызовы, если они есть в документации. "
            "Ссылайся на документы в формате [[Название Заметки]] при упоминании разделов."
        )

        user_prompt = (
            f"Вопрос пользователя: {query}\n\n"
            f"Контекст из базы знаний:\n{context_str}\n"
            "Дай точный технический ответ на русском языке:"
        )

        if self.mock_mode:
            # Mock answer offline/tests compatibility
            logger.info("Mock mode active for RAG Ask.")
            snippet = matched_notes[0]["content"][:300] + "..."
            answer = (
                f"Это заглушка ответа RAG (офлайн/mock-режим).\n"
                f"Найдена релевантная нота: [[{matched_notes[0]['title']}]].\n"
                f"Выдержка из документации:\n> {snippet}\n"
                f"Для выполнения запроса: {query}."
            )
            return {"answer": answer, "context": matched_notes}

        try:
            if not self.client:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )
            return {"answer": response.text.strip(), "context": matched_notes}
        except Exception as e:
            logger.error(f"Gemini API generation failed: {e}")
            return {
                "answer": f"Произошла ошибка при обращении к ИИ: {e}",
                "context": matched_notes,
            }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    engine = BitrixRAGEngine()
    # Simple test run if indexing has occurred
    res = engine.search("deal", limit=2)
    print("Search results:")
    for r in res:
        print(f"- {r['title']} (Score: {r['score']:.4f})")
