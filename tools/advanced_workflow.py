#!/usr/bin/env python3
"""
Advanced workflow orchestration engine for AI automation agents.
Implements dependency graphs, context management, and branching execution.
"""

from collections.abc import Callable
from typing import Any



class WorkflowContext:
    """Manages the state and variables passed between execution steps."""
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)


class StepResult:
    """Represents the execution outcome of a workflow step."""
    def __init__(self, success: bool, message: str = "") -> None:
        self.success = success
        self.message = message


class StepDefinition:
    """Defines a workflow step, its code logic and dependency relationships."""
    def __init__(
        self,
        name: str,
        func: Callable[[WorkflowContext], StepResult],
        depends_on: list[str] | None = None,
    ) -> None:
        self.name = name
        self.func = func
        self.depends_on = depends_on or []


class AdvancedWorkflow:
    """Orchestrates sequential, parallel and conditional steps based on dependencies."""
    def __init__(self) -> None:
        self.context = WorkflowContext()
        self.steps: dict[str, StepDefinition] = {}
        self.skipped_steps: set[str] = set()

    def step(self, name: str, depends_on: list[str] | None = None) -> Callable:
        """Decorator to register a workflow step."""
        def decorator(func: Callable[[WorkflowContext], StepResult]) -> Callable:
            self.steps[name] = StepDefinition(name, func, depends_on)
            return func
        return decorator

    def run(self) -> dict[str, StepResult]:
        """Runs the registered steps while resolving dependencies in topological order."""
        executed: dict[str, StepResult] = {}
        self.skipped_steps.clear()

        # Simple resolution loop
        while len(executed) + len(self.skipped_steps) < len(self.steps):
            progressed = False
            for name, step_def in self.steps.items():
                if name in executed or name in self.skipped_steps:
                    continue

                # Check if all dependencies have run successfully
                all_deps_resolved = True
                dep_failed = False
                for dep in step_def.depends_on:
                    if dep in self.skipped_steps:
                        dep_failed = True
                        break
                    elif dep not in executed:
                        all_deps_resolved = False
                        break
                    elif not executed[dep].success:
                        dep_failed = True
                        break

                if dep_failed:
                    self.skipped_steps.add(name)
                    progressed = True
                elif all_deps_resolved:
                    try:
                        result = step_def.func(self.context)
                        executed[name] = result
                    except Exception as e:
                        executed[name] = StepResult(success=False, message=str(e))
                    progressed = True

            if not progressed:
                # Circular dependency or missing dependency detected
                break

        return executed
