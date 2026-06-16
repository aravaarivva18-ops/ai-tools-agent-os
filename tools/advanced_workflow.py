#!/usr/bin/env python3
"""
Advanced workflow orchestration engine for AI automation agents.
Simplified minimalist version avoiding overengineering.
"""

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def run_workflow(steps: list[Callable[[dict[str, Any]], bool]], context: dict[str, Any]) -> bool:
    """
    Executes a list of step functions sequentially passing a shared context.
    Aborts and returns False on first step failure or uncaught exception.
    """
    for i, step in enumerate(steps):
        step_name = getattr(step, "__name__", f"step_{i}")
        try:
            logger.info("Executing workflow step: %s", step_name)
            success = step(context)
            if not success:
                logger.error("Workflow step failed: %s", step_name)
                return False
        except Exception as e:
            logger.error("Exception in step %s: %s", step_name, e)
            return False
            
    return True
