#!/usr/bin/env python3
"""
Agent Skills Manager.
Coordinates creation of standardized JIT skills, validation of LLM outputs,
and extraction of declarative tool schemas using tool_validator.
"""

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel

try:
    from tools.tool_validator import (
        LLMValidationError,
        generate_tool_schema,
        validate_llm_output,
    )
except ImportError:
    from tool_validator import (
        LLMValidationError,
        generate_tool_schema,
        validate_llm_output,
    )

__all__ = ["AgentSkillsManager", "LLMValidationError"]


class AgentSkillsManager:
    """Manages workspace JIT skills and handles their lifecycle and schemas."""

    def __init__(self, workspace_path: str | Path | None = None):
        if workspace_path is None:
            # Fallback to current directory or default path
            self.workspace_root = Path(os.getcwd())
        else:
            self.workspace_root = Path(workspace_path)

        self.skills_dir = self.workspace_root / "skills"

    def create_skill(self, name: str, description: str) -> Path:
        """Creates a standardized JIT skill skeleton under skills/<name>/.

        Args:
            name: Normalized skill folder name (e.g. 'data-extractor').
            description: Short summary of what this skill does.

        Returns:
            Path: Path to the newly created SKILL.md.
        """
        # Normalize name: replace spaces and underscores with dashes
        normalized_name = name.strip().lower().replace("_", "-").replace(" ", "-")
        if not normalized_name:
            raise ValueError("Skill name cannot be empty.")

        skill_folder = self.skills_dir / normalized_name
        skill_folder.mkdir(parents=True, exist_ok=True)

        skill_md_path = skill_folder / "SKILL.md"

        # Check if the skill is UI-themed (for animations, hover, scroll, frontend)
        is_ui = any(
            keyword in normalized_name or keyword in description.lower()
            for keyword in ["ui", "landing", "animation", "hover", "scroll", "frontend", "css", "web"]
        )

        if is_ui:
            tech_stack = """- **Core Technology**: React / Next.js, Tailwind CSS
- **Animations**: Framer Motion (for hover masks & simple transitions), GSAP (for scroll-tied timelines)
- **3D Elements**: React Three Fiber (R3F) / Three.js (for 3D models like astronauts)"""
            design_principles = """- Utilize rich aesthetics (gradients, glassmorphism, tailored HSL colors).
- Enforce smooth micro-animations and interactive hover effects.
- Reject static placeholders; design visual layouts using generate_image first."""
        else:
            tech_stack = """- **Core Technology**: Python 3.12+ / sqlite3 / FastAPI"""
            design_principles = """- Always follow clean, simple Python structures.
- Max 2 levels of abstraction.
- Validate output structure using Pydantic models."""

        # Standardized JIT SKILL template
        template_content = f"""---
name: {normalized_name}
description: {description.strip()}
---

# {name.replace("-", " ").replace("_", " ").title()}

## 🛠️ Stack & Config
{tech_stack}

## 📐 Best Practices & Code Patterns
{design_principles}

## 🔄 Verification Checklist
- [ ] Code is formatted with Ruff.
- [ ] Tests run successfully offline.
"""
        skill_md_path.write_text(template_content, encoding="utf-8")

        # Create scripts, examples and tests placeholders
        if is_ui:
            (skill_folder / "components").mkdir(exist_ok=True)
            (skill_folder / "styles").mkdir(exist_ok=True)
        else:
            (skill_folder / "scripts").mkdir(exist_ok=True)

        (skill_folder / "examples").mkdir(exist_ok=True)
        (skill_folder / "tests").mkdir(exist_ok=True)

        return skill_md_path

    @staticmethod
    def validate_skill_output(data: Any, model_cls: type[BaseModel]) -> BaseModel:
        """Validates skill execution output against a Pydantic BaseModel.

        Wraps validation logic from tool_validator.
        """
        return validate_llm_output(data, model_cls)

    @staticmethod
    def get_skill_tool_schema(func: Callable[..., Any]) -> dict[str, Any]:
        """Generates an OpenAPI/Gemini-compatible Function Declaration from a skill function.

        Wraps declarative schema generator from tool_validator.
        """
        return generate_tool_schema(func)
