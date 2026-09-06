"""Tests for cli_override_name annotation and override collision detection."""

from dataclasses import dataclass, field
from typing import Any, Dict

import pytest

from dataclass_args import (
    build_config_from_cli,
    cli_help,
    cli_override_name,
    combine_annotations,
    get_cli_override_name,
)
from dataclass_args.builder import GenericConfigBuilder
from dataclass_args.exceptions import ConfigBuilderError


class TestCliOverrideName:
    """Test custom override name annotation."""

    def test_custom_override_name_used(self):
        """cli_override_name sets custom override abbreviation."""

        @dataclass
        class Config:
            model_config: Dict[str, Any] = cli_override_name("mc", default_factory=dict)

        build_config_from_cli(Config, args=[])
        # Just verify it builds without error — override name is --mc

    def test_custom_override_name_property_override(self, tmp_path):
        """Property override works with custom override name."""
        import json

        cfg = tmp_path / "base.json"
        cfg.write_text(json.dumps({"key": "value"}))

        @dataclass
        class Config:
            model_config: Dict[str, Any] = cli_override_name("mc", default_factory=dict)

        config = build_config_from_cli(
            Config, args=["--model-config", str(cfg), "--mc", "extra:added"]
        )
        assert config.model_config["key"] == "value"
        assert config.model_config["extra"] == "added"

    def test_custom_override_resolves_collision(self):
        """cli_override_name resolves collision between fields with same initials."""

        @dataclass
        class Config:
            sandbox_config: Dict[str, Any] = field(default_factory=dict)
            skills_config: Dict[str, Any] = cli_override_name(
                "sk", default_factory=dict
            )

        # Should NOT raise — sandbox_config→--sc, skills_config→--sk
        build_config_from_cli(Config, args=[])

    def test_collision_detected_without_annotation(self):
        """Two dict fields with same initials raise ConfigBuilderError."""

        @dataclass
        class Config:
            sandbox_config: Dict[str, Any] = field(default_factory=dict)
            skills_config: Dict[str, Any] = field(default_factory=dict)

        with pytest.raises(ConfigBuilderError, match="Override name collision"):
            GenericConfigBuilder(Config)

    def test_combine_with_other_annotations(self):
        """cli_override_name works with combine_annotations."""

        @dataclass
        class Config:
            model_config: Dict[str, Any] = combine_annotations(
                cli_override_name("mc"),
                cli_help("Model configuration"),
                default_factory=dict,
            )

        build_config_from_cli(Config, args=[])

    def test_get_cli_override_name_accessor(self):
        """get_cli_override_name returns the custom name."""

        @dataclass
        class Config:
            model_config: Dict[str, Any] = cli_override_name("mc", default_factory=dict)

        from dataclasses import fields

        f = fields(Config)[0]
        info = {"field_obj": f}
        assert get_cli_override_name(info) == "mc"

    def test_get_cli_override_name_returns_none(self):
        """get_cli_override_name returns None for unannotated fields."""

        @dataclass
        class Config:
            model_config: Dict[str, Any] = field(default_factory=dict)

        from dataclasses import fields

        f = fields(Config)[0]
        info = {"field_obj": f}
        assert get_cli_override_name(info) is None

    def test_invalid_override_name_empty_string(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            cli_override_name("")

    def test_invalid_override_name_non_string(self):
        """Non-string raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            cli_override_name(123)

    def test_auto_override_unchanged_for_non_colliding(self):
        """Fields without annotation still get auto-generated overrides."""

        @dataclass
        class Config:
            model_config: Dict[str, Any] = field(default_factory=dict)
            server_params: Dict[str, Any] = field(default_factory=dict)

        # mc and sp — no collision
        build_config_from_cli(Config, args=[])
