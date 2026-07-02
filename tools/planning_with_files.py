#!/usr/bin/env python3
"""
Planning with Files Utility (from planning-with-files pattern).
Manages persistent state on disk using implementation_plan.md to allow
AI agents to recover context after crashes or /clear.
"""

import re
from pathlib import Path
from typing import Any

try:
    from tools.config import get_workspace_root, load_config
except ImportError:
    from config import get_workspace_root, load_config


class PlanningWithFiles:
    """Manages roadmaps, findings, and logs directly on the filesystem for context restoration."""

    def __init__(self, workspace_dir: str | Path | None = None):
        if workspace_dir is None:
            self.workspace_root = get_workspace_root()
        else:
            self.workspace_root = Path(workspace_dir)

        config = load_config()
        findings_rel = config.get("vault", {}).get("findings_file", "vault/findings.md")
        progress_rel = config.get("vault", {}).get(
            "progress_file", str(Path(findings_rel).parent / "progress.md")
        )

        self.plan_path = self.workspace_root / "implementation_plan.md"
        self.findings_path = self.workspace_root / findings_rel
        self.progress_path = self.workspace_root / progress_rel

    def restore_state(self) -> dict[str, Any]:  # noqa: C901
        """Parses implementation_plan.md and progress logs to recover current task state.

        Returns:
            dict: Containing 'title', 'steps', 'completed_steps', 'next_step', 'findings'.
        """
        state: dict[str, Any] = {
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

        # 2. Parse 5-Line Plan or Step List (Robust parsing)
        plan_section = content
        section_match = re.search(
            r"##\s*[^#\n]*(?:план|шаг|step|plan|implementation|ход работы)[^#\n]*(.*?)(?=\n##\s|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if section_match:
            plan_section = section_match.group(1)

        h3_steps = re.findall(r"^###\s+(.+)$", plan_section, re.MULTILINE)
        raw_steps = []
        if h3_steps:
            for h3 in h3_steps:
                h3_clean = h3.strip()
                h3_clean = re.sub(r"^(?:Шаг|Step|Задача|Task)\s*\d+\.?\s*", "", h3_clean, flags=re.IGNORECASE)
                h3_clean = re.sub(r"^\d+\.?\s*", "", h3_clean)
                if h3_clean:
                    raw_steps.append(h3_clean)
        else:
            raw_steps = re.findall(r"^\s*(?:\d+\.|\*|-)\s+(.+)$", plan_section, re.MULTILINE)

        steps = []
        for raw_step in raw_steps:
            clean_step = raw_step.strip()

            name_part = clean_step
            details_part = ""

            bold_colon_match = re.match(r"^\*\*([^*]+)\*\*:\s*(.+)$", clean_step)
            if bold_colon_match:
                name_part = bold_colon_match.group(1).strip()
                details_part = bold_colon_match.group(2).strip()
            else:
                bold_match = re.match(r"^\*\*([^*]+)\*\*$", clean_step)
                if bold_match:
                    name_part = bold_match.group(1).strip()
                else:
                    colon_parts = clean_step.split(":", 1)
                    if len(colon_parts) > 1 and len(colon_parts[0]) < 60:
                        name_part = colon_parts[0].strip()
                        details_part = colon_parts[1].strip()

            step_name = name_part
            name_lower = name_part.lower()
            if details_part and any(kw in name_lower for kw in ["шаг", "задача", "step", "task", "todo"]):
                step_name = details_part

            step_name = step_name.strip()

            if step_name and len(step_name) > 2 and len(step_name) < 200:
                steps.append(step_name)

        state["steps"] = steps



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

        # 6. Semantic search warmup context from past sessions
        if state["title"] and state["title"] != "Unknown Plan":
            try:
                import sys
                from pathlib import Path

                # Add obsidian folder to system path dynamically to avoid import errors
                sys.path.insert(0, str(Path(__file__).parent / "obsidian"))
                import semantic_search

                # Инициализируем векторный поиск только при наличии маркеров глубокого анализа
                title_lower = state["title"].lower()
                need_semantic = any(
                    kw in title_lower
                    for kw in [
                        "avito", "lead", "video", "marketing", "sales",
                        "scrape", "crawl", "audit", "pitch", "post",
                        "copywrite", "humanis", "telegram", "instagram", "аудит"
                    ]
                )

                brief = semantic_search.get_semantic_brief(state["title"], limit=2, semantic=need_semantic)
                if brief and "ℹ️ Релевантных" not in brief and "ℹ️ Быстрый поиск" not in brief:
                    # Write brief automatically to findings.md for agent retrieval
                    self.findings_path.parent.mkdir(parents=True, exist_ok=True)

                    header = "🧠 СЕМАНТИЧЕСКАЯ ПАМЯТЬ: Lessons Learned"
                    content_to_write = f"\n\n### {header}\n{brief.strip()}\n"

                    # Read existing findings to prevent duplicate append
                    existing = ""
                    if self.findings_path.exists():
                        existing = self.findings_path.read_text(encoding="utf-8")

                    if header not in existing:
                        # Append semantic brief to findings
                        with open(self.findings_path, "a", encoding="utf-8") as f:
                            f.write(content_to_write)
                        # Re-read findings to include in state
                        state["findings"] = self.findings_path.read_text(
                            encoding="utf-8"
                        )
            except Exception:
                pass

        # 7. Auto-inject codebase standards and build selective rule context
        try:
            self.optimize_rules()
        except Exception:
            pass

        return state

    def optimize_rules(self) -> None:
        """Запускает оптимизатор правил для компиляции селективного контекста в .agents/AGENTS.md."""
        try:
            from tools.context_optimizer import ContextOptimizer
        except ImportError:
            try:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent))
                from context_optimizer import ContextOptimizer
            except Exception:
                return

        default_rules_dir = self.workspace_root / "vault" / "reference" / "rules"
        optimizer = ContextOptimizer(rules_dir=str(default_rules_dir))
        optimizer.optimize_context(workspace_dir=str(self.workspace_root))

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
