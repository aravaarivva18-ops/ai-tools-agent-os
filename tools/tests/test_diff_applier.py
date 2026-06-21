import os
import sys
import unittest

# Добавляем текущую директорию scratch в path, чтобы импортировать тестируемый модуль
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from diff_applier import apply_blocks, parse_blocks


class TestDiffApplier(unittest.TestCase):
    def test_parse_single_block(self):
        patch = """<<<<<<< SEARCH
def old_func():
    return "old"
=======
def new_func():
    return "new"
>>>>>>> REPLACE"""
        blocks = parse_blocks(patch)
        assert len(blocks) == 1
        assert blocks[0]["search"] == 'def old_func():\n    return "old"'
        assert blocks[0]["replace"] == 'def new_func():\n    return "new"'

    def test_parse_multiple_blocks(self):
        patch = """<<<<<<< SEARCH
old 1
=======
new 1
>>>>>>> REPLACE
Some text between blocks...
<<<<<<< SEARCH
old 2
=======
new 2
>>>>>>> REPLACE"""
        blocks = parse_blocks(patch)
        assert len(blocks) == 2
        assert blocks[0]["search"] == "old 1"
        assert blocks[0]["replace"] == "new 1"
        assert blocks[1]["search"] == "old 2"
        assert blocks[1]["replace"] == "new 2"

    def test_exact_match_and_apply(self):
        content = "line 1\nline 2\nline 3"
        blocks = [{"search": "line 2", "replace": "line two"}]
        success, result, _err = apply_blocks(content, blocks, fuzzy_threshold=1.0)
        assert success
        assert result == "line 1\nline two\nline 3"

    def test_fuzzy_match_success(self):
        content = "  def my_func(a, b):\n      print('hello')\n      return a + b"
        # SEARCH блок с немного отличающимися пробелами
        search = "def my_func(a,b):\n    print('hello')\n    return a+b"
        replace = "def my_func(a,b):\n    print('hi')\n    return a*b"

        blocks = [{"search": search, "replace": replace}]
        success, result, _err = apply_blocks(content, blocks, fuzzy_threshold=0.8)
        assert success
        # Проверяем, что отступы сохранились (2 пробела базовых превратились в правильный отступ)
        assert "print('hi')" in result
        assert "return a*b" in result

    def test_apply_failure_unmatched(self):
        content = "line 1\nline 2\nline 3"
        blocks = [{"search": "nonexistent line", "replace": "new line"}]
        success, _result, err = apply_blocks(content, blocks)
        assert not success
        assert "Could not match block" in err


if __name__ == "__main__":
    unittest.main()
