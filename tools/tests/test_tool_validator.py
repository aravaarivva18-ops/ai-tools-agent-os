#!/usr/bin/env python3
"""Tests for Pydantic BaseModel LLM output validator and declarative tool schema generator."""

import time

import pytest
from pydantic import BaseModel, Field
from tool_validator import (
    LLMValidationError,
    generate_tool_schema,
    validate_llm_output,
)


class UserProfile(BaseModel):
    name: str = Field(description="User's full name")
    age: int = Field(description="User's age in years")
    email: str | None = Field(default=None, description="Optional email address")
    skills: list[str] = Field(
        default_factory=list, description="List of technical skills"
    )


def sample_tool(
    username: str, limit: int = 10, tags: list[str] | None = None
) -> list[str]:
    """Retrieves user actions based on criteria.

    Args:
        username: Name of the target user.
        limit: Max actions to return.
        tags: Filter actions by these tags.
    """
    return []


def test_validate_llm_output_success_dict():
    """Tests successful validation from a dictionary representation."""
    start = time.perf_counter()
    data = {
        "name": "Alex",
        "age": 30,
        "email": "alex@example.com",
        "skills": ["python", "go"],
    }
    profile = validate_llm_output(data, UserProfile)
    assert profile.name == "Alex"
    assert profile.age == 30
    assert profile.email == "alex@example.com"
    assert profile.skills == ["python", "go"]
    assert (time.perf_counter() - start) < 0.1


def test_validate_llm_output_success_json_string():
    """Tests successful validation from a raw JSON string."""
    start = time.perf_counter()
    data_str = '{"name": "Bob", "age": 25, "skills": ["javascript"]}'
    profile = validate_llm_output(data_str, UserProfile)
    assert profile.name == "Bob"
    assert profile.age == 25
    assert profile.email is None
    assert profile.skills == ["javascript"]
    assert (time.perf_counter() - start) < 0.1


def test_validate_llm_output_success_markdown_wrapped():
    """Tests successful validation from a Markdown wrapped JSON block."""
    start = time.perf_counter()
    markdown_str = """
    ```json
    {
        "name": "Charlie",
        "age": 42,
        "skills": ["c++"]
    }
    ```
    """
    profile = validate_llm_output(markdown_str, UserProfile)
    assert profile.name == "Charlie"
    assert profile.age == 42
    assert profile.skills == ["c++"]
    assert (time.perf_counter() - start) < 0.1


def test_validate_llm_output_already_model():
    """Tests validation when input is already a Pydantic model instance."""
    start = time.perf_counter()
    original = UserProfile(name="Dave", age=35, skills=["rust"])
    profile = validate_llm_output(original, UserProfile)
    assert profile is original
    assert (time.perf_counter() - start) < 0.1


def test_validate_llm_output_invalid_json():
    """Tests validation error for syntactically invalid JSON string."""
    start = time.perf_counter()
    invalid_json = (
        '{"name": "Bob", "age": 25, "skills": ["javascript"'  # missing closing brace
    )
    with pytest.raises(LLMValidationError) as exc_info:
        validate_llm_output(invalid_json, UserProfile)
    assert "Failed to parse LLM output as JSON" in str(exc_info.value)
    assert (time.perf_counter() - start) < 0.1


def test_validate_llm_output_validation_failure():
    """Tests validation failure due to missing required fields or type mismatches."""
    start = time.perf_counter()
    # Missing required field 'name'
    invalid_data = {"age": 25, "skills": ["python"]}
    with pytest.raises(LLMValidationError) as exc_info:
        validate_llm_output(invalid_data, UserProfile)
    assert "Pydantic validation failed" in str(exc_info.value)
    assert (time.perf_counter() - start) < 0.1


def test_generate_tool_schema():
    """Tests schema generation from function annotations and docstring."""
    start = time.perf_counter()
    schema = generate_tool_schema(sample_tool)

    assert schema["name"] == "sample_tool"
    assert "Retrieves user actions" in schema["description"]

    params = schema["parameters"]
    assert params["type"] == "OBJECT"

    props = params["properties"]
    assert props["username"]["type"] == "STRING"
    assert props["username"]["description"] == "Name of the target user."

    assert props["limit"]["type"] == "INTEGER"
    assert props["limit"]["description"] == "Max actions to return."

    assert props["tags"]["type"] == "ARRAY"
    assert props["tags"]["items"]["type"] == "STRING"
    assert props["tags"]["description"] == "Filter actions by these tags."

    # Required params should only be 'username'
    # limit has default 10, tags is Optional
    assert params["required"] == ["username"]

    assert (time.perf_counter() - start) < 0.1
