#!/usr/bin/env python3
"""
Planning with Files Utility (from planning-with-files pattern).
Manages persistent state on disk using implementation_plan.md to allow
AI agents to recover context after crashes or /clear.
"""

import os
import re
from pathlib import Path
from typing import Any


class PlanningWithFiles:
    """Manages roadmaps, findings, and logs directly on the filesystem for context restoration."""

    def __init__(self, workspace_dir: str | Path | None = None):
        if workspace_dir is None:
            self.workspace_root = Path(os.getcwd())
        else:
            self.workspace_root = Path(workspace_dir)

        self.plan_path = self.workspace_root / "implementation_plan.md"
        self.findings_path = self.workspace_root / "vault" / "findings.md"
        self.progress_path = self.workspace_root / "vault" / "progress.md"

    def restore_state(self) -> dict[str, Any]:
        """Parses implementation_plan.md and progress logs to recover current task state.

        Returns:
            dict: Containing 'title', 'steps', 'completed_steps', 'next_step', 'findings'.
        """
        state = {
            "title": "Unknown Plan",
            "steps": [],
            "completed_steps": [],
            "next_step": None,
            "findings": "",
        }

        if not self.plan_path.exists():
            return state

        content = self.plan_path.read_text(encoding="utf-8")

        # 1. Parse Title
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            state["title"] = title_match.group(1).strip()

        # 2. Parse 5-Line Plan or Step List
        # Look for numbered lines in 5. Пошаговый план (5-Line Plan) or similar lists
        step_matches = re.findall(
            r"^\d+\.\s+\*\*([^*]+)\*\*:\s*(.+)$", content, re.MULTILINE
        )
        if not step_matches:
            # Fallback to general numbered list in the plan section
            step_matches = re.findall(r"^\s*\d+\.\s+(.+)$", content, re.MULTILINE)

        state["steps"] = [
            step[1].strip() if isinstance(step, tuple) else step.strip()
            for step in step_matches
        ]

        # 3. Read findings if present
        if self.findings_path.exists():
            state["findings"] = self.findings_path.read_text(encoding="utf-8")

        # 4. Parse progress log to see what has been completed
        if self.progress_path.exists():
            progress_content = self.progress_path.read_text(encoding="utf-8")
            # Look for matches like "[x] Step Name" or "Completed: Step Name"
            completed = re.findall(r"\[x\]\s*(.+)$", progress_content, re.MULTILINE)
            state["completed_steps"] = [c.strip() for c in completed]

        # 5. Determine the next step
        for step in state["steps"]:
            # Check if this step is already completed
            is_done = False
            for comp in state["completed_steps"]:
                if step.lower() in comp.lower() or comp.lower() in step.lower():
                    is_done = True
                    break
            if not is_done:
                state["next_step"] = step
                break

        return state

    def record_progress(
        self, step_name: str, status: str, details: str | None = None
    ) -> None:
        """Records progress log on the filesystem.

        Args:
            step_name: The name of the step.
            status: e.g. 'completed', 'failed', 'in-progress'.
            details: Optional details.
        """
        self.progress_path.parent.mkdir(parents=True, exist_ok=True)

        # Append progress log
        marker = "[x]" if status == "completed" else "[-]"
        log_entry = f"{marker} {step_name} - {status.upper()}"
        if details:
            log_entry += f" ({details})"

        with open(self.progress_path, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def record_finding(self, header: str, content: str) -> None:
        """Appends new research finding or error log to findings.md."""
        self.findings_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.findings_path, "a", encoding="utf-8") as f:
            f.write(f"\n### {header}\n{content.strip()}\n")
