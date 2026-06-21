import pytest
from tools.normalize_constitution import normalize_headings, ensure_core_block

def test_renumbering_positive():
    src = "## 🏛️ 1. Foo\n## 🧠 5. Bar\n## 📉 7. Baz\n"
    out = normalize_headings(src)
    assert "## 🏛️ 1. Foo\n" in out
    assert "## 🧠 2. Bar\n" in out
    assert "## 📉 3. Baz\n" in out

def test_renumbering_idempotency():
    src = "## 🏛️ 1. Foo\n## 🧠 5. Bar\n## 📉 7. Baz\n"
    first = normalize_headings(src)
    second = normalize_headings(first)
    assert first == second

def test_renumbering_no_emoji():
    src = "## 1. Foo\n## 5. Bar\n"
    out = normalize_headings(src)
    assert "## 1. Foo\n" in out
    assert "## 2. Bar\n" in out

def test_core_block_added_negative():
    src = "# Заголовок\n## 1. Первый раздел\n"
    out = ensure_core_block(src)
    assert "## 🏛️ Ядро (Core Imperatives)" in out
    assert "Solo Loop v10" in out
