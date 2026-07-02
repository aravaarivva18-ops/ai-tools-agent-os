import os
import unittest
from unittest.mock import AsyncMock, patch

from tools.mcp_server import apply_patch, mcp, obsidian_log, obsidian_search, run_tests


class TestMcpServer(unittest.TestCase):
    def setUp(self):
        self.orig_env = os.environ.get("AGY_MODE")

    def tearDown(self):
        if self.orig_env is not None:
            os.environ["AGY_MODE"] = self.orig_env
        else:
            os.environ.pop("AGY_MODE", None)

    def test_tools_registered(self):
        """Проверяет, что все 4 инструмента успешно зарегистрированы в FastMCP."""
        import asyncio

        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert "apply_patch" in tool_names
        assert "run_tests" in tool_names
        assert "obsidian_log" in tool_names
        assert "obsidian_search" in tool_names

    @patch("asyncio.create_subprocess_exec")
    def test_apply_patch_success(self, mock_exec):
        """Проверяет успешное применение патча."""
        os.environ["AGY_MODE"] = "patch"
        # Мокаем процесс
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"Patch applied successfully", b"")
        mock_exec.return_value = mock_proc

        # Запускаем асинхронный тест
        import asyncio

        res = asyncio.run(apply_patch("target.py", "patch_text"))

        assert "SUCCESS" in res
        assert "Patch applied successfully" in res
        mock_exec.assert_called_once()

    @patch("asyncio.create_subprocess_exec")
    def test_run_tests_failed(self, mock_exec):
        """Проверяет поведение при падении тестов."""
        os.environ["AGY_MODE"] = "verify"
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"Tests failed", b"Some error output")
        mock_exec.return_value = mock_proc

        import asyncio

        res = asyncio.run(run_tests("test.py", timeout=5))

        assert "TESTS FAILED" in res
        assert "Some error output" in res
        # Проверяем, что таймаут передался в аргументы командной строки
        args = mock_exec.call_args[0]
        assert "--timeout=5" in args

    @patch("asyncio.create_subprocess_exec")
    def test_obsidian_log_success(self, mock_exec):
        """Проверяет успешное логирование в Obsidian."""
        os.environ["AGY_MODE"] = "mcp"
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"Handoff logged into Daily Note", b"")
        mock_exec.return_value = mock_proc

        import asyncio

        res = asyncio.run(obsidian_log("handoff.md", "conv-123"))

        assert "LOGGED SUCCESS" in res
        assert "Handoff logged into Daily Note" in res

    @patch("asyncio.create_subprocess_exec")
    def test_obsidian_search_success(self, mock_exec):
        """Проверяет семантический поиск по Obsidian."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"Found 3 matching notes", b"")
        mock_exec.return_value = mock_proc

        import asyncio

        res = asyncio.run(obsidian_search("YAGNI rules"))

        assert "Found 3 matching notes" in res


if __name__ == "__main__":
    unittest.main()
