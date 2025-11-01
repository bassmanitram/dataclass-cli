"""
Comprehensive tests for annotation functionality.
"""

from dataclasses import dataclass, field
from typing import Optional

import pytest

from dataclass_args import build_config, cli_exclude, cli_file_loadable, cli_help
from dataclass_args.annotations import (
    get_cli_help,
    is_cli_excluded,
    is_cli_file_loadable,
)


class TestCliHelpAnnotation:
    """Tests for cli_help annotation."""

    def test_cli_help_basic(self):
        """Should set help text for field."""

        @dataclass
        class Config:
            name: str = cli_help("The service name")

        # Check that help text is retrievable
        field_info = {"field_obj": Config.__dataclass_fields__["name"]}
        help_text = get_cli_help(field_info)
        assert help_text == "The service name"

    def test_cli_help_with_default(self):
        """Should combine help text with default value."""

        @dataclass
        class Config:
            port: int = cli_help("Server port", default=8080)

        config = build_config(Config, [])
        assert config.port == 8080

    def test_cli_help_separate_fields(self):
        """Annotations are per-field, not composable."""

        @dataclass
        class Config:
            public: str = cli_help("Public field")
            secret: str = cli_exclude(default="hidden")

        # Each field has its own annotation
        public_info = {"field_obj": Config.__dataclass_fields__["public"]}
        secret_info = {"field_obj": Config.__dataclass_fields__["secret"]}

        assert get_cli_help(public_info) == "Public field"
        assert is_cli_excluded(secret_info)

    def test_multiple_fields_with_help(self):
        """Should handle multiple fields with help text."""

        @dataclass
        class Config:
            name: str = cli_help("Service name")
            host: str = cli_help("Server hostname")
            port: int = cli_help("Server port", default=8080)

        # Verify each field has its help text
        for field_name, expected_help in [
            ("name", "Service name"),
            ("host", "Server hostname"),
            ("port", "Server port"),
        ]:
            field_info = {"field_obj": Config.__dataclass_fields__[field_name]}
            assert get_cli_help(field_info) == expected_help


class TestCliExcludeAnnotation:
    """Tests for cli_exclude annotation."""

    def test_cli_exclude_basic(self):
        """Should exclude field from CLI arguments."""

        @dataclass
        class Config:
            public: str
            private: str = cli_exclude(default="secret")

        # Build config should work without private field
        config = build_config(Config, ["--public", "visible"])
        assert config.public == "visible"
        assert config.private == "secret"

    def test_cli_exclude_detection(self):
        """Should detect cli_exclude annotation."""

        @dataclass
        class Config:
            excluded: str = cli_exclude(default="hidden")

        field_info = {"field_obj": Config.__dataclass_fields__["excluded"]}
        assert is_cli_excluded(field_info)

    def test_cli_exclude_with_factory(self):
        """Should work with default_factory."""

        @dataclass
        class Config:
            name: str
            internal_list: list = cli_exclude(default_factory=list)

        config = build_config(Config, ["--name", "test"])
        assert config.name == "test"
        assert config.internal_list == []

    def test_cli_exclude_optional_field(self):
        """Should work with optional fields."""

        @dataclass
        class Config:
            public: str
            internal: Optional[str] = cli_exclude(default=None)

        config = build_config(Config, ["--public", "test"])
        assert config.internal is None

    def test_multiple_excluded_fields(self):
        """Should handle multiple excluded fields."""

        @dataclass
        class Config:
            public1: str
            private1: str = cli_exclude(default="secret1")
            public2: str = "visible"
            private2: str = cli_exclude(default="secret2")

        config = build_config(Config, ["--public1", "test1", "--public2", "test2"])
        assert config.public1 == "test1"
        assert config.public2 == "test2"
        assert config.private1 == "secret1"
        assert config.private2 == "secret2"


class TestCliFileLoadableAnnotation:
    """Tests for cli_file_loadable annotation."""

    def test_cli_file_loadable_basic(self):
        """Should mark field as file-loadable."""

        @dataclass
        class Config:
            message: str = cli_file_loadable(default="default message")

        field_info = {"field_obj": Config.__dataclass_fields__["message"]}
        assert is_cli_file_loadable(field_info)

    def test_cli_file_loadable_with_literal_value(self):
        """Should accept literal value without @ prefix."""

        @dataclass
        class Config:
            message: str = cli_file_loadable(default="")

        config = build_config(Config, ["--message", "literal value"])
        assert config.message == "literal value"

    def test_cli_file_loadable_with_file(self, tmp_path):
        """Should load content from file with @ prefix."""
        import tempfile

        # Create temporary file with content
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("file content")
            file_path = f.name

        try:

            @dataclass
            class Config:
                message: str = cli_file_loadable(default="")

            config = build_config(Config, ["--message", f"@{file_path}"])
            assert config.message == "file content"
        finally:
            import os

            os.unlink(file_path)

    def test_cli_file_loadable_with_manual_metadata(self):
        """Should work when setting metadata manually."""

        @dataclass
        class Config:
            # Manual metadata setting for combined annotations
            prompt: str = field(
                default="",
                metadata={"cli_help": "System prompt text", "cli_file_loadable": True},
            )

        field_info = {"field_obj": Config.__dataclass_fields__["prompt"]}
        assert is_cli_file_loadable(field_info)
        # Note: get_cli_help will append file-loadable hint
        help_text = get_cli_help(field_info)
        assert "System prompt text" in help_text
        assert "file" in help_text.lower()


class TestAnnotationEdgeCases:
    """Edge case tests for annotations."""

    def test_field_without_annotations(self):
        """Should handle fields without any annotations."""

        @dataclass
        class Config:
            plain_field: str

        field_info = {"field_obj": Config.__dataclass_fields__["plain_field"]}
        assert not is_cli_excluded(field_info)
        assert not is_cli_file_loadable(field_info)
        # get_cli_help returns empty string, not None
        assert get_cli_help(field_info) == ""

    def test_field_with_field_function(self):
        """Should work with dataclass field() function."""

        @dataclass
        class Config:
            name: str = field(default="test", metadata={"cli_help": "Name field"})

        field_info = {"field_obj": Config.__dataclass_fields__["name"]}
        # Should be able to retrieve metadata
        assert "cli_help" in Config.__dataclass_fields__["name"].metadata
        assert get_cli_help(field_info) == "Name field"

    def test_annotation_with_none_default(self):
        """Should handle None as default value."""

        @dataclass
        class Config:
            optional: Optional[str] = cli_help("Optional field", default=None)

        config = build_config(Config, [])
        assert config.optional is None

    def test_combined_metadata_manually(self):
        """Should handle manually combined metadata."""

        @dataclass
        class Config:
            # Manual metadata combination for complex cases
            data: str = field(
                default="default data",
                metadata={
                    "cli_help": "Data content or file path",
                    "cli_file_loadable": True,
                },
            )

        field_info = {"field_obj": Config.__dataclass_fields__["data"]}
        assert is_cli_file_loadable(field_info)
        help_text = get_cli_help(field_info)
        assert "Data content or file path" in help_text

        # Should use default when not provided
        config = build_config(Config, [])
        assert config.data == "default data"


class TestAnnotationHelperFunctions:
    """Tests for annotation helper functions."""

    def test_get_cli_help_returns_empty_string_for_no_help(self):
        """get_cli_help should return empty string when no help text set."""

        @dataclass
        class Config:
            field: str = "default"

        field_info = {"field_obj": Config.__dataclass_fields__["field"]}
        # Returns empty string, not None
        assert get_cli_help(field_info) == ""

    def test_is_cli_excluded_false_by_default(self):
        """is_cli_excluded should return False for non-excluded fields."""

        @dataclass
        class Config:
            field: str

        field_info = {"field_obj": Config.__dataclass_fields__["field"]}
        assert not is_cli_excluded(field_info)

    def test_is_cli_file_loadable_false_by_default(self):
        """is_cli_file_loadable should return False for non-file-loadable fields."""

        @dataclass
        class Config:
            field: str

        field_info = {"field_obj": Config.__dataclass_fields__["field"]}
        assert not is_cli_file_loadable(field_info)

    def test_helper_functions_handle_missing_field_obj(self):
        """Helper functions should handle missing field_obj gracefully."""
        empty_info = {}

        # Should not crash, return False/empty string
        assert get_cli_help(empty_info) == ""
        assert not is_cli_excluded(empty_info)
        assert not is_cli_file_loadable(empty_info)


class TestAnnotationInRealScenarios:
    """Test annotations in realistic use cases."""

    def test_service_config_with_mixed_annotations(self):
        """Realistic service configuration with various annotations."""

        @dataclass
        class ServiceConfig:
            # Public fields with help
            name: str = cli_help("Service name")
            host: str = cli_help("Service hostname", default="localhost")
            port: int = cli_help("Service port", default=8080)

            # File-loadable fields
            system_prompt: str = field(
                default="You are helpful.",
                metadata={
                    "cli_help": "System prompt text or file path",
                    "cli_file_loadable": True,
                },
            )

            # Internal/private fields
            _internal_id: str = cli_exclude(default="service-001")
            _secret_key: str = cli_exclude(default="secret")

        config = build_config(
            ServiceConfig,
            [
                "--name",
                "my-service",
                "--port",
                "9000",
                "--system-prompt",
                "Custom prompt",
            ],
        )

        assert config.name == "my-service"
        assert config.host == "localhost"  # default
        assert config.port == 9000
        assert config.system_prompt == "Custom prompt"
        assert config._internal_id == "service-001"
        assert config._secret_key == "secret"

    def test_database_config_with_excluded_credentials(self):
        """Database config with excluded credential fields."""

        @dataclass
        class DatabaseConfig:
            host: str = cli_help("Database host")
            port: int = cli_help("Database port", default=5432)
            database: str = cli_help("Database name", default="postgres")

            # These are set programmatically, not via CLI
            username: str = cli_exclude(default="")
            password: str = cli_exclude(default="")

        config = build_config(
            DatabaseConfig,
            ["--host", "db.example.com", "--database", "mydb"],
        )

        assert config.host == "db.example.com"
        assert config.port == 5432
        assert config.database == "mydb"
        assert config.username == ""
        assert config.password == ""

    def test_ai_agent_config_with_file_loadable_prompts(self, tmp_path):
        """AI agent config with file-loadable prompt fields."""
        import tempfile

        # Create prompt file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("You are an expert assistant.")
            prompt_file = f.name

        try:

            @dataclass
            class AgentConfig:
                name: str = cli_help("Agent name")
                model: str = cli_help("Model name", default="gpt-4")
                system_prompt: str = field(
                    default="",
                    metadata={"cli_help": "System prompt", "cli_file_loadable": True},
                )
                user_prompt_template: str = field(
                    default="{input}",
                    metadata={
                        "cli_help": "User prompt template",
                        "cli_file_loadable": True,
                    },
                )

            config = build_config(
                AgentConfig,
                [
                    "--name",
                    "expert",
                    "--system-prompt",
                    f"@{prompt_file}",
                    "--user-prompt-template",
                    "Question: {input}",
                ],
            )

            assert config.name == "expert"
            assert config.model == "gpt-4"
            assert config.system_prompt == "You are an expert assistant."
            assert config.user_prompt_template == "Question: {input}"
        finally:
            import os

            os.unlink(prompt_file)
