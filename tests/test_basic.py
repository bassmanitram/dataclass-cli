"""
Basic tests for dataclass-cli functionality.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest

from dataclass_cli import (
    build_config_from_cli,
    cli_exclude,
    cli_file_loadable,
    cli_help,
)
from dataclass_cli.exceptions import ConfigBuilderError, ConfigurationError


@dataclass
class SimpleConfig:
    name: str
    count: int = 10
    debug: bool = False


@dataclass
class ComplexConfig:
    host: str = cli_help("Server host")
    port: int = cli_help("Server port", default=8000)
    items: List[str] = cli_help("Item list", default_factory=list)
    settings: Dict[str, Any] = None
    timeout: Optional[float] = None
    _internal: str = cli_exclude(default="hidden")


class TestBasicFunctionality:
    """Test basic CLI building functionality."""

    def test_simple_config_creation(self):
        """Test creating a simple config from CLI args."""
        config = build_config_from_cli(
            SimpleConfig, ["--name", "test", "--count", "5", "--debug", "true"]
        )

        assert config.name == "test"
        assert config.count == 5
        assert config.debug is True

    def test_simple_config_defaults(self):
        """Test that default values are used when not specified."""
        config = build_config_from_cli(SimpleConfig, ["--name", "test"])

        assert config.name == "test"
        assert config.count == 10  # Default value
        assert config.debug is False  # Default value

    def test_boolean_parsing(self):
        """Test various boolean value formats."""
        test_cases = [
            ("true", True),
            ("false", False),
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
            ("on", True),
            ("off", False),
            ("TRUE", True),
            ("FALSE", False),
        ]

        for bool_str, expected in test_cases:
            config = build_config_from_cli(
                SimpleConfig, ["--name", "test", "--debug", bool_str]
            )
            assert config.debug is expected, f"Failed for input: {bool_str}"

    def test_complex_types(self):
        """Test handling of complex types like lists and dicts."""
        config = build_config_from_cli(
            ComplexConfig,
            [
                "--host",
                "localhost",
                "--port",
                "9000",
                "--items",
                "item1",
                "--items",
                "item2",
                "--items",
                "item3",
                "--timeout",
                "30.5",
            ],
        )

        assert config.host == "localhost"
        assert config.port == 9000
        assert config.items == ["item1", "item2", "item3"]
        assert config.timeout == 30.5
        assert config._internal == "hidden"  # Excluded field keeps default

    def test_optional_types(self):
        """Test handling of optional types."""
        # Without optional value
        config1 = build_config_from_cli(ComplexConfig, ["--host", "localhost"])
        assert config1.timeout is None

        # With optional value
        config2 = build_config_from_cli(
            ComplexConfig, ["--host", "localhost", "--timeout", "15.0"]
        )
        assert config2.timeout == 15.0


class TestErrorHandling:
    """Test error handling and validation."""

    def test_invalid_dataclass(self):
        """Test error when config_class is not a dataclass."""

        class NotADataclass:
            pass

        with pytest.raises(
            ConfigBuilderError, match="config_class must be a dataclass"
        ):
            build_config_from_cli(NotADataclass, [])

    def test_missing_required_field(self):
        """Test error when required field is missing."""
        with pytest.raises(ConfigurationError, match="Failed to create SimpleConfig"):
            build_config_from_cli(SimpleConfig, [])  # Missing required 'name'

    def test_invalid_type_conversion(self):
        """Test error when type conversion fails."""
        with pytest.raises(SystemExit):  # argparse exits on invalid type
            build_config_from_cli(
                SimpleConfig, ["--name", "test", "--count", "not-a-number"]
            )


class TestAnnotations:
    """Test CLI annotations functionality."""

    @dataclass
    class AnnotatedConfig:
        public_field: str = cli_help("Public field help")
        another_field: int = cli_help("Another field", default=42)
        hidden_field: str = cli_exclude(default="secret")

    def test_cli_exclude_annotation(self):
        """Test that cli_exclude() hides fields from CLI."""
        config = build_config_from_cli(
            self.AnnotatedConfig,
            ["--public-field", "test", "--another-field", "100"],
        )

        assert config.public_field == "test"
        assert config.another_field == 100
        assert config.hidden_field == "secret"  # Default value, not from CLI

    def test_help_text_generation(self):
        """Test that help text is properly generated."""
        # This is more of an integration test - would need to capture help output
        # For now, just verify the config builds successfully
        config = build_config_from_cli(self.AnnotatedConfig, ["--public-field", "test"])
        assert config.public_field == "test"


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    @dataclass
    class EmptyConfig:
        pass

    @dataclass
    class AllOptionalConfig:
        field1: Optional[str] = None
        field2: Optional[int] = None

    def test_empty_config(self):
        """Test config with no fields."""
        config = build_config_from_cli(self.EmptyConfig, [])
        assert isinstance(config, self.EmptyConfig)

    def test_all_optional_config(self):
        """Test config where all fields are optional."""
        config = build_config_from_cli(self.AllOptionalConfig, [])
        assert config.field1 is None
        assert config.field2 is None

        # With values
        config2 = build_config_from_cli(
            self.AllOptionalConfig, ["--field1", "test", "--field2", "42"]
        )
        assert config2.field1 == "test"
        assert config2.field2 == 42


if __name__ == "__main__":
    pytest.main([__file__])
