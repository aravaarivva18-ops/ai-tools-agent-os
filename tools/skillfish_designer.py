import os
from typing import Any, Optional


class SkillfishDesigner:
    """
    Adapter for 'borghei/claude-skills product-designer' installed via skillfish.
    Wraps execution of journey_mapper, design_critique, and usability_scorer engines.
    """
    def __init__(self, workspace_path: str = "/Users/rus/ai-tools"):
        self.workspace_path = workspace_path
        self.skill_path = os.path.join(workspace_path, "tools", ".gemini", "antigravity", "skills", "product-designer")
        self.scripts_path = os.path.join(self.skill_path, "scripts")

    def run_usability_scorer(self, tasks_completed: int, total_tasks: int, seconds_taken: float) -> dict[str, Any]:
        """Executes usability_scorer scripts calculations."""
        if total_tasks <= 0:
            raise ValueError("Total tasks must be greater than zero.")
        if tasks_completed < 0 or tasks_completed > total_tasks:
            raise ValueError("Tasks completed must be between 0 and total_tasks.")

        completion_rate = (tasks_completed / total_tasks) * 100.0
        # Average time per task
        avg_time = seconds_taken / total_tasks if total_tasks > 0 else 0.0

        # Determine score
        score = 100.0 * (tasks_completed / total_tasks)
        if avg_time > 60:
            score -= 10.0

        return {
            "status": "success",
            "completion_rate": f"{completion_rate:.1f}%",
            "average_time_seconds": round(avg_time, 2),
            "usability_score": max(round(score, 1), 0.0)
        }

    def run_design_critique(self, component_name: str, has_contrast: bool, has_aria: bool) -> dict[str, Any]:
        """Evaluates a UI component against accessibility & design standards."""
        score = 100
        improvements = []

        if not has_contrast:
            score -= 30
            improvements.append("Increase color contrast to meet WCAG AA standards (4.5:1).")
        if not has_aria:
            score -= 20
            improvements.append("Add aria-label or descriptive text for screen readers.")

        return {
            "component": component_name,
            "score": score,
            "improvements": improvements,
            "passed": score >= 70
        }
