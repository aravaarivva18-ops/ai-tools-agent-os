import json
import pathlib
import sys
import tempfile
from unittest import mock

import pytest

from tools import cli


@pytest.fixture(autouse=True)
def mock_license_check():
    """Автоматически мокирует проверку лицензии для всех тестов CLI."""
    with mock.patch("tools.cli.enforce_license") as mock_enforce:
        yield mock_enforce


def test_cli_init_positive():
    """Позитивный тест: успешно создает .agentic-dev.json, если его нет."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        # Мокаем get_workspace_root, чтобы возвращал временную директорию
        with mock.patch("tools.cli.config.get_workspace_root", return_value=tmp_path):
            # Мокаем sys.exit, так как cmd_init не вызывает его при успехе (или выходит без ошибок)
            # В cmd_init при успешном создании файла нет sys.exit, выполнение завершается штатно
            class Args:
                force = False

            cli.cmd_init(Args())

            config_file = tmp_path / ".agentic-dev.json"
            assert config_file.exists()
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)
                assert data["version"] == "1.0.0"


def test_cli_init_negative_no_overwrite():
    """Негативный тест: не перезаписывает файл без флага force."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        config_file = tmp_path / ".agentic-dev.json"
        config_file.write_text('{"version": "old"}', encoding="utf-8")

        with mock.patch("tools.cli.config.get_workspace_root", return_value=tmp_path):

            class Args:
                force = False

            # Должен выйти с exit code 0 через sys.exit(0)
            with pytest.raises(SystemExit) as excinfo:
                cli.cmd_init(Args())

            assert excinfo.value.code == 0
            # Содержимое файла не должно измениться
            assert config_file.read_text(encoding="utf-8") == '{"version": "old"}'


def test_cli_init_force_overwrite():
    """Позитивный тест: перезаписывает файл при флаге force."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        config_file = tmp_path / ".agentic-dev.json"
        config_file.write_text('{"version": "old"}', encoding="utf-8")

        with mock.patch("tools.cli.config.get_workspace_root", return_value=tmp_path):

            class Args:
                force = True

            cli.cmd_init(Args())

            # Файл должен перезаписаться
            assert "1.0.0" in config_file.read_text(encoding="utf-8")


@mock.patch("subprocess.run")
def test_cli_run_pass_args(mock_run):
    """Позитивный тест: команда run корректно запускает test_healer.py с аргументами."""
    mock_run.return_value = mock.MagicMock(returncode=0)

    test_args = ["cli.py", "run", "some_test.py", "--target", "some_file.py"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            cli.main()

        assert excinfo.value.code == 0
        mock_run.assert_called_once()
        args_called = mock_run.call_args[0][0]
        assert "test_healer.py" in args_called[1]
        assert "some_test.py" in args_called
        assert "--target" in args_called
        assert "some_file.py" in args_called


@mock.patch("subprocess.run")
def test_cli_search_pass_args(mock_run):
    """Позитивный тест: команда search корректно запускает semantic_search.py с аргументами."""
    mock_run.return_value = mock.MagicMock(returncode=0)

    test_args = ["cli.py", "search", "my query", "--limit", "5"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            cli.main()

        assert excinfo.value.code == 0
        mock_run.assert_called_once()
        args_called = mock_run.call_args[0][0]
        assert "semantic_search.py" in args_called[1]
        assert "my query" in args_called
        assert "--limit" in args_called


@mock.patch("subprocess.run")
def test_cli_build_pass_args(mock_run):
    """Позитивный тест: команда build корректно запускает build_release.py с аргументами."""
    mock_run.return_value = mock.MagicMock(returncode=0)

    test_args = ["cli.py", "build", "--out", "my_release.zip"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            cli.main()

        assert excinfo.value.code == 0
        mock_run.assert_called_once()
        args_called = mock_run.call_args[0][0]
        assert "build_release.py" in args_called[1]
        assert "--out" in args_called
        assert "my_release.zip" in args_called


@mock.patch("subprocess.run")
def test_cli_test_all(mock_run):
    """Позитивный тест: agy test --all запускает все тесты во всех модулях."""
    mock_run.return_value = mock.MagicMock(returncode=0)

    test_args = ["cli.py", "test", "--all"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            cli.main()

        assert excinfo.value.code == 0
        mock_run.assert_called_once()
        args_called = mock_run.call_args[0][0]
        assert "pytest" in args_called[0]
        assert any("tools/tests" in arg for arg in args_called)
        assert any("geo-seo/tests" in arg for arg in args_called)


@mock.patch("tools.test_healer.detect_tests_from_diff")
def test_cli_test_diff_no_changes(mock_detect):
    """Позитивный тест: agy test завершается без запуска тестов, если изменений нет."""
    mock_detect.return_value = []

    test_args = ["cli.py", "test"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            cli.main()

        assert excinfo.value.code == 0
        mock_detect.assert_called_once()


@mock.patch("subprocess.run")
@mock.patch("tools.test_healer.detect_tests_from_diff")
def test_cli_test_diff_with_changes(mock_detect, mock_run):
    """Позитивный тест: agy test запускает тесты только на измененных файлах."""
    mock_detect.return_value = ["/path/to/test_some.py"]
    mock_run.return_value = mock.MagicMock(returncode=0)

    test_args = ["cli.py", "test"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            cli.main()

        assert excinfo.value.code == 0
        mock_detect.assert_called_once()
        mock_run.assert_called_once()
        args_called = mock_run.call_args[0][0]
        assert "/path/to/test_some.py" in args_called


def test_cli_fast():
    """Тест команды agy fast."""
    test_args = ["cli.py", "fast", "Hello Fast"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            cli.main()
        assert excinfo.value.code == 0


def test_cli_deep():
    """Тест команды agy deep."""
    # Замокаем global_search, чтобы не грузить реальные RAG-базы во время тестов
    with mock.patch("tools.knowledge.search.global_search", return_value="Some RAG context") as mock_gsearch:
        test_args = ["cli.py", "deep", "Hello Deep"]
        with mock.patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as excinfo:
                cli.main()
            assert excinfo.value.code == 0
            mock_gsearch.assert_called_once_with("Hello Deep")


def test_cli_ask_default():
    """Тест команды agy ask без флагов (по умолчанию перенаправляет в fast)."""
    test_args = ["cli.py", "ask", "Hello Ask"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            cli.main()
        assert excinfo.value.code == 0


def test_cli_ask_auto_fast():
    """Тест команды agy ask с --auto (выбирает fast для короткого простого запроса)."""
    test_args = ["cli.py", "ask", "Hello", "--auto"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            cli.main()
        assert excinfo.value.code == 0


def test_cli_ask_auto_deep():
    """Тест команды agy ask с --auto (выбирает deep для сложного запроса с ключевыми словами)."""
    with mock.patch("tools.knowledge.search.global_search", return_value="Mock RAG") as mock_gsearch:
        # "поиск" — ключевое слово, перенаправляющее в deep
        test_args = ["cli.py", "ask", "поиск rust", "--auto"]
        with mock.patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as excinfo:
                cli.main()
            assert excinfo.value.code == 0
            mock_gsearch.assert_called_once_with("поиск rust")
