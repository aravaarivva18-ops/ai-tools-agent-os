import tempfile
from pathlib import Path
from unittest import mock

import pytest

from tools.knowledge.memory import (
    cosine_similarity,
    dot_product,
    magnitude,
    search_memory,
)
from tools.knowledge.search import global_search
from tools.knowledge.wiki import search_wiki


def test_vector_math():
    v1 = [1.0, 0.0]
    v2 = [1.0, 0.0]
    v3 = [0.0, 1.0]
    assert dot_product(v1, v2) == 1.0
    assert magnitude(v1) == 1.0
    assert cosine_similarity(v1, v2) == 1.0
    assert cosine_similarity(v1, v3) == 0.0


@pytest.fixture
def mock_wiki_setup():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()

        # Создаем тестовые ноды
        (wiki_dir / "index.md").write_text("# Index", encoding="utf-8")
        (wiki_dir / "Log.md").write_text("# Log", encoding="utf-8")
        (wiki_dir / "python_tips.md").write_text("# Python Tips\nUse early returns.", encoding="utf-8")
        (wiki_dir / "docker.md").write_text("# Docker\nContainerize your apps.", encoding="utf-8")

        with mock.patch("tools.config.get_workspace_root", return_value=tmp_path):
            yield tmp_path


def test_search_wiki_direct(mock_wiki_setup):
    res = search_wiki("python_tips")
    assert "Use early returns" in res


def test_search_wiki_partial_name(mock_wiki_setup):
    res = search_wiki("tips")
    assert "Use early returns" in res


def test_search_wiki_content(mock_wiki_setup):
    res = search_wiki("Containerize")
    assert "Containerize your apps" in res


def test_search_wiki_not_found(mock_wiki_setup):
    res = search_wiki("javascript")
    assert "не найдено" in res


@pytest.fixture
def mock_obsidian_setup():
    mock_index = {
        "session_1.md": {
            "mtime": 1000.0,
            "content": "Refactored python code.",
            "vector": [1.0, 0.0]
        },
        "session_2.md": {
            "mtime": 2000.0,
            "content": "Refactored rust code.",
            "vector": [0.0, 1.0]
        }
    }
    with mock.patch("tools.obsidian.semantic_search.load_index", return_value=mock_index):
        yield mock_index


def test_search_memory_text(mock_obsidian_setup):
    # Тестируем текстовый поиск
    # Запрос "rust" должен вернуть session_2.md, так как там есть слово "rust"
    res = search_memory("rust", semantic=False)
    assert "session_2.md" in res
    assert "rust code" in res


def test_search_memory_semantic(mock_obsidian_setup):
    # Тестируем семантический поиск через мок модели
    mock_model = mock.MagicMock()
    mock_model.embed.return_value = [[0.0, 1.0]]  # Вектор запроса близок к session_2.md

    with mock.patch("tools.obsidian.semantic_search.load_model", return_value=mock_model):
        res = search_memory("rust", semantic=True)
        assert "session_2.md" in res
        # Должен отдать предпочтение session_2.md
        assert "rust code" in res


def test_global_search(mock_wiki_setup, mock_obsidian_setup):
    res = global_search("python")
    assert "=== RELEVANT WIKI KNOWLEDGE ===" in res
    assert "=== RELEVANT MEMORY (HANDOFFS) ===" in res
