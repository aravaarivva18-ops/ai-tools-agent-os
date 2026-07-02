import os
import pytest
from unittest.mock import patch
from tools.obsidian.semantic_search import get_semantic_brief, CACHE_FILE


@pytest.fixture(autouse=True)
def clean_cache():
    """Удаляет файл кэша перед и после каждого теста."""
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass
    yield
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass


def test_semantic_brief_cache_flow():
    """Проверяет запись в кэш, чтение из кэша и инвалидацию при изменении mtime."""
    # 1. Мокаем mtime и индекс
    mock_index = {
        "test_handoff.md": {
            "mtime": 100.0,
            "content": "Содержимое тестового хандоффа с ключевым словом target_query",
            "vector": [0.1, 0.2, 0.3]
        }
    }

    with patch("tools.obsidian.semantic_search.get_handoffs_mtime") as mock_mtime, \
         patch("tools.obsidian.semantic_search.load_index") as mock_load:
        
        mock_mtime.return_value = 100.0
        mock_load.return_value = mock_index

        # 2. Первый поиск (кэш пуст, должен сработать реальный поиск)
        brief1 = get_semantic_brief("target_query", limit=1, semantic=False)
        assert "target_query" in brief1
        assert mock_load.call_count == 1

        # Проверим, что файл кэша создался
        assert os.path.exists(CACHE_FILE)

        # 3. Второй поиск с тем же запросом и тем же mtime (должен отдать из кэша без load_index)
        mock_load.reset_mock()
        brief2 = get_semantic_brief("target_query", limit=1, semantic=False)
        assert brief2 == brief1
        assert mock_load.call_count == 0  # load_index НЕ вызывался!

        # 4. Изменяем mtime (инвалидация кэша)
        mock_mtime.return_value = 200.0
        mock_load.reset_mock()
        brief3 = get_semantic_brief("target_query", limit=1, semantic=False)
        assert brief3 == brief1
        assert mock_load.call_count == 1  # load_index снова вызвался!
