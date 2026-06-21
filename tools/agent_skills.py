#!/usr/bin/env python3
"""
Agent Skills Manager.
Coordinates creation of standardized JIT skills, validation of LLM outputs,
and extraction of declarative tool schemas using tool_validator.
"""

import ast
import inspect
import os
import textwrap
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

try:
    from tools.prompt_validator import enforce_anti_clutter
except ImportError:
    try:
        from prompt_validator import enforce_anti_clutter
    except ImportError:
        enforce_anti_clutter = None

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

        # Check if the skill is Business Scaling/Productivity-themed (Dan Martell insights)
        is_scale = any(
            keyword in normalized_name or keyword in description.lower()
            for keyword in [
                "scale",
                "productivity",
                "business",
                "automation",
                "sop",
                "delegate",
                "time",
            ]
        )

        # Check if the skill is SEO/GEO-themed
        is_seo = any(
            keyword in normalized_name or keyword in description.lower()
            for keyword in ["seo", "geo", "traffic", "keywords", "crawler"]
        )

        # Check if the skill is MCP-themed
        is_mcp = any(
            keyword in normalized_name or keyword in description.lower()
            for keyword in ["mcp", "protocol", "model-context"]
        )

        # Check if the skill is UI-themed (for animations, hover, scroll, frontend)
        is_ui = any(
            keyword in normalized_name or keyword in description.lower()
            for keyword in [
                "ui",
                "landing",
                "animation",
                "hover",
                "scroll",
                "frontend",
                "css",
                "web",
            ]
        )

        # Check if the skill is Prototype-themed (throwaway spike)
        is_prototype = any(
            keyword in normalized_name or keyword in description.lower()
            for keyword in [
                "prototype",
                "spike",
                "draft",
                "throwaway",
                "proof-of-concept",
            ]
        )

        # Check if the skill is Grill/Docs-alignment themed
        is_grill = any(
            keyword in normalized_name or keyword in description.lower()
            for keyword in ["grill", "interview", "spec", "docs-align"]
        )

        if is_scale:
            tech_stack = """- **Core Technology**: Python 3.12+ (automation scripts)
- **APIs & Integrations**: Calendar, Email and Tasks APIs (Google Workspace / Microsoft Graph)
- **Time Auditing**: Automatic logging of start/end timestamps and execution cost"""
            design_principles = """- 10-80-10 Rule: Ensure agent implements the core 80% work based on 10% explicit specs, outputting results for human final 10% review.
- DRIP Matrix & SOP: Design autonomous tasks to execute well-defined, low-energy processes via sequential, repeatable scripts.
- Buyback Loop & Time Saved: Log "Time Saved: <number_of_minutes> min" in the final log or HANDOFF.md to trace business buyback rate.
- Pre-delegation Checklist: Define input datasets, expected output schema, and human approval gates before executing the script."""
        elif is_seo:
            tech_stack = """- **Core Technology**: Programmatic SEO (Python / sqlite3 / jinja2)
- **AI Crawler Strategy**: Robots.txt and AI crawlers customization (allow/disallow rules for agents)"""
            design_principles = """- EEAT Signals: Build author biography, credentials, and reference citations.
- GEO Optimization: Citations structure, structured JSON-LD data, and clear FAQ patterns to rank in AI Search Engines (Perplexity, Gemini)."""
        elif is_mcp:
            tech_stack = """- **Core Technology**: Anthropic MCP SDK (Python)
- **Communication Protocol**: JSON-RPC over Standard I/O (stdin/stdout)
- **Minimalist Stack**: SQLite for local persistence (levelsio YAGNI)"""
            design_principles = """- Model Context Protocol: Follow official Anthropic SDK guidelines for tool declaration and schema-driven input validation.
- Karpathy Vibe Coding: Write clean, straightforward Python handlers with max 2 levels of abstraction. Keep logic flat and readable.
- levelsio YAGNI: Reject unnecessary frameworks; use fast stdio/json communication."""
        elif is_ui:
            tech_stack = """- **Core Technology**: HTML, Vanilla JS, Vanilla CSS
- **Animations**: Framer Motion (for hover masks & simple transitions), GSAP (for scroll-tied timelines)
- **3D Elements**: React Three Fiber (R3F) / Three.js (for 3D models like astronauts)
- **CSS Framework**: Tailwind CSS is disabled by default; use Vanilla CSS unless Tailwind is explicitly requested by the user"""
            design_principles = """- Utilize rich aesthetics (gradients, glassmorphism, tailored HSL colors).
- Enforce smooth micro-animations and interactive hover effects.
- Reject static placeholders; design visual layouts using generate_image first."""
        elif is_prototype:
            tech_stack = """- **Core Technology**: Minimal Python 3.12+ (single file) or single-file HTML/JS
- **Data Persistence**: SQLite (in-memory or local file database) or file-based scratch files"""
            design_principles = """- Throwaway Prototyping: Build rapid spikes to test design hypotheses. Reject maintainability and complex architectures.
- Keep it Flat: Max 1 level of abstraction. Write code directly in scratch/ folder without modular overhead.
- Fast Cleanup: No unit tests required for prototypes. Bezжалостно delete or rewrite cleanly with TDD after validation."""
        elif is_grill:
            tech_stack = """- **APIs & MCPs**: Context7 MCP (resolve-library-id -> query-docs on context7.com)
- **Slash Commands**: /grill-me for interactive developer interview"""
            design_principles = """- Docs-First Alignment: Always query context7.com documentation first before generating implementation details.
- Interrogative Strategy: Grill the user on ambiguous requirements. Resolve design decisions and parameters via one-question-at-a-time interview.
- Define Boundaries: Explicitly verify inputs, outputs, assumptions, and developer-saved time (ROI)."""
        else:
            tech_stack = """- **Core Technology**: Python 3.12+ / sqlite3 / FastAPI"""
            design_principles = """- Karpathy Vibe Coding: Always follow clean, simple Python structures. Max 2 levels of abstraction.
- levelsio YAGNI: Restrict architecture to minimalist data schemes. Reject premature abstractions and keep logic flat.
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
        if enforce_anti_clutter:
            enforce_anti_clutter(skill_md_path)
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
        try:
            source = inspect.getsource(func)
            source = textwrap.dedent(source)
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ("invoke_subagent", "define_subagent"):
                        raise ValueError(
                            f"Strict Solo Loop Violation: Forbidden call to '{node.func.id}' found in function '{func.__name__}' source code."
                        )
        except (TypeError, OSError):
            pass

        return generate_tool_schema(func)
