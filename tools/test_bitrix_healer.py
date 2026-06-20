import os

import pytest

from tools.bitrix_healer import heal_file


def test_heal_file_no_duplicate(tmp_path):
    # Setup test file
    test_php = tmp_path / "init.php"
    content = """<?php
// Some initialization code
use Bitrix\\Main\\EventManager;

EventManager::getInstance()->addEventHandler("main", "OnPageStart", function() {});
"""
    test_php.write_text(content, encoding="utf-8")

    # Run healing
    healed = heal_file(str(test_php))

    # It should replace EventManager:: with absolute path
    assert healed is True

    # Check backup file exists
    assert os.path.exists(str(test_php) + ".bak")

    # Check healed content
    healed_content = test_php.read_text(encoding="utf-8")
    assert "\\Bitrix\\Main\\EventManager::getInstance()" in healed_content
    # Import should remain as is
    assert "use Bitrix\\Main\\EventManager;" in healed_content


def test_heal_file_duplicate_imports(tmp_path):
    # Setup test file with duplicate EventManager imports
    test_php = tmp_path / "init.php"
    content = """<?php
use Bitrix\\Main\\EventManager;
// Some middleware imports
use Bitrix\\Main\\EventManager as EventManager;

EventManager::getInstance();
"""
    test_php.write_text(content, encoding="utf-8")

    # Run healing
    healed = heal_file(str(test_php))
    assert healed is True

    # Check duplicate import commented out and call resolved to absolute path
    healed_content = test_php.read_text(encoding="utf-8")
    assert "// use Bitrix\\Main\\EventManager as EventManager;" in healed_content
    assert "\\Bitrix\\Main\\EventManager::getInstance();" in healed_content


def test_heal_file_non_existent():
    with pytest.raises(FileNotFoundError):
        heal_file("non_existent_file.php")
