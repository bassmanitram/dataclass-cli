"""
Tests for combine_annotations() functionality.
"""

import tempfile
from dataclasses import dataclass, fields
from pathlib import Path

import pytest

from dataclass_args import (
    build_config,
    cli_exclude,
    cli_file_loadable,
    cli_help,
    cli_include,
    combine_annotations,
)


class TestCombineAnnotations:
    """Test combine_annotations() helper function."""

    def test_combine_help_and_file_loadable(self):
        """Test combining cli_help and cli_file_loadable."""

        @dataclass
        class Config:
            message: str = combine_annotations(
                cli_help("Message content"),
                cli_file_loadable(),
                default="default",
            )

        # Check metadata was combined
        field_map = {f.name: f for f in fields(Config)}
        message_field = field_map["message"]

        assert "cli_help" in message_field.metadata
        assert "cli_file_loadable" in message_field.metadata
        assert message_field.metadata["cli_help"] == "Message content"
        assert message_field.metadata["cli_file_loadable"] is True

    def test_combine_multiple_annotations(self):
        """Test combining three or more annotations."""

        @dataclass
        class Config:
            field: str = combine_annotations(
                cli_help("Field help text"),
                cli_file_loadable(),
                cli_include(),
                default="default",
            )

        field_map = {f.name: f for f in fields(Config)}
        test_field = field_map["field"]

        assert "cli_help" in test_field.metadata
        assert "cli_file_loadable" in test_field.metadata
        assert "cli_include" in test_field.metadata
        assert test_field.metadata["cli_help"] == "Field help text"
        assert test_field.metadata["cli_file_loadable"] is True
        assert test_field.metadata["cli_include"] is True

    def test_combine_with_literal_value(self):
        """Test combined annotation works with literal CLI value."""

        @dataclass
        class Config:
            message: str = combine_annotations(
                cli_help("Message"),
                cli_file_loadable(),
                default="default",
            )

        config = build_config(Config, ["--message", "literal value"])
        assert config.message == "literal value"

    def test_combine_with_file_loading(self):
        """Test combined annotation works with file loading."""

        @dataclass
        class Config:
            message: str = combine_annotations(
                cli_help("Message"),
                cli_file_loadable(),
                default="default",
            )

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("file content")
            temp_path = f.name

        try:
            config = build_config(Config, ["--message", f"@{temp_path}"])
            assert config.message == "file content"
        finally:
            Path(temp_path).unlink()

    def test_combine_preserves_defaults(self):
        """Test that default values are preserved."""

        @dataclass
        class Config:
            required: str = combine_annotations(cli_help("Required field"))
            with_default: str = combine_annotations(
                cli_help("Field with default"),
                default="my default",
            )

        config = build_config(Config, ["--required", "value"])
        assert config.with_default == "my default"
        assert config.required == "value"

    def test_combine_with_default_factory(self):
        """Test combine_annotations with default_factory."""

        @dataclass
        class Config:
            items: list = combine_annotations(
                cli_help("List of items"),
                default_factory=list,
            )

        config = build_config(Config, [])
        assert config.items == []
        assert isinstance(config.items, list)

    def test_multiple_fields_with_combine(self):
        """Test multiple fields using combine_annotations."""

        @dataclass
        class Config:
            field1: str = combine_annotations(
                cli_help("First field"),
                cli_file_loadable(),
                default="default1",
            )
            field2: str = combine_annotations(
                cli_help("Second field"),
                cli_file_loadable(),
                default="default2",
            )
            field3: str = cli_help("Third field", default="default3")

        config = build_config(Config, ["--field1", "value1", "--field2", "value2"])
        assert config.field1 == "value1"
        assert config.field2 == "value2"
        assert config.field3 == "default3"

    def test_combine_with_exclude(self):
        """Test that combine_annotations works with cli_exclude."""

        @dataclass
        class Config:
            visible: str = combine_annotations(
                cli_help("Visible field"),
                default="visible",
            )
            hidden: str = combine_annotations(
                cli_exclude(),
                default="hidden",
            )

        # Hidden field should not be accessible via CLI
        config = build_config(Config, ["--visible", "test"])
        assert config.visible == "test"
        assert config.hidden == "hidden"

    def test_combine_metadata_overwrite(self):
        """Test that later annotations override earlier ones for same key."""

        @dataclass
        class Config:
            field: str = combine_annotations(
                cli_help("First help"),
                cli_help("Second help"),  # Should override first
                default="default",
            )

        field_map = {f.name: f for f in fields(Config)}
        test_field = field_map["field"]

        # Later help should win
        assert test_field.metadata["cli_help"] == "Second help"

    def test_combine_empty_annotations(self):
        """Test combine_annotations with no annotations (just kwargs)."""

        @dataclass
        class Config:
            field: str = combine_annotations(default="just a default")

        config = build_config(Config, ["--field", "value"])
        assert config.field == "value"

    def test_combine_with_existing_metadata(self):
        """Test combine_annotations with pre-existing metadata dict."""

        @dataclass
        class Config:
            field: str = combine_annotations(
                cli_help("Help text"),
                cli_file_loadable(),
                metadata={"custom_key": "custom_value"},
                default="default",
            )

        field_map = {f.name: f for f in fields(Config)}
        test_field = field_map["field"]

        # Should have all metadata
        assert "cli_help" in test_field.metadata
        assert "cli_file_loadable" in test_field.metadata
        assert "custom_key" in test_field.metadata
        assert test_field.metadata["custom_key"] == "custom_value"

    def test_combine_help_shown_in_parser(self):
        """Test that combined help text appears in argument parser."""
        import argparse

        from dataclass_args import GenericConfigBuilder

        @dataclass
        class Config:
            message: str = combine_annotations(
                cli_help("Message content"),
                cli_file_loadable(),
                default="default",
            )

        builder = GenericConfigBuilder(Config)
        parser = argparse.ArgumentParser()
        builder.add_arguments(parser)

        # Get help text
        help_text = parser.format_help()

        # Should contain the help text
        assert "Message content" in help_text
        # Should contain file loading hint
        assert "supports @file.txt" in help_text or "@file" in help_text.lower()
