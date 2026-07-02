"""Tests for tools/json_utils.py safe JSON parsing utility."""

import json

import pytest

from tools.json_utils import safe_load_json


def test_safe_load_json_valid():
    """Проверяет корректный парсинг валидного JSON."""
    raw = '{"name": "Antigravity", "version": 1.0, "active": true}'
    res = safe_load_json(raw)
    assert res == {"name": "Antigravity", "version": 1.0, "active": True}


def test_safe_load_json_trailing_comma():
    """Проверяет исправление лишней запятой в конце объекта/массива."""
    raw_dict = '{"key": "value",}'
    res_dict = safe_load_json(raw_dict)
    assert res_dict == {"key": "value"}

    raw_list = '[1, 2, 3,]'
    res_list = safe_load_json(raw_list)
    assert res_list == [1, 2, 3]


def test_safe_load_json_missing_quotes():
    """Проверяет исправление пропущенных кавычек в ключах."""
    raw = '{key: "value"}'
    res = safe_load_json(raw)
    assert res == {"key": "value"}


def test_safe_load_json_unclosed_object():
    """Проверяет авто-закрытие скобок в неполном объекте."""
    raw = '{"key": "value"'
    res = safe_load_json(raw)
    assert res == {"key": "value"}


def test_safe_load_json_invalid_fallback():
    """Проверяет, что при полной невозможности починить падает стандартный json.loads."""
    raw = "not a json string"
    with pytest.raises(json.JSONDecodeError):
        safe_load_json(raw)


def test_safe_load_json_empty():
    """Проверяет парсинг пустой строки или None."""
    assert safe_load_json("") is None
    assert safe_load_json(None) is None
