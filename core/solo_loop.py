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
    from planning_with_files import PlanningWithFiles  # type: ignore[no-redef]


class SoloLoopV10:
    """Core Orchestrator for Solo Loop v10 execution cycle."""

    def __init__(self, workspace_path: str | Path | None = None):
        if workspace_path is None:
            self.workspace_root = Path(os.getcwd())
        else:
            self.workspace_root = Path(workspace_path)

        self.planner = PlanningWithFiles(self.workspace_root)
        self.error_registry: dict[str, int] = {}  # Tracks error_message -> count
        self.stealth_stop_triggered = False

    def startup_restore(self) -> dict[str, Any]:
        """Restores session state on startup from implementation_plan.md.

        Returns:
            dict: The recovered state from disk.
        """
        state = self.planner.restore_state()
        return state

    def compact_context(self, history_steps: list[dict[str, Any]], max_tokens: int = 2000) -> dict[str, Any]:
        """Summarizes history steps and cleans up detailed logs using Exact Token Compression.

        Args:
            history_steps: A list of dicts with 'command', 'success', 'output'.
            max_tokens: Maximum allowed tokens for the history block.

        Returns:
            dict: Containing 'summary_text', 'cleaned_steps'.
        """
        if not history_steps:
            return {"summary_text": "No history to compact.", "cleaned_steps": []}

        try:
            from tools.context_utils import count_tokens_exact
        except ImportError:
            def count_tokens_exact(text: str, *_args: Any, **_kwargs: Any) -> int:
                return len(text) // 4

        successful_commands = []
        failed_commands = []
        unique_errors = set()
        cleaned_steps = []

        for step in history_steps:
            cmd = step.get("command", "unknown")
            success = step.get("success", False)
            output = step.get("output", "")

            # Clean up output using compress_log to reduce token usage
            compressed_output = self.compress_log(
                output, max_lines=5, is_error=not success
            )

            cleaned_steps.append(
                {"command": cmd, "success": success, "output": compressed_output}
            )

            if success:
                successful_commands.append(cmd)
            else:
                failed_commands.append(cmd)
                err_sig = self._extract_error_signature(output)
                if err_sig:
                    unique_errors.add(err_sig)

        # Фаза 1: Сжимаем успешные шаги, если превышен лимит
        def calc_total_tokens(steps_list):
            return sum(count_tokens_exact(s["command"]) + count_tokens_exact(s["output"]) for s in steps_list)

        if calc_total_tokens(cleaned_steps) > max_tokens:
            for step in cleaned_steps:
                if calc_total_tokens(cleaned_steps) <= max_tokens:
                    break
                if step["success"] and step["output"] != "[success output trimmed]":
                    step["output"] = "[success output trimmed]"

        # Фаза 2: Удаляем старые шаги, если все еще превышен лимит (но не трогаем последний шаг)
        while len(cleaned_steps) > 1 and calc_total_tokens(cleaned_steps) > max_tokens:
            cleaned_steps.pop(0)

        # Build a concise summary text
        summary_parts = []
        if successful_commands:
            summary_parts.append(
                f"Successfully executed: {', '.join(successful_commands)}"
            )
        if failed_commands:
            summary_parts.append(f"Failed commands: {', '.join(failed_commands)}")
        if unique_errors:
            summary_parts.append("Distinct errors encountered:")
            for err in unique_errors:
                summary_parts.append(f"- {err}")

        summary_text = "\n".join(summary_parts)

        return {"summary_text": summary_text, "cleaned_steps": cleaned_steps}

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
