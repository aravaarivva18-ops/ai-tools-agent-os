"""
Модуль для работы с контекстом и токенами.
Содержит только свободные функции и ленивые импорты для максимальной скорости CLI.
"""



def estimate_tokens_fast(text: str) -> int:
    """Быстрая эвристика оценки количества токенов (длина текста / 4)."""
    if not text:
        return 0
    return len(text) // 4


def count_tokens_exact(text: str, model: str = "gpt-4") -> int:
    """
    Точный подсчет токенов с использованием tiktoken.
    Выполняет ленивый импорт tiktoken для предотвращения замедления старта CLI.
    В случае ошибки импорта или работы tiktoken переходит на fast-эвристику.
    """
    if not text:
        return 0
    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Дефолтная кодировка для большинства моделей OpenAI
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return estimate_tokens_fast(text)


def trim_context(messages: list[dict[str, str]], max_tokens: int, model: str = "gpt-4") -> list[dict[str, str]]:
    """
    Обрезает контекст сообщений до max_tokens.
    Приоритеты:
    1. Системные сообщения (role == "system") и текущий запрос (последнее сообщение в списке)
       никогда не режутся и не удаляются.
    2. Прочие сообщения удаляются по одному, начиная с самых старых.
    """
    if not messages:
        return []

    # Если уже укладываемся в лимит, возвращаем как есть
    def get_total_tokens(msg_list: list[dict[str, str]]) -> int:
        return sum(count_tokens_exact(m.get("content", ""), model) for m in msg_list)

    if get_total_tokens(messages) <= max_tokens:
        return list(messages)

    # Защищенные сообщения: все system и последнее сообщение
    protected_indices = set()
    for i, m in enumerate(messages):
        if m.get("role") == "system":
            protected_indices.add(i)
    if messages:
        protected_indices.add(len(messages) - 1)

    # Кандидаты на удаление: индексы, которые не защищены, в хронологическом порядке (от старых к новым)
    candidates = [i for i in range(len(messages)) if i not in protected_indices]

    # Строим результат, исключая удаляемые сообщения
    # Будем удалять кандидатов с начала списка, пока общие токены > max_tokens
    removed_indices = set()
    for idx in candidates:
        # Проверяем текущий размер без уже удаленных
        current_active = [m for j, m in enumerate(messages) if j not in removed_indices]
        if get_total_tokens(current_active) <= max_tokens:
            break
        removed_indices.add(idx)

    return [m for j, m in enumerate(messages) if j not in removed_indices]
