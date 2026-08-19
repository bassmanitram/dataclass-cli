"""
Test suite for build_config_from_dict() function.

Tests the new convenience function that builds dataclass instances from dictionaries
without CLI involvement.
"""

import os
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest

from dataclass_args import (
    build_config_from_dict,
    cli_exclude,
    cli_file_loadable,
    cli_help,
    cli_nested,
    cli_resolve,
)
from dataclass_args.exceptions import ConfigurationError


@pytest.fixture
def temp_text_file():
    """Create a temporary text file with content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello, World! This is test content.")
        fname = f.name
    yield fname
    os.unlink(fname)


# ============================================================================
# Test Classes
# ============================================================================


@dataclass
class SimpleConfig:
    """Simple dataclass for basic field tests. All fields have defaults for testing."""

    name: str = "default_name"
    count: int = 10
    temperature: float = 0.5
    debug: bool = False


@dataclass
class SimpleConfigWithRequired:
    """Simple dataclass with required field for testing error cases."""

    name: str  # Required field
    count: int = 10
    temperature: float = 0.5
    debug: bool = False


@dataclass
class FileLoadableConfig:
    """Config with cli_file_loadable field."""

    message: str = cli_file_loadable()
    prefix: str = "Default:"


@dataclass
class NestedChildConfig:
    """Child dataclass for nested testing."""

    retry_count: int = 3
    timeout: int = 30


@dataclass
class NestedConfig:
    """Config with nested dataclass field."""

    app_name: str = "MyApp"
    wrapper: NestedChildConfig = cli_nested(
        prefix="wrap", default_factory=NestedChildConfig
    )


def resolve_custom_type(value: Any) -> str:
    """Resolver function for testing cli_resolve."""
    if isinstance(value, dict):
        return f"Resolved: {value.get('type', 'unknown')}"
    return f"Direct: {value}"


@dataclass
class ResolverConfig:
    """Config with cli_resolve field."""

    backend: str = cli_resolve(resolver=resolve_custom_type, default="default")


@dataclass
class ExcludedConfig:
    """Config with cli_exclude field."""

    visible_field: str = "visible"
    hidden_field: str = cli_exclude(default="excluded_default")


@dataclass
class AllDefaultsConfig:
    """Config where ALL fields have defaults - for empty dict testing."""

    name: str = "full_defaults"
    count: int = 100
    enabled: bool = True


# ============================================================================
# Tests
# ============================================================================


def test_simple_scalar_fields():
    """Test that basic scalar fields pass through correctly."""
    config_dict = {
        "name": "test_app",
        "count": 42,
        "temperature": 0.7,
        "debug": True,
    }

    result = build_config_from_dict(SimpleConfig, config_dict)

    assert result.name == "test_app"
    assert result.count == 42
    assert result.temperature == 0.7
    assert result.debug is True


def test_fields_with_defaults():
    """Test that fields with defaults work when omitted from dict."""
    config_dict = {
        "name": "test_app",
        # count, temperature, debug omitted - should use defaults
    }

    result = build_config_from_dict(SimpleConfig, config_dict)

    assert result.name == "test_app"
    assert result.count == 10
    assert result.temperature == 0.5
    assert result.debug is False


def test_empty_dict_uses_all_defaults():
    """Test that empty dict works when ALL fields have defaults."""
    result = build_config_from_dict(AllDefaultsConfig, {})

    # All fields should use their defaults
    assert result.name == "full_defaults"
    assert result.count == 100
    assert result.enabled is True


def test_required_field_missing_raises_error():
    """Test that missing required field raises appropriate error."""
    config_dict = {
        # name field is required and missing
        "count": 20,
    }

    # This should fail because 'name' is required
    with pytest.raises(Exception):  # Will be ConfigurationError or similar
        build_config_from_dict(SimpleConfigWithRequired, config_dict)


def test_nested_dataclass_with_flat_fields():
    """Test that nested dataclass works with flat field access."""
    config_dict = {
        "app_name": "TestApp",
        "wrapper": {"retry_count": 5, "timeout": 90},  # Use nested dict format
    }

    result = build_config_from_dict(NestedConfig, config_dict)

    assert result.app_name == "TestApp"
    assert result.wrapper.retry_count == 5
    assert result.wrapper.timeout == 90


def test_nested_config_with_default():
    """Test nested dataclass using defaults."""
    config_dict = {
        "app_name": "DefaultConfig",
        # wrapper omitted - should use default from default_factory
    }

    result = build_config_from_dict(NestedConfig, config_dict)

    assert result.app_name == "DefaultConfig"
    assert result.wrapper.retry_count == 3  # default
    assert result.wrapper.timeout == 30  # default


def test_resolver_function_applied():
    """Test that cli_resolve fields have resolver called on dict values."""
    # Test with dict value
    config_dict = {"backend": {"type": "redis", "host": "localhost"}}

    result = build_config_from_dict(ResolverConfig, config_dict)

    assert result.backend == "Resolved: redis"


def test_resolver_function_with_string_value():
    """Test that cli_resolve fields work with string values."""
    config_dict = {"backend": "simple_string"}

    result = build_config_from_dict(ResolverConfig, config_dict)

    assert result.backend == "Direct: simple_string"


def test_excluded_fields_settable_via_dict():
    """Test that cli_exclude fields can be set via dict."""
    config_dict = {
        "visible_field": "visible_value",
        "hidden_field": "hidden_value",
    }

    result = build_config_from_dict(ExcludedConfig, config_dict)

    assert result.visible_field == "visible_value"
    assert result.hidden_field == "hidden_value"


def test_included_fields_only():
    """Test that only included fields (non-excluded) are processed normally."""
    config_dict = {
        "visible_field": "only_visible",
        # hidden_field not set, should use its default
    }

    result = build_config_from_dict(ExcludedConfig, config_dict)

    assert result.visible_field == "only_visible"
    assert result.hidden_field == "excluded_default"


def test_non_dict_raises_type_error():
    """Test that passing non-dict raises TypeError with helpful message."""
    with pytest.raises(TypeError) as exc_info:
        build_config_from_dict(SimpleConfig, "not_a_dict")

    assert "build_config_from_dict requires a dict" in str(exc_info.value)
    assert "Use build_config_from_cli() with base_configs" in str(exc_info.value)


def test_list_raises_type_error():
    """Test that passing list raises TypeError."""
    with pytest.raises(TypeError) as exc_info:
        build_config_from_dict(SimpleConfig, ["list", "not", "dict"])

    assert "build_config_from_dict requires a dict" in str(exc_info.value)


def test_int_raises_type_error():
    """Test that passing int raises TypeError."""
    with pytest.raises(TypeError) as exc_info:
        build_config_from_dict(SimpleConfig, 42)

    assert "build_config_from_dict requires a dict" in str(exc_info.value)


# Additional tests for comprehensive coverage


@dataclass
class OptionalFieldsConfig:
    """Config with optional fields."""

    required: str
    optional: Optional[str] = None
    optional_with_default: Optional[int] = 42


def test_optional_fields_with_required():
    """Test handling of Optional fields when required field is present."""
    config_dict = {
        "required": "value",
        # optional fields omitted
    }

    result = build_config_from_dict(OptionalFieldsConfig, config_dict)

    assert result.required == "value"
    assert result.optional is None
    assert result.optional_with_default == 42


def test_optional_fields_explicitly_set():
    """Test setting optional fields explicitly."""
    config_dict = {
        "required": "value",
        "optional": "set_value",
        "optional_with_default": 100,
    }

    result = build_config_from_dict(OptionalFieldsConfig, config_dict)

    assert result.required == "value"
    assert result.optional == "set_value"
    assert result.optional_with_default == 100


@dataclass
class ListFieldsConfig:
    """Config with list fields."""

    items: Optional[List[str]] = None
    numbers: Optional[List[int]] = None


def test_list_fields():
    """Test that list fields work correctly."""
    config_dict = {
        "items": ["a", "b", "c"],
        "numbers": [1, 2, 3],
    }

    result = build_config_from_dict(ListFieldsConfig, config_dict)

    assert result.items == ["a", "b", "c"]
    assert result.numbers == [1, 2, 3]


def test_list_fields_with_defaults():
    """Test that list fields use defaults when omitted."""
    result = build_config_from_dict(ListFieldsConfig, {})

    assert result.items is None
    assert result.numbers is None


def test_file_loadable_resolved_from_dict(tmp_path):
    """@file reference in dict is resolved for cli_file_loadable fields."""
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("You are helpful.")

    @dataclass
    class FileConfig:
        prompt: str = cli_file_loadable(default="default")

    result = build_config_from_dict(FileConfig, {"prompt": f"@{prompt_file}"})
    assert result.prompt == "You are helpful."


def test_file_loadable_literal_unchanged():
    """Non-@ string passes through unchanged for file_loadable fields."""

    @dataclass
    class FileConfig:
        prompt: str = cli_file_loadable(default="default")

    result = build_config_from_dict(FileConfig, {"prompt": "literal value"})
    assert result.prompt == "literal value"


def test_file_loadable_missing_uses_default():
    """Missing field uses default."""

    @dataclass
    class FileConfig:
        prompt: str = cli_file_loadable(default="the default")

    result = build_config_from_dict(FileConfig, {})
    assert result.prompt == "the default"


def test_file_loadable_nonexistent_file_raises():
    """@file pointing to nonexistent file raises error."""

    @dataclass
    class FileConfig:
        prompt: str = cli_file_loadable(default="default")

    with pytest.raises(Exception):
        build_config_from_dict(FileConfig, {"prompt": "@/nonexistent/path.txt"})


def test_non_file_loadable_at_prefix_unchanged():
    """@-prefixed value in regular field is NOT resolved."""

    @dataclass
    class RegularConfig:
        name: str = "default"

    result = build_config_from_dict(RegularConfig, {"name": "@some-value"})
    assert result.name == "@some-value"


def test_build_config_remembers_base_config_name(tmp_path):
    """build_config() uses base_config_name from add_arguments() by default."""
    import argparse
    import json

    from dataclass_args import GenericConfigBuilder

    config_file = tmp_path / "my_config.json"
    config_file.write_text(json.dumps({"name": "from-file", "count": 42}))

    @dataclass
    class MyConfig:
        name: str = "default"
        count: int = 0

    builder = GenericConfigBuilder(MyConfig)
    parser = argparse.ArgumentParser()
    builder.add_arguments(parser, base_config_name="my-config")

    args = parser.parse_args(["--my-config", str(config_file)])

    # Without explicit base_config_name — should use "my_config" from add_arguments
    config = builder.build_config(args)
    assert config.name == "from-file"
    assert config.count == 42


def test_build_config_explicit_base_config_name_overrides(tmp_path):
    """Explicit base_config_name in build_config overrides the stored one."""
    import argparse
    import json

    from dataclass_args import GenericConfigBuilder

    config_file = tmp_path / "alt.json"
    config_file.write_text(json.dumps({"name": "alt-file"}))

    @dataclass
    class MyConfig:
        name: str = "default"

    builder = GenericConfigBuilder(MyConfig)
    parser = argparse.ArgumentParser()
    builder.add_arguments(parser, base_config_name="my-config")

    # Add a second config argument manually
    parser.add_argument("--alt", type=str)
    args = parser.parse_args(["--alt", str(config_file)])

    # Explicit base_config_name overrides
    config = builder.build_config(args, base_config_name="alt")
    assert config.name == "alt-file"
