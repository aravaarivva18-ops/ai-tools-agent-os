"""Tests for tools/obsidian/task_observer.py continuous session observer."""

import shutil
from pathlib import Path

import pytest

from tools.obsidian.task_observer import (
    analyze_handoffs,
    extract_tag_content,
    jaccard_similarity,
    update_proposed_rules,
)

# Временная рабочая папка для тестов
TEST_DIR = Path(__file__).parent / "observer_test_workspace"


@pytest.fixture(autouse=True)
def setup_test_env():
    """Создает и очищает тестовое окружение."""
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)


def test_extract_tag_content():
    """Проверяет правильное извлечение псевдо-XML тегов."""
    content = """
    <state_snapshot>
    <all_user_messages>
    Line 1
    Line 2
    </all_user_messages>
    </state_snapshot>
    """
    res = extract_tag_content(content, "all_user_messages")
    assert res == "Line 1\n    Line 2"


def test_jaccard_similarity():
    """Проверяет сходство Жаккара для близких и далеких фраз."""
    s1 = "не пиши комменты к коду"
    s2 = "не нужно писать комментарии к коду"
    assert jaccard_similarity(s1, s2) >= 0.35

    s3 = "запусти тесты в Healer"
    assert jaccard_similarity(s1, s3) < 0.2


def test_analyze_handoffs_finds_rules():
    """Проверяет, что при анализе похожих сообщений в хандоффах генерируется правило."""
    handoffs_dir = TEST_DIR / "vault/handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)

    # Создаем 2 файла хандоффов с похожими сообщениями
    h1 = handoffs_dir / "handoff_1.md"
    h1.write_text(
        "<state_snapshot>\n"
        "<all_user_messages>\n"
        "не пиши комменты к коду\n"
        "</all_user_messages>\n"
        "</state_snapshot>",
        encoding="utf-8"
    )

    h2 = handoffs_dir / "handoff_2.md"
    h2.write_text(
        "<state_snapshot>\n"
        "<all_user_messages>\n"
        "не нужно писать комментарии к коду\n"
        "</all_user_messages>\n"
        "</state_snapshot>",
        encoding="utf-8"
    )

    rules = analyze_handoffs(TEST_DIR)
    assert len(rules) == 1
    assert any(x in rules[0]["addition"] for x in ("не пиши комменты", "писать комментарии"))
    assert "Повторяющееся требование" in rules[0]["why"]


def test_update_proposed_rules():
    """Проверяет корректность записи предложенных правил в wiki/proposed_rules.md."""
    rules = [{
        "addition": "не пиши комменты к коду",
        "why": "Повторяющееся требование пользователя.",
        "prompt_scaffold": "Всегда следуй правилу: не пиши комменты"
    }]

    # Запускаем обновление
    update_proposed_rules(rules, TEST_DIR)

    proposed_file = TEST_DIR / "wiki/proposed_rules.md"
    assert proposed_file.exists()

    content = proposed_file.read_text(encoding="utf-8")
    assert "не пиши комменты к коду" in content
    assert "Повторяющееся требование" in content

    # Проверяем, что дубликат не запишется повторно
    update_proposed_rules(rules, TEST_DIR)
    content_after = proposed_file.read_text(encoding="utf-8")
    assert content_after == content
