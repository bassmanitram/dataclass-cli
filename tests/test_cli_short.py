"""
Tests for cli_short() functionality.
"""

import argparse
from dataclasses import dataclass, fields

import pytest

from dataclass_args import (
    GenericConfigBuilder,
    build_config,
    cli_help,
    cli_short,
    combine_annotations,
    get_cli_short,
)


class TestCliShortAnnotation:
    """Test cli_short() annotation function."""

    def test_cli_short_basic(self):
        """Test basic cli_short annotation."""

        @dataclass
        class Config:
            name: str = cli_short("n")

        # Check metadata
        field_map = {f.name: f for f in fields(Config)}
        name_field = field_map["name"]

        assert "cli_short" in name_field.metadata
        assert name_field.metadata["cli_short"] == "n"

    def test_cli_short_with_default(self):
        """Test cli_short with default value."""

        @dataclass
        class Config:
            host: str = cli_short("H", default="localhost")

        config = build_config(Config, [])
        assert config.host == "localhost"

        config = build_config(Config, ["-H", "0.0.0.0"])
        assert config.host == "0.0.0.0"

        config = build_config(Config, ["--host", "192.168.1.1"])
        assert config.host == "192.168.1.1"

    def test_cli_short_validation(self):
        """Test that cli_short validates single character."""

        with pytest.raises(ValueError, match="single character"):

            @dataclass
            class Config:
                name: str = cli_short("ab")  # Too long

        with pytest.raises(ValueError, match="single character"):

            @dataclass
            class Config2:
                name: str = cli_short("")  # Empty

    def test_cli_short_multiple_fields(self):
        """Test multiple fields with short options."""

        @dataclass
        class Config:
            name: str = cli_short("n")
            host: str = cli_short("H", default="localhost")
            port: int = cli_short("p", default=8080)

        config = build_config(
            Config, ["-n", "myapp", "-H", "0.0.0.0", "--port", "9000"]
        )
        assert config.name == "myapp"
        assert config.host == "0.0.0.0"
        assert config.port == 9000


class TestCliShortFunctionality:
    """Test cli_short in actual CLI parsing."""

    def test_short_option_works(self):
        """Test that short option is accepted."""

        @dataclass
        class Config:
            name: str = cli_short("n")

        config = build_config(Config, ["-n", "test"])
        assert config.name == "test"

    def test_long_option_still_works(self):
        """Test that long option still works with short defined."""

        @dataclass
        class Config:
            name: str = cli_short("n")

        config = build_config(Config, ["--name", "test"])
        assert config.name == "test"

    def test_mixed_short_and_long(self):
        """Test mixing short and long options."""

        @dataclass
        class Config:
            name: str = cli_short("n")
            host: str = cli_short("H", default="localhost")
            port: int = 8080

        config = build_config(
            Config, ["-n", "myapp", "--host", "0.0.0.0", "--port", "9000"]
        )
        assert config.name == "myapp"
        assert config.host == "0.0.0.0"
        assert config.port == 9000

    def test_short_option_with_integer(self):
        """Test short option with integer type."""

        @dataclass
        class Config:
            port: int = cli_short("p", default=8080)

        config = build_config(Config, ["--port", "9000"])
        assert config.port == 9000
        assert isinstance(config.port, int)

    def test_short_option_with_boolean(self):
        """Test short option with boolean type."""

        @dataclass
        class Config:
            debug: bool = cli_short("d", default=False)

        config = build_config(Config, ["-d"])
        assert config.debug is True

        config = build_config(Config, ["--no-debug"])
        assert config.debug is False


class TestCliShortWithCombineAnnotations:
    """Test cli_short combined with other annotations."""

    def test_combine_short_and_help(self):
        """Test combining cli_short and cli_help."""

        @dataclass
        class Config:
            name: str = combine_annotations(
                cli_short("n"), cli_help("Application name")
            )

        # Check metadata
        field_map = {f.name: f for f in fields(Config)}
        name_field = field_map["name"]

        assert "cli_short" in name_field.metadata
        assert "cli_help" in name_field.metadata
        assert name_field.metadata["cli_short"] == "n"
        assert name_field.metadata["cli_help"] == "Application name"

        # Test functionality
        config = build_config(Config, ["-n", "myapp"])
        assert config.name == "myapp"

    def test_combine_short_help_and_default(self):
        """Test combining multiple annotations with default."""

        @dataclass
        class Config:
            host: str = combine_annotations(
                cli_short("H"), cli_help("Server host"), default="localhost"
            )

        config = build_config(Config, [])
        assert config.host == "localhost"

        config = build_config(Config, ["-H", "0.0.0.0"])
        assert config.host == "0.0.0.0"


class TestGetCliShort:
    """Test get_cli_short() helper function."""

    def test_get_cli_short_returns_value(self):
        """Test that get_cli_short returns the short option."""

        @dataclass
        class Config:
            name: str = cli_short("n")

        builder = GenericConfigBuilder(Config)
        field_info = builder._config_fields["name"]

        short = get_cli_short(field_info)
        assert short == "n"

    def test_get_cli_short_returns_none_without_annotation(self):
        """Test that get_cli_short returns None without annotation."""

        @dataclass
        class Config:
            name: str

        builder = GenericConfigBuilder(Config)
        field_info = builder._config_fields["name"]

        short = get_cli_short(field_info)
        assert short is None


class TestCliShortInHelp:
    """Test that short options appear in help text."""

    def test_short_option_in_help(self):
        """Test that short option appears in help text."""

        @dataclass
        class Config:
            name: str = cli_short("n")

        builder = GenericConfigBuilder(Config)
        parser = argparse.ArgumentParser()
        builder.add_arguments(parser)

        help_text = parser.format_help()

        # Should contain both -n and --name
        assert "-n" in help_text
        assert "--name" in help_text

    def test_short_and_help_text(self):
        """Test that short option and help text both appear."""

        @dataclass
        class Config:
            name: str = combine_annotations(
                cli_short("n"), cli_help("Application name")
            )

        builder = GenericConfigBuilder(Config)
        parser = argparse.ArgumentParser()
        builder.add_arguments(parser)

        help_text = parser.format_help()

        assert "-n" in help_text
        assert "--name" in help_text
        assert "Application name" in help_text


class TestCliShortEdgeCases:
    """Test edge cases and error handling."""

    def test_field_without_short_still_works(self):
        """Test that fields without short option still work."""

        @dataclass
        class Config:
            with_short: str = cli_short("n")
            without_short: str = "default"

        config = build_config(Config, ["-n", "test"])
        assert config.with_short == "test"
        assert config.without_short == "default"

        config = build_config(Config, ["-n", "test", "--without-short", "value"])
        assert config.with_short == "test"
        assert config.without_short == "value"

    def test_required_field_with_short(self):
        """Test required field with short option."""

        @dataclass
        class Config:
            required: str = cli_short("r")

        # Should work with short
        config = build_config(Config, ["-r", "value"])
        assert config.required == "value"

        # Should work with long
        config = build_config(Config, ["--required", "value"])
        assert config.required == "value"

    def test_all_common_short_options(self):
        """Test commonly used short options."""

        @dataclass
        class Config:
            # Common short options from tools like git, ls, etc.
            name: str = cli_short("n")
            host: str = cli_short("H", default="localhost")
            port: int = cli_short("p", default=8080)
            verbose: bool = cli_short("v", default=False)
            debug: bool = cli_short("d", default=False)
            output: str = cli_short("o", default="out.txt")

        config = build_config(
            Config,
            [
                "-n",
                "myapp",
                "-H",
                "0.0.0.0",
                "--port",
                "9000",
                "-v",
                "-d",
                "-o",
                "result.txt",
            ],
        )

        assert config.name == "myapp"
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.verbose is True
        assert config.debug is True
        assert config.output == "result.txt"
