from tools import context_utils


def test_estimate_tokens_fast():
    assert context_utils.estimate_tokens_fast("") == 0
    assert context_utils.estimate_tokens_fast("abcd") == 1
    assert context_utils.estimate_tokens_fast("abcdefgh") == 2


def test_count_tokens_exact():
    # Проверим, что функция работает
    text = "Hello world!"
    # Без мока tiktoken должен отработать (так как tiktoken установлен в .venv)
    exact = context_utils.count_tokens_exact(text)
    fast = context_utils.estimate_tokens_fast(text)
    assert exact > 0
    # Проверим fallback при ошибке tiktoken
    # Замокаем импорт tiktoken с помощью некорректного поведения
    import sys
    from unittest import mock
    with mock.patch.dict(sys.modules, {"tiktoken": None}):
        assert context_utils.count_tokens_exact(text) == fast


def test_trim_context_fits():
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "User question"},
    ]
    # Все укладывается в большой лимит
    trimmed = context_utils.trim_context(messages, 1000)
    assert trimmed == messages


def test_trim_context_removes_old_non_system():
    # Каждое сообщение примерно по 3-4 токена (или по эвристике 12 символов / 4 = 3 токена)
    messages = [
        {"role": "system", "content": "Keep system rule"},
        {"role": "user", "content": "Old user message"},
        {"role": "assistant", "content": "Old assistant reply"},
        {"role": "user", "content": "Latest user query"},
    ]
    # Если мы зададим лимит в 10 токенов (или аналогичный по символам)
    # Посчитаем общую длину контента:
    # "Keep system rule" = 16 симв
    # "Old user message" = 16 симв
    # "Old assistant reply" = 19 симв
    # "Latest user query" = 17 симв
    #
    # Защищенные: Keep system rule (индекс 0) и Latest user query (индекс 3).
    # Удалить можно: Old user message (индекс 1) и Old assistant reply (индекс 2).
    # Установим лимит токенов так, чтобы удалились только старые сообщения.
    # Давайте замокаем count_tokens_exact, чтобы точно контролировать лимиты токенов.
    from unittest import mock

    def mock_count(text, model="gpt-4"):
        if "Keep system rule" in text:
            return 5
        if "Old user message" in text:
            return 5
        if "Old assistant reply" in text:
            return 5
        if "Latest user query" in text:
            return 5
        return 0

    with mock.patch("tools.context_utils.count_tokens_exact", side_effect=mock_count):
        # Всего токенов = 20.
        # Защищенные (system + latest) = 10 токенов.
        # Если лимит = 15, то должно удалиться одно старое незащищенное сообщение ("Old user message").
        trimmed_15 = context_utils.trim_context(messages, 15)
        assert len(trimmed_15) == 3
        assert trimmed_15[0]["content"] == "Keep system rule"
        assert trimmed_15[1]["content"] == "Old assistant reply"
        assert trimmed_15[2]["content"] == "Latest user query"

        # Если лимит = 10, должны удалиться оба незащищенных.
        trimmed_10 = context_utils.trim_context(messages, 10)
        assert len(trimmed_10) == 2
        assert trimmed_10[0]["content"] == "Keep system rule"
        assert trimmed_10[1]["content"] == "Latest user query"

        # Если лимит = 5, то защищенные сообщения все равно не удаляются.
        trimmed_5 = context_utils.trim_context(messages, 5)
        assert len(trimmed_5) == 2
        assert trimmed_5[0]["content"] == "Keep system rule"
        assert trimmed_5[1]["content"] == "Latest user query"
