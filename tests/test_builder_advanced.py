"""
Advanced tests for builder module - dict configs, overrides, and error handling.
"""

import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pytest

from dataclass_cli import GenericConfigBuilder, build_config, build_config_from_cli
from dataclass_cli.annotations import cli_exclude, cli_help
from dataclass_cli.exceptions import ConfigBuilderError, ConfigurationError


class TestDictConfigLoading:
    """Tests for dictionary configuration loading from files."""

    @dataclass
    class ServerConfig:
        name: str
        settings: Optional[Dict[str, any]] = None

    def test_load_dict_from_json_file(self):
        """Should load dict field from JSON file."""
        # Create settings file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            settings = {"host": "localhost", "port": 8080, "debug": True}
            json.dump(settings, f)
            settings_path = f.name

        try:
            config = build_config(
                self.ServerConfig,
                ["--name", "test-server", "--settings", settings_path],
            )

            assert config.name == "test-server"
            assert config.settings["host"] == "localhost"
            assert config.settings["port"] == 8080
            assert config.settings["debug"] is True
        finally:
            Path(settings_path).unlink()

    def test_merge_dict_with_base_config(self):
        """Should merge dict from CLI with base config dict."""
        # Create base config with initial settings
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            base_config = {"name": "base", "settings": {"timeout": 30, "retry": 3}}
            json.dump(base_config, f)
            base_path = f.name

        # Create CLI settings file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            cli_settings = {"host": "localhost", "port": 8080}
            json.dump(cli_settings, f)
            settings_path = f.name

        try:
            config = build_config(
                self.ServerConfig,
                ["--config", base_path, "--settings", settings_path],
            )

            # Should merge settings
            assert config.settings["timeout"] == 30  # From base
            assert config.settings["retry"] == 3  # From base
            assert config.settings["host"] == "localhost"  # From CLI
            assert config.settings["port"] == 8080  # From CLI
        finally:
            Path(base_path).unlink()
            Path(settings_path).unlink()

    def test_dict_loading_error(self):
        """Should raise ConfigurationError for invalid dict file."""
        with pytest.raises(ConfigurationError, match="Failed to load dictionary"):
            build_config(
                self.ServerConfig,
                ["--name", "test", "--settings", "/nonexistent/file.json"],
            )

    def test_dict_with_invalid_json(self):
        """Should raise ConfigurationError for malformed dict file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            invalid_path = f.name

        try:
            with pytest.raises(ConfigurationError, match="Failed to load dictionary"):
                build_config(
                    self.ServerConfig, ["--name", "test", "--settings", invalid_path]
                )
        finally:
            Path(invalid_path).unlink()


class TestPropertyOverrides:
    """Tests for property override functionality."""

    @dataclass
    class AppConfig:
        name: str
        settings: Optional[Dict[str, any]] = None

    def test_property_override_simple(self):
        """Should apply simple property override."""
        # Create settings file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            settings = {"host": "localhost", "port": 8080}
            json.dump(settings, f)
            settings_path = f.name

        try:
            config = build_config(
                self.AppConfig,
                [
                    "--name",
                    "test",
                    "--settings",
                    settings_path,
                    "--s",
                    "port:9000",  # Override port
                ],
            )

            assert config.settings["host"] == "localhost"
            assert config.settings["port"] == 9000  # Overridden
        finally:
            Path(settings_path).unlink()

    def test_property_override_nested(self):
        """Should apply nested property override using dot notation."""
        # Create settings file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            settings = {"database": {"host": "localhost", "port": 5432}}
            json.dump(settings, f)
            settings_path = f.name

        try:
            config = build_config(
                self.AppConfig,
                [
                    "--name",
                    "test",
                    "--settings",
                    settings_path,
                    "--s",
                    "database.host:remote.example.com",
                ],
            )

            assert config.settings["database"]["host"] == "remote.example.com"
            assert config.settings["database"]["port"] == 5432
        finally:
            Path(settings_path).unlink()

    def test_property_override_creates_nested_structure(self):
        """Should create nested structure if it doesn't exist."""
        # Create settings file with minimal content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            settings_path = f.name

        try:
            config = build_config(
                self.AppConfig,
                [
                    "--name",
                    "test",
                    "--settings",
                    settings_path,
                    "--s",
                    "new.nested.value:42",
                ],
            )

            assert config.settings["new"]["nested"]["value"] == 42
        finally:
            Path(settings_path).unlink()

    def test_property_override_multiple(self):
        """Should apply multiple property overrides."""
        # Create settings file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"a": 1, "b": 2}, f)
            settings_path = f.name

        try:
            config = build_config(
                self.AppConfig,
                [
                    "--name",
                    "test",
                    "--settings",
                    settings_path,
                    "--s",
                    "a:10",
                    "--s",
                    "b:20",
                    "--s",
                    "c:30",
                ],
            )

            assert config.settings["a"] == 10
            assert config.settings["b"] == 20
            assert config.settings["c"] == 30
        finally:
            Path(settings_path).unlink()

    def test_property_override_invalid_format(self):
        """Should raise ConfigurationError for invalid override format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            settings_path = f.name

        try:
            with pytest.raises(
                ConfigurationError, match="Invalid override format.*expected"
            ):
                build_config(
                    self.AppConfig,
                    [
                        "--name",
                        "test",
                        "--settings",
                        settings_path,
                        "--s",
                        "invalid_no_colon",
                    ],
                )
        finally:
            Path(settings_path).unlink()

    def test_property_override_json_values(self):
        """Should parse override values as JSON when possible."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            settings_path = f.name

        try:
            config = build_config(
                self.AppConfig,
                [
                    "--name",
                    "test",
                    "--settings",
                    settings_path,
                    "--s",
                    "number:42",
                    "--s",
                    "boolean:true",
                    "--s",
                    "string:hello",
                ],
            )

            assert config.settings["number"] == 42  # int, not string
            assert config.settings["boolean"] is True  # boolean, not string
            assert config.settings["string"] == "hello"  # string
        finally:
            Path(settings_path).unlink()

    def test_property_override_without_dict_file(self):
        """Should work with overrides even without dict file."""
        config = build_config(self.AppConfig, ["--name", "test", "--s", "key:value"])

        assert config.settings["key"] == "value"


class TestBuilderErrorHandling:
    """Tests for error handling in GenericConfigBuilder."""

    def test_non_dataclass_error(self):
        """Should raise ConfigBuilderError for non-dataclass type."""

        class NotADataclass:
            name: str

        with pytest.raises(ConfigBuilderError, match="must be a dataclass"):
            GenericConfigBuilder(NotADataclass)

    def test_conflicting_filters_error(self):
        """Should raise ConfigBuilderError for conflicting include/exclude filters."""

        @dataclass
        class TestConfig:
            name: str

        with pytest.raises(
            ConfigBuilderError,
            match="Cannot specify both exclude_fields and include_fields",
        ):
            GenericConfigBuilder(
                TestConfig, exclude_fields={"name"}, include_fields={"name"}
            )

    def test_base_config_loading_error(self):
        """Should raise ConfigurationError for invalid base config."""

        @dataclass
        class TestConfig:
            name: str

        with pytest.raises(ConfigurationError, match="Failed to load base config"):
            build_config(TestConfig, ["--config", "/nonexistent/config.json"])

    def test_dataclass_instantiation_error(self):
        """Should raise ConfigurationError when dataclass creation fails."""

        @dataclass
        class StrictConfig:
            name: str
            count: int  # Required, no default

        # Missing required field 'count'
        with pytest.raises(ConfigurationError, match="Failed to create.*StrictConfig"):
            build_config(StrictConfig, ["--name", "test"])


class TestBuilderFieldFiltering:
    """Tests for field filtering mechanisms."""

    @dataclass
    class FilterableConfig:
        public_field: str = "public"
        _internal_field: str = cli_exclude(default="internal")
        excluded_field: str = "excluded"
        included_field: str = "included"

    def test_exclude_fields_parameter(self):
        """Should exclude specified fields from CLI."""
        builder = GenericConfigBuilder(
            self.FilterableConfig, exclude_fields={"excluded_field"}
        )

        # excluded_field should not be in config fields
        assert "excluded_field" not in builder._config_fields
        assert "public_field" in builder._config_fields
        assert "included_field" in builder._config_fields

    def test_include_fields_parameter(self):
        """Should only include specified fields in CLI."""
        builder = GenericConfigBuilder(
            self.FilterableConfig, include_fields={"included_field"}
        )

        # Only included_field should be in config fields (excluding cli_exclude)
        assert "included_field" in builder._config_fields
        assert "public_field" not in builder._config_fields
        assert "excluded_field" not in builder._config_fields

    def test_custom_field_filter(self):
        """Should apply custom field filter function."""

        def only_long_names(field_name: str, field_info) -> bool:
            return len(field_name) > 10

        builder = GenericConfigBuilder(
            self.FilterableConfig, field_filter=only_long_names, use_annotations=False
        )

        # Only fields with names longer than 10 chars
        # public_field = 12 chars, _internal_field = 15 chars
        # excluded_field = 14 chars, included_field = 14 chars
        assert "public_field" in builder._config_fields
        assert "_internal_field" in builder._config_fields
        assert "excluded_field" in builder._config_fields
        assert "included_field" in builder._config_fields

    def test_annotations_respected_by_default(self):
        """Should respect cli_exclude annotations by default."""
        builder = GenericConfigBuilder(self.FilterableConfig)

        # _internal_field has cli_exclude annotation
        assert "_internal_field" not in builder._config_fields

    def test_annotations_can_be_disabled(self):
        """Should ignore annotations when use_annotations=False."""
        builder = GenericConfigBuilder(self.FilterableConfig, use_annotations=False)

        # With annotations disabled, _internal_field should be included
        assert "_internal_field" in builder._config_fields


class TestBuilderConvenienceFunctions:
    """Tests for convenience functions."""

    @dataclass
    class SimpleConfig:
        name: str
        count: int = 10

    def test_build_config_uses_sys_argv_by_default(self, monkeypatch):
        """build_config should use sys.argv when args not provided."""
        # Mock sys.argv
        monkeypatch.setattr(
            sys, "argv", ["prog", "--name", "from-argv", "--count", "5"]
        )

        config = build_config(self.SimpleConfig)
        assert config.name == "from-argv"
        assert config.count == 5

    def test_build_config_explicit_args(self):
        """build_config should accept explicit args list."""
        config = build_config(self.SimpleConfig, ["--name", "explicit", "--count", "3"])

        assert config.name == "explicit"
        assert config.count == 3

    def test_build_config_from_cli_all_parameters(self):
        """build_config_from_cli should accept all configuration parameters."""
        config = build_config_from_cli(
            self.SimpleConfig,
            args=["--name", "test"],
            base_config_name="config",
            exclude_fields=set(),
            include_fields=None,
            field_filter=None,
            use_annotations=True,
        )

        assert config.name == "test"
        assert config.count == 10  # default value


class TestBuilderComplexScenarios:
    """Tests for complex real-world scenarios."""

    @dataclass
    class ComplexConfig:
        name: str
        items: Optional[List[str]] = None
        settings: Optional[Dict[str, any]] = None
        debug: bool = False

    def test_multiple_list_items(self):
        """Should accumulate multiple list items."""
        config = build_config(
            self.ComplexConfig,
            ["--name", "test", "--items", "a", "b", "c"],
        )

        assert config.items == ["a", "b", "c"]

    def test_combined_dict_and_overrides(self):
        """Should combine dict file loading with overrides."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key1": "value1", "key2": "value2"}, f)
            settings_path = f.name

        try:
            config = build_config(
                self.ComplexConfig,
                [
                    "--name",
                    "test",
                    "--settings",
                    settings_path,
                    "--s",
                    "key2:overridden",
                    "--s",
                    "key3:new",
                ],
            )

            assert config.settings["key1"] == "value1"  # From file
            assert config.settings["key2"] == "overridden"  # Overridden
            assert config.settings["key3"] == "new"  # Added
        finally:
            Path(settings_path).unlink()

    def test_all_features_combined(self):
        """Should handle base config + CLI dict + overrides + lists."""
        # Create base config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            base = {"name": "base", "items": ["base1"], "debug": False}
            json.dump(base, f)
            base_path = f.name

        # Create settings file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            settings = {"original": "value"}
            json.dump(settings, f)
            settings_path = f.name

        try:
            config = build_config(
                self.ComplexConfig,
                [
                    "--config",
                    base_path,
                    "--name",
                    "overridden",
                    "--items",
                    "cli1",
                    "cli2",
                    "--settings",
                    settings_path,
                    "--s",
                    "added:override",
                    "--debug",
                ],
            )

            assert config.name == "overridden"  # CLI override
            assert config.items == ["cli1", "cli2"]  # CLI replaces base
            assert config.settings["original"] == "value"  # From file
            assert config.settings["added"] == "override"  # From override
            assert config.debug is True  # CLI override
        finally:
            Path(base_path).unlink()
            Path(settings_path).unlink()
