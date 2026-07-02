#!/usr/bin/env python3
"""
Pydantic BaseModel LLM output validator and declarative tool schema generator.
Provides clean validation and Agno-style schema generation under 2 levels of abstraction.
"""

import inspect
import logging
import re
import typing
from collections.abc import Callable
from typing import Any, TypeVar, get_args, get_origin

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMValidationError(Exception):
    """Raised when LLM output parsing or validation fails."""

    pass


def validate_llm_output(data: Any, model_cls: type[T]) -> T:  # noqa: UP047
    """Parses and validates LLM response JSON to a Pydantic model.

    Args:
        data: Raw string output from LLM, dictionary, or existing BaseModel.
        model_cls: Target Pydantic model class.

    Returns:
        Instance of model_cls.

    Raises:
        LLMValidationError: If JSON formatting or validation fails.
    """
    if isinstance(data, model_cls):
        return data

    if isinstance(data, dict):
        try:
            return model_cls.model_validate(data)
        except ValidationError as e:
            raise LLMValidationError(f"Pydantic validation failed: {e}") from e

    if not isinstance(data, str):
        raise LLMValidationError(f"Unsupported data type for validation: {type(data)}")

    # Clean potential Markdown codeblock wrapping (e.g. ```json ... ```)
    clean_data = data.strip()
    if clean_data.startswith("```"):
        match = re.match(
            r"^```(?:json)?\s*(.*?)\s*```$", clean_data, re.DOTALL | re.IGNORECASE
        )
        if match:
            clean_data = match.group(1).strip()

    try:
        from tools.json_utils import safe_load_json
        parsed_dict = safe_load_json(clean_data)
        if parsed_dict is None or not isinstance(parsed_dict, (dict, list)):
            raise ValueError("Parsed JSON is not an object or array")
    except Exception as e:
        raise LLMValidationError(
            f"Failed to parse LLM output as JSON (even after repair attempt): {e}. Output was: {data}"
        ) from e

    try:
        return model_cls.model_validate(parsed_dict)
    except ValidationError as e:
        raise LLMValidationError(
            f"Pydantic validation failed for parsed JSON: {e}"
        ) from e


def _unwrap_union(annot: Any) -> Any:
    """Unwraps Optional and Union types to return the core non-None type."""
    origin = get_origin(annot)
    if origin is typing.Union or str(origin) == "types.UnionType":
        args = get_args(annot)
        non_none_args = [a for a in args if a is not type(None)]
        if non_none_args:
            return non_none_args[0]
    return annot


def _get_json_type(annot: Any) -> str:
    """Maps a Python type/annotation to OpenAPI JSON Schema type name."""
    unwrapped = _unwrap_union(annot)
    origin = get_origin(unwrapped)

    if unwrapped is str:
        return "STRING"
    elif unwrapped is int:
        return "INTEGER"
    elif unwrapped is float:
        return "NUMBER"
    elif unwrapped is bool:
        return "BOOLEAN"
    elif unwrapped is list or origin is list or origin is list:
        return "ARRAY"
    elif unwrapped is dict or origin is dict or origin is dict:
        return "OBJECT"
    return "STRING"


def parse_docstring(docstring: str | None) -> tuple[str, dict[str, str]]:
    """Extracts summary and parameters descriptions from function docstring.

    Supports simple list, Sphinx (:param:), and Google styles.
    """
    if not docstring:
        return "", {}

    lines = [line.strip() for line in docstring.split("\n")]
    summary = lines[0] if lines else ""

    params = {}
    current_param = None
    in_args_section = False

    for line in lines:
        if not line:
            continue

        lower_line = line.lower()
        if lower_line.startswith("args:") or lower_line.startswith("parameters:"):
            in_args_section = True
            continue

        if in_args_section:
            if ":" in line:
                parts = line.split(":", 1)
                name_part = parts[0].strip()
                # strip type info e.g. "param (str)"
                param_name = name_part.split("(")[0].strip()
                if param_name.isidentifier():
                    params[param_name] = parts[1].strip()
                    current_param = param_name
            elif current_param and (
                line.startswith("    ")
                or line.startswith("\t")
                or not line.startswith("-")
            ):
                params[current_param] += " " + line.strip()
        else:
            if line.startswith(":param "):
                content = line[7:]
                if ":" in content:
                    param_part, desc = content.split(":", 1)
                    param_name = param_part.strip().split()[-1]
                    params[param_name] = desc.strip()
                    current_param = param_name
            elif current_param and (line.startswith("    ") or line.startswith("\t")):
                params[current_param] += " " + line.strip()

    return summary, params


def generate_tool_schema(func: Callable[..., Any]) -> dict[str, Any]:
    """Generates an OpenAPI/Gemini-compatible Function Declaration from a Python function.

    Args:
        func: Python function to declare.

    Returns:
        Declarative schema dictionary.
    """
    sig = inspect.signature(func)
    summary, doc_params = parse_docstring(func.__doc__)

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        unwrapped_annot = _unwrap_union(param.annotation)
        param_desc = doc_params.get(param_name, "")

        # Поддержка Pydantic моделей в сигнатуре
        if inspect.isclass(unwrapped_annot) and issubclass(unwrapped_annot, BaseModel):
            param_type = "OBJECT"
            prop_def = {
                "type": "OBJECT",
                "description": param_desc or unwrapped_annot.__doc__ or "",
                "properties": {},
            }
            for field_name, field in unwrapped_annot.model_fields.items():
                field_type = _get_json_type(field.annotation)
                f_def = {"type": field_type}
                if field.description:
                    f_def["description"] = field.description
                prop_def["properties"][field_name] = f_def
        else:
            param_type = _get_json_type(unwrapped_annot)
            prop_def = {"type": param_type}
            if param_desc:
                prop_def["description"] = param_desc

        # Check if Optional (Union with None)
        is_optional = False
        origin = get_origin(param.annotation)
        if origin is typing.Union or str(origin) == "types.UnionType":
            args = get_args(param.annotation)
            if type(None) in args:
                is_optional = True

        if param.default is inspect.Parameter.empty and not is_optional:
            required.append(param_name)

        if param_type == "ARRAY":
            args = get_args(unwrapped_annot)
            if args:
                item_type = _get_json_type(args[0])
                prop_def["items"] = {"type": item_type}
            else:
                prop_def["items"] = {"type": "STRING"}

        properties[param_name] = prop_def

    schema: dict[str, Any] = {
        "name": func.__name__,
        "description": summary or func.__doc__ or "",
        "parameters": {
            "type": "OBJECT",
            "properties": properties,
        },
    }
    if required:
        schema["parameters"]["required"] = required

    return schema
