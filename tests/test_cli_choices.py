"""
Tests for cli_choices() functionality.
"""

import argparse
from dataclasses import dataclass, fields

import pytest

from dataclass_args import (
    GenericConfigBuilder,
    build_config,
    cli_choices,
    cli_help,
    cli_short,
    combine_annotations,
    get_cli_choices,
)


class TestCliChoicesAnnotation:
    """Test cli_choices() annotation function."""

    def test_cli_choices_basic(self):
        """Test basic cli_choices annotation."""

        @dataclass
        class Config:
            environment: str = cli_choices(["dev", "staging", "prod"])

        # Check metadata
        field_map = {f.name: f for f in fields(Config)}
        env_field = field_map["environment"]

        assert "cli_choices" in env_field.metadata
        assert env_field.metadata["cli_choices"] == ["dev", "staging", "prod"]

    def test_cli_choices_with_default(self):
        """Test cli_choices with default value."""

        @dataclass
        class Config:
            size: str = cli_choices(["small", "medium", "large"], default="medium")

        config = build_config(Config, [])
        assert config.size == "medium"

        config = build_config(Config, ["--size", "large"])
        assert config.size == "large"

    def test_cli_choices_validation_empty(self):
        """Test that cli_choices validates non-empty choices."""

        with pytest.raises(ValueError, match="at least one choice"):

            @dataclass
            class Config:
                field: str = cli_choices([])

    def test_cli_choices_multiple_fields(self):
        """Test multiple fields with choices."""

        @dataclass
        class Config:
            environment: str = cli_choices(["dev", "staging", "prod"])
            size: str = cli_choices(["small", "medium", "large"], default="medium")
            region: str = cli_choices(
                ["us-east", "us-west", "eu-west"], default="us-east"
            )

        config = build_config(
            Config, ["--environment", "prod", "--size", "large", "--region", "us-west"]
        )
        assert config.environment == "prod"
        assert config.size == "large"
        assert config.region == "us-west"


class TestCliChoicesFunctionality:
    """Test cli_choices in actual CLI parsing."""

    def test_valid_choice_accepted(self):
        """Test that valid choice is accepted."""

        @dataclass
        class Config:
            environment: str = cli_choices(["dev", "staging", "prod"])

        config = build_config(Config, ["--environment", "dev"])
        assert config.environment == "dev"

        config = build_config(Config, ["--environment", "prod"])
        assert config.environment == "prod"

    def test_invalid_choice_rejected(self):
        """Test that invalid choice is rejected."""

        @dataclass
        class Config:
            environment: str = cli_choices(["dev", "staging", "prod"])

        with pytest.raises(SystemExit):
            build_config(Config, ["--environment", "invalid"])

    def test_choices_with_integers(self):
        """Test choices with integer values."""

        @dataclass
        class Config:
            priority: int = cli_choices([1, 2, 3, 5, 8], default=3)

        config = build_config(Config, ["--priority", "5"])
        assert config.priority == 5
        assert isinstance(config.priority, int)

    def test_choices_shown_in_error(self):
        """Test that choices are shown in error message."""

        @dataclass
        class Config:
            size: str = cli_choices(["small", "large"])

        # Capture the error by using parse_args directly
        builder = GenericConfigBuilder(Config)
        parser = argparse.ArgumentParser()
        builder.add_arguments(parser)

        with pytest.raises(SystemExit):
            parser.parse_args(["--size", "invalid"])


class TestCliChoicesWithCombineAnnotations:
    """Test cli_choices combined with other annotations."""

    def test_combine_choices_and_help(self):
        """Test combining cli_choices and cli_help."""

        @dataclass
        class Config:
            environment: str = combine_annotations(
                cli_choices(["dev", "staging", "prod"]),
                cli_help("Deployment environment"),
            )

        # Check metadata
        field_map = {f.name: f for f in fields(Config)}
        env_field = field_map["environment"]

        assert "cli_choices" in env_field.metadata
        assert "cli_help" in env_field.metadata
        assert env_field.metadata["cli_choices"] == ["dev", "staging", "prod"]
        assert env_field.metadata["cli_help"] == "Deployment environment"

        # Test functionality
        config = build_config(Config, ["--environment", "prod"])
        assert config.environment == "prod"

    def test_combine_short_choices_and_help(self):
        """Test combining cli_short, cli_choices, and cli_help."""

        @dataclass
        class Config:
            region: str = combine_annotations(
                cli_short("r"),
                cli_choices(["us-east-1", "us-west-2", "eu-west-1"]),
                cli_help("AWS region"),
                default="us-east-1",
            )

        # Check metadata
        field_map = {f.name: f for f in fields(Config)}
        region_field = field_map["region"]

        assert "cli_short" in region_field.metadata
        assert "cli_choices" in region_field.metadata
        assert "cli_help" in region_field.metadata

        # Test functionality with short option
        config = build_config(Config, ["-r", "us-west-2"])
        assert config.region == "us-west-2"

        # Test functionality with long option
        config = build_config(Config, ["--region", "eu-west-1"])
        assert config.region == "eu-west-1"

    def test_combine_all_three_with_default(self):
        """Test combining short, choices, help with default."""

        @dataclass
        class Config:
            size: str = combine_annotations(
                cli_short("s"),
                cli_choices(["small", "medium", "large"]),
                cli_help("Instance size"),
                default="medium",
            )

        config = build_config(Config, [])
        assert config.size == "medium"

        config = build_config(Config, ["-s", "large"])
        assert config.size == "large"


class TestGetCliChoices:
    """Test get_cli_choices() helper function."""

    def test_get_cli_choices_returns_value(self):
        """Test that get_cli_choices returns the choices list."""

        @dataclass
        class Config:
            environment: str = cli_choices(["dev", "staging", "prod"])

        builder = GenericConfigBuilder(Config)
        field_info = builder._config_fields["environment"]

        choices = get_cli_choices(field_info)
        assert choices == ["dev", "staging", "prod"]

    def test_get_cli_choices_returns_none_without_annotation(self):
        """Test that get_cli_choices returns None without annotation."""

        @dataclass
        class Config:
            environment: str

        builder = GenericConfigBuilder(Config)
        field_info = builder._config_fields["environment"]

        choices = get_cli_choices(field_info)
        assert choices is None


class TestCliChoicesInHelp:
    """Test that choices appear in help text."""

    def test_choices_in_help(self):
        """Test that choices appear in help text."""

        @dataclass
        class Config:
            environment: str = cli_choices(["dev", "staging", "prod"])

        builder = GenericConfigBuilder(Config)
        parser = argparse.ArgumentParser()
        builder.add_arguments(parser)

        help_text = parser.format_help()

        # Should contain choices
        assert "dev" in help_text
        assert "staging" in help_text
        assert "prod" in help_text

    def test_choices_and_help_text(self):
        """Test that choices and help text both appear."""

        @dataclass
        class Config:
            environment: str = combine_annotations(
                cli_choices(["dev", "staging", "prod"]),
                cli_help("Deployment environment"),
            )

        builder = GenericConfigBuilder(Config)
        parser = argparse.ArgumentParser()
        builder.add_arguments(parser)

        help_text = parser.format_help()

        assert "Deployment environment" in help_text
        assert "dev" in help_text or "choices:" in help_text.lower()


class TestCliChoicesEdgeCases:
    """Test edge cases and error handling."""

    def test_field_without_choices_still_works(self):
        """Test that fields without choices still work."""

        @dataclass
        class Config:
            with_choices: str = cli_choices(["a", "b", "c"])
            without_choices: str = "default"

        config = build_config(Config, ["--with-choices", "a"])
        assert config.with_choices == "a"
        assert config.without_choices == "default"

        config = build_config(
            Config, ["--with-choices", "b", "--without-choices", "value"]
        )
        assert config.with_choices == "b"
        assert config.without_choices == "value"

    def test_choices_with_numeric_strings(self):
        """Test choices with numeric string values."""

        @dataclass
        class Config:
            version: str = cli_choices(["1.0", "2.0", "3.0"], default="1.0")

        config = build_config(Config, ["--version", "2.0"])
        assert config.version == "2.0"

    def test_choices_case_sensitive(self):
        """Test that choices are case-sensitive."""

        @dataclass
        class Config:
            environment: str = cli_choices(["dev", "DEV", "Dev"])

        # All should be valid
        config = build_config(Config, ["--environment", "dev"])
        assert config.environment == "dev"

        config = build_config(Config, ["--environment", "DEV"])
        assert config.environment == "DEV"

        config = build_config(Config, ["--environment", "Dev"])
        assert config.environment == "Dev"

    def test_choices_with_special_characters(self):
        """Test choices with special characters."""

        @dataclass
        class Config:
            region: str = cli_choices(["us-east-1", "us-west-2", "eu-west-1"])

        config = build_config(Config, ["--region", "us-east-1"])
        assert config.region == "us-east-1"


class TestCliChoicesRealWorld:
    """Test real-world usage patterns."""

    def test_deployment_configuration(self):
        """Test realistic deployment configuration."""

        @dataclass
        class DeployConfig:
            name: str = cli_short("n")
            environment: str = combine_annotations(
                cli_short("e"),
                cli_choices(["dev", "staging", "prod"]),
                cli_help("Deployment environment"),
                default="dev",
            )
            region: str = combine_annotations(
                cli_short("r"),
                cli_choices(["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]),
                cli_help("AWS region"),
                default="us-east-1",
            )
            size: str = combine_annotations(
                cli_short("s"),
                cli_choices(["small", "medium", "large", "xlarge"]),
                default="medium",
            )

        # Test realistic usage
        config = build_config(
            DeployConfig,
            [
                "-n",
                "myapp",
                "-e",
                "prod",
                "-r",
                "us-west-2",
                "-s",
                "large",
            ],
        )

        assert config.name == "myapp"
        assert config.environment == "prod"
        assert config.region == "us-west-2"
        assert config.size == "large"

        # Test with long forms
        config = build_config(
            DeployConfig,
            [
                "--name",
                "myapp2",
                "--environment",
                "staging",
                "--region",
                "eu-west-1",
                "--size",
                "xlarge",
            ],
        )

        assert config.name == "myapp2"
        assert config.environment == "staging"
        assert config.region == "eu-west-1"
        assert config.size == "xlarge"
