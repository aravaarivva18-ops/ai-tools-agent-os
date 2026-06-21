#!/usr/bin/env python3
"""
Solo Loop v10 Engine.
Orchestrates context recovery, error loop checking, and log compression
to prevent context bloat and ensure crash-proof planning.
"""

import os
from pathlib import Path
from typing import Any

try:
    from tools.planning_with_files import PlanningWithFiles
except ImportError:
    from planning_with_files import PlanningWithFiles


class SoloLoopV10:
    """Core Orchestrator for Solo Loop v10 execution cycle."""

    def __init__(self, workspace_path: str | Path | None = None):
        if workspace_path is None:
            self.workspace_root = Path(os.getcwd())
        else:
            self.workspace_root = Path(workspace_path)

        self.planner = PlanningWithFiles(self.workspace_root)
        self.error_registry = {}  # Tracks error_message -> count
        self.stealth_stop_triggered = False

    def startup_restore(self) -> dict[str, Any]:
        """Restores session state on startup from implementation_plan.md.

        Returns:
            dict: The recovered state from disk.
        """
        state = self.planner.restore_state()
        return state

    def track_execution(
        self, command: str, success: bool, output: str
    ) -> dict[str, Any]:
        """Processes command output, checks for loop cycles, and compresses logs.

        Args:
            command: The command that was executed.
            success: Whether it succeeded.
            output: The raw console stdout/stderr.

        Returns:
            dict: Containing 'success', 'compressed_output', 'stealth_stop'.
        """
        result = {
            "success": success,
            "compressed_output": output,
            "stealth_stop": False,
        }

        if success:
            # Succeeded: Compress log to remove noise
            result["compressed_output"] = self.compress_log(output)
            # Clear error registry since progress was made
            self.error_registry.clear()
        else:
            # Failed: Detect loop cycles
            error_sig = self._extract_error_signature(output)
            self.error_registry[error_sig] = self.error_registry.get(error_sig, 0) + 1

            # Stealth Stop triggered on 3 identical failures
            if self.error_registry[error_sig] >= 3:
                self.stealth_stop_triggered = True
                result["stealth_stop"] = True
                result["compressed_output"] = (
                    f"[STEALTH STOP] Идентичная ошибка повторилась 3 раза при запуске '{command}'.\n"
                    f"Суть ошибки:\n{error_sig}\n"
                    "Остановка сессии для предотвращения зацикливания контекста."
                )
            else:
                # Compress the traceback log to keep context clean
                result["compressed_output"] = self.compress_log(output, is_error=True)

        return result

    def compress_log(
        self, text: str, max_lines: int = 30, is_error: bool = False
    ) -> str:
        """Trims output log to keep only the most critical lines (Headroom concept)."""
        if not text:
            return ""

        lines = text.splitlines()
        if len(lines) <= max_lines:
            return text

        if is_error:
            # If error, try to prioritize lines with error markers (e.g. 'E ', '>', 'FAIL', 'Error')
            critical_lines = []
            for line in lines:
                if any(
                    marker in line
                    for marker in (
                        "E ",
                        ">",
                        "FAIL:",
                        "Error:",
                        "Traceback",
                        "Exception",
                    )
                ):
                    critical_lines.append(line)
            if len(critical_lines) > 5:
                return (
                    "\n".join(critical_lines[:max_lines])
                    + "\n... [Логи обрезаны для экономии контекста] ..."
                )

        # Fallback to head + tail compression
        half = max_lines // 2
        head = lines[:half]
        tail = lines[-half:]
        return (
            "\n".join(head)
            + "\n... [Логи обрезаны для экономии контекста] ...\n"
            + "\n".join(tail)
        )

    def _extract_error_signature(self, text: str) -> str:
        """Helper to extract a unique signature from traceback/error log."""
        # Find lines starting with 'E ' or 'FAIL:' or 'Error:'
        sig_lines = []
        for line in text.splitlines():
            clean = line.strip()
            if (
                clean.startswith("E ")
                or clean.startswith("FAIL:")
                or clean.startswith("Error:")
                or "Exception" in clean
            ):
                sig_lines.append(clean)

        if sig_lines:
            return "\n".join(sig_lines)

        # Fallback to last 3 lines if no matches
        return "\n".join(
            [line.strip() for line in text.splitlines()[-3:] if line.strip()]
        )
