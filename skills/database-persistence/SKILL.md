---
name: database-persistence
description: Guidelines and patterns for Supabase, pgvector, and Alembic database persistence in AI agents.
---

# Хранение состояния агентов: Supabase, pgvector & Alembic

Этот навык описывает стандарты проектирования баз данных для хранения состояния ИИ-агентов, семантического поиска по истории диалогов и управления миграциями в монорепозитории.

## 💾 1. Схема хранения сессий агентов (JSONB Pattern)

Для гибкости стейта агентов используется гибридная схема:
- **Строгие реляционные колонки** для метаданных (`id`, `user_id`, `created_at`, `status`).
- **Столбец типа `JSONB`** для хранения динамического состояния графа или памяти агента.

### SQL Схема (PostgreSQL / Supabase):
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL, -- 'legal', 'sales', 'marketing'
    status VARCHAR(20) DEFAULT 'active',
    state JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Индекс для быстрого поиска внутри JSONB стейта
CREATE INDEX idx_agent_sessions_state_gin ON agent_sessions USING gin (state);
```

---

## 🔍 2. Векторный поиск по истории (pgvector & HNSW)

Для семантической памяти агентов (Semantic Memory) используется расширение `pgvector`. Для масштабируемости (100k+ векторов) применяется индекс HNSW (Hierarchical Navigable Small World).

```sql
-- Подключение pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Таблица для эмбеддингов сообщений
CREATE TABLE agent_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant'
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL, -- Размерность для OpenAI text-embedding-3-small
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Создание индекса HNSW для косинусного сходства (Cosine Distance)
CREATE INDEX idx_agent_memory_embedding_hnsw 
ON agent_memory USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Пример семантического поиска сходства (SQL):
```sql
CREATE OR REPLACE FUNCTION search_agent_memory(
    query_embedding VECTOR(1536),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE (
    id UUID,
    session_id UUID,
    content TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.session_id,
        m.content,
        1 - (m.embedding <=> query_embedding) AS similarity
    FROM agent_memory m
    WHERE 1 - (m.embedding <=> query_embedding) > match_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

---

## 🔒 3. Безопасность на уровне строк (Row Level Security - RLS)

В Supabase безопасность данных каждого клиента обязательна через RLS-политики.

```sql
-- Включение RLS
ALTER TABLE agent_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_memory ENABLE ROW LEVEL SECURITY;

-- Создание политики для сессий (доступ только владельцу)
CREATE POLICY "Users can manage their own agent sessions"
ON agent_sessions
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Создание политики для памяти
CREATE POLICY "Users can manage memory in their sessions"
ON agent_memory
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM agent_sessions 
        WHERE agent_sessions.id = agent_memory.session_id 
        AND agent_sessions.user_id = auth.uid()
    )
);
```

---

## 🛠️ 4. Управление миграциями через Alembic в монорепозитории

В монорепозиториях запрещено иметь единую глобальную папку миграций. Каждый подпроект должен управлять своими таблицами обособленно:

1. **Изолированные конфиги:** Каждый сервис имеет свой `alembic.ini` и папку `migrations/` (или `alembic/`) внутри своей директории.
2. **Запуск в CI/CD:** Миграции запускаются как **Pre-deployment task** в пайплайне деплоя. Запуск миграций `alembic upgrade head` на ходу при старте докер-контейнера приложения строго запрещен (чтобы избежать конфликтов гонки при масштабировании реплик).
