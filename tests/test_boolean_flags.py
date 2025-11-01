"""
Tests for boolean flag functionality with --flag and --no-flag support.
"""

import argparse
from dataclasses import dataclass

import pytest

from dataclass_args import (
    GenericConfigBuilder,
    build_config,
    cli_help,
    cli_short,
    combine_annotations,
)


class TestBooleanFlags:
    """Test boolean flag functionality."""

    def test_boolean_default_false_with_positive_flag(self):
        """Test boolean with default False using positive flag."""

        @dataclass
        class Config:
            debug: bool = False

        # Default should be False
        config = build_config(Config, [])
        assert config.debug is False

        # --debug should set to True
        config = build_config(Config, ["--debug"])
        assert config.debug is True

    def test_boolean_default_false_with_negative_flag(self):
        """Test boolean with default False using negative flag."""

        @dataclass
        class Config:
            debug: bool = False

        # --no-debug should explicitly set to False
        config = build_config(Config, ["--no-debug"])
        assert config.debug is False

    def test_boolean_default_true_with_positive_flag(self):
        """Test boolean with default True using positive flag."""

        @dataclass
        class Config:
            optimize: bool = True

        # Default should be True
        config = build_config(Config, [])
        assert config.optimize is True

        # --optimize should keep True
        config = build_config(Config, ["--optimize"])
        assert config.optimize is True

    def test_boolean_default_true_with_negative_flag(self):
        """Test boolean with default True using negative flag."""

        @dataclass
        class Config:
            optimize: bool = True

        # --no-optimize should set to False
        config = build_config(Config, ["--no-optimize"])
        assert config.optimize is False

    def test_multiple_boolean_flags(self):
        """Test multiple boolean flags together."""

        @dataclass
        class Config:
            debug: bool = False
            verbose: bool = False
            optimize: bool = True
            cache: bool = True

        config = build_config(
            Config, ["--debug", "--verbose", "--no-optimize", "--no-cache"]
        )
        assert config.debug is True
        assert config.verbose is True
        assert config.optimize is False
        assert config.cache is False


class TestBooleanFlagsWithShort:
    """Test boolean flags with short options."""

    def test_boolean_with_short_option(self):
        """Test boolean flag with short option."""

        @dataclass
        class Config:
            debug: bool = cli_short("d", default=False)
            verbose: bool = cli_short("v", default=False)

        # Short form
        config = build_config(Config, ["-d", "-v"])
        assert config.debug is True
        assert config.verbose is True

        # Long form still works
        config = build_config(Config, ["--debug", "--verbose"])
        assert config.debug is True
        assert config.verbose is True

    def test_boolean_short_with_negative(self):
        """Test boolean short option with negative flag."""

        @dataclass
        class Config:
            cache: bool = cli_short("c", default=True)

        # Default
        config = build_config(Config, [])
        assert config.cache is True

        # Negative flag
        config = build_config(Config, ["--no-cache"])
        assert config.cache is False

        # Short positive
        config = build_config(Config, ["-c"])
        assert config.cache is True


class TestBooleanFlagsWithCombineAnnotations:
    """Test boolean flags with combined annotations."""

    def test_combine_boolean_short_and_help(self):
        """Test boolean with short option and help text."""

        @dataclass
        class Config:
            debug: bool = combine_annotations(
                cli_short("d"), cli_help("Enable debug mode"), default=False
            )

        config = build_config(Config, ["-d"])
        assert config.debug is True

        config = build_config(Config, ["--no-debug"])
        assert config.debug is False

    def test_multiple_combined_booleans(self):
        """Test multiple booleans with combined annotations."""

        @dataclass
        class Config:
            debug: bool = combine_annotations(
                cli_short("d"), cli_help("Debug mode"), default=False
            )
            verbose: bool = combine_annotations(
                cli_short("v"), cli_help("Verbose output"), default=False
            )
            quiet: bool = combine_annotations(
                cli_short("q"), cli_help("Quiet mode"), default=False
            )

        config = build_config(Config, ["-d", "-v", "--no-quiet"])
        assert config.debug is True
        assert config.verbose is True
        assert config.quiet is False


class TestBooleanFlagsInHelp:
    """Test that boolean flags appear correctly in help."""

    def test_boolean_flags_in_help(self):
        """Test that both positive and negative forms appear in help."""

        @dataclass
        class Config:
            debug: bool = False

        builder = GenericConfigBuilder(Config)
        parser = argparse.ArgumentParser()
        builder.add_arguments(parser)

        help_text = parser.format_help()

        # Should contain both forms
        assert "--debug" in help_text
        assert "--no-debug" in help_text

    def test_boolean_with_short_in_help(self):
        """Test that short option appears in boolean help."""

        @dataclass
        class Config:
            debug: bool = cli_short("d", default=False)

        builder = GenericConfigBuilder(Config)
        parser = argparse.ArgumentParser()
        builder.add_arguments(parser)

        help_text = parser.format_help()

        # Should contain short, long, and negative forms
        assert "-d" in help_text
        assert "--debug" in help_text
        assert "--no-debug" in help_text


class TestBooleanFlagsEdgeCases:
    """Test edge cases for boolean flags."""

    def test_boolean_with_underscore_in_name(self):
        """Test boolean with underscore in field name."""

        @dataclass
        class Config:
            enable_cache: bool = False

        config = build_config(Config, ["--enable-cache"])
        assert config.enable_cache is True

        config = build_config(Config, ["--no-enable-cache"])
        assert config.enable_cache is False

    def test_mixed_boolean_and_other_types(self):
        """Test booleans mixed with other field types."""

        @dataclass
        class Config:
            name: str = cli_short("n")
            debug: bool = cli_short("d", default=False)
            port: int = cli_short("p", default=8080)
            verbose: bool = False

        config = build_config(Config, ["-n", "myapp", "-d", "-p", "9000", "--verbose"])
        assert config.name == "myapp"
        assert config.debug is True
        assert config.port == 9000
        assert config.verbose is True

    def test_only_negative_flag_used(self):
        """Test using only negative flag when default is True."""

        @dataclass
        class Config:
            production: bool = True

        config = build_config(Config, ["--no-production"])
        assert config.production is False


class TestBooleanFlagsRealWorld:
    """Test real-world usage patterns."""

    def test_build_configuration(self):
        """Test realistic build configuration with feature flags."""

        @dataclass
        class BuildConfig:
            # Build steps (default on)
            build: bool = True
            test: bool = True
            lint: bool = True

            # Optional steps (default off)
            deploy: bool = False
            notify: bool = False

            # Debug options
            debug: bool = cli_short("d", default=False)
            verbose: bool = cli_short("v", default=False)

        # Quick CI build: skip slow steps
        config = build_config(BuildConfig, ["--no-lint", "--no-test"])
        assert config.build is True
        assert config.test is False
        assert config.lint is False
        assert config.deploy is False

        # Full pipeline with deployment
        config = build_config(BuildConfig, ["--deploy", "--notify", "-d", "-v"])
        assert config.build is True
        assert config.test is True
        assert config.lint is True
        assert config.deploy is True
        assert config.notify is True
        assert config.debug is True
        assert config.verbose is True

    def test_server_feature_flags(self):
        """Test server with feature flags."""

        @dataclass
        class ServerConfig:
            name: str = cli_short("n")

            # Feature flags (default on)
            api_v2: bool = True
            analytics: bool = True

            # Beta features (default off)
            new_ui: bool = False
            beta_api: bool = False

        # Disable problematic feature
        config = build_config(ServerConfig, ["-n", "prod-1", "--no-api-v2"])
        assert config.name == "prod-1"
        assert config.api_v2 is False
        assert config.analytics is True

        # Enable beta features
        config = build_config(ServerConfig, ["-n", "staging", "--new-ui", "--beta-api"])
        assert config.new_ui is True
        assert config.beta_api is True
