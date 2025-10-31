"""
Tests for file loading functionality.
"""

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from dataclass_cli import build_config_from_cli, cli_file_loadable, cli_help
from dataclass_cli.exceptions import FileLoadingError
from dataclass_cli.file_loading import (
    is_file_loadable_value,
    load_file_content,
    process_file_loadable_value,
)


@dataclass
class FileLoadableConfig:
    # Fields without defaults must come first
    welcome_message: str = cli_file_loadable()  # No default - must be first
    name: str = cli_help("Application name")
    system_prompt: str = cli_file_loadable(default="You are helpful")
    regular_field: str = "not file loadable"


class TestFileLoadingFunctions:
    """Test core file loading functions."""

    def test_is_file_loadable_value(self):
        """Test detection of file-loadable values."""
        assert is_file_loadable_value("@file.txt") is True
        assert is_file_loadable_value("@") is True
        assert is_file_loadable_value("@/path/to/file.txt") is True
        assert is_file_loadable_value("regular string") is False
        assert is_file_loadable_value("") is False
        assert is_file_loadable_value(123) is False
        assert is_file_loadable_value(None) is False

    def test_load_file_content_success(self):
        """Test successful file content loading."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            test_content = "Hello, World!\nThis is a test file."
            f.write(test_content)
            f.flush()

            try:
                content = load_file_content(f.name)
                assert content == test_content
            finally:
                os.unlink(f.name)

    def test_load_file_content_not_found(self):
        """Test error when file doesn't exist."""
        with pytest.raises(FileLoadingError, match="File not found"):
            load_file_content("/nonexistent/file.txt")

    def test_load_file_content_not_file(self):
        """Test error when path is not a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(FileLoadingError, match="Path is not a file"):
                load_file_content(temp_dir)

    def test_load_file_content_unreadable(self):
        """Test error when file is not readable."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            f.flush()

            try:
                # Remove read permissions
                os.chmod(f.name, 0o000)

                with pytest.raises(FileLoadingError, match="File is not readable"):
                    load_file_content(f.name)
            finally:
                # Restore permissions and clean up
                os.chmod(f.name, 0o644)
                os.unlink(f.name)

    def test_process_file_loadable_value_literal(self):
        """Test processing literal (non-file) values."""
        result = process_file_loadable_value("literal value", "test_field")
        assert result == "literal value"

        result = process_file_loadable_value(123, "test_field")
        assert result == 123

    def test_process_file_loadable_value_file(self):
        """Test processing file-loadable values."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            test_content = "File content loaded successfully!"
            f.write(test_content)
            f.flush()

            try:
                result = process_file_loadable_value(f"@{f.name}", "test_field")
                assert result == test_content
            finally:
                os.unlink(f.name)

    def test_process_file_loadable_value_empty_path(self):
        """Test error when file path is empty."""
        with pytest.raises(ValueError, match="Empty file path"):
            process_file_loadable_value("@", "test_field")

    def test_process_file_loadable_value_file_error(self):
        """Test error propagation from file loading."""
        with pytest.raises(ValueError, match="Failed to process field"):
            process_file_loadable_value("@/nonexistent/file.txt", "test_field")


class TestFileLoadableConfig:
    """Test file loading in CLI configuration."""

    def test_literal_values(self):
        """Test using literal values (no file loading)."""
        config = build_config_from_cli(
            FileLoadableConfig,
            [
                "--welcome-message",
                "Welcome to the test!",
                "--name",
                "TestApp",
                "--system-prompt",
                "You are a test assistant",
            ],
        )

        assert config.welcome_message == "Welcome to the test!"
        assert config.name == "TestApp"
        assert config.system_prompt == "You are a test assistant"
        assert config.regular_field == "not file loadable"

    def test_file_loading(self):
        """Test loading content from files."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as system_file:
            system_content = "You are an expert assistant with deep knowledge."
            system_file.write(system_content)
            system_file.flush()

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as welcome_file:
                welcome_content = "Welcome to our advanced AI system!"
                welcome_file.write(welcome_content)
                welcome_file.flush()

                try:
                    config = build_config_from_cli(
                        FileLoadableConfig,
                        [
                            "--welcome-message",
                            f"@{welcome_file.name}",
                            "--name",
                            "FileApp",
                            "--system-prompt",
                            f"@{system_file.name}",
                        ],
                    )

                    assert config.welcome_message == welcome_content
                    assert config.name == "FileApp"
                    assert config.system_prompt == system_content

                finally:
                    os.unlink(system_file.name)
                    os.unlink(welcome_file.name)

    def test_mixed_literal_and_file(self):
        """Test mixing literal values and file loading."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            file_content = "Content loaded from file"
            f.write(file_content)
            f.flush()

            try:
                config = build_config_from_cli(
                    FileLoadableConfig,
                    [
                        "--welcome-message",
                        f"@{f.name}",  # File
                        "--name",
                        "MixedApp",
                        "--system-prompt",
                        "Literal prompt text",  # Literal
                    ],
                )

                assert config.welcome_message == file_content
                assert config.name == "MixedApp"
                assert config.system_prompt == "Literal prompt text"

            finally:
                os.unlink(f.name)

    def test_default_values_with_file_loadable(self):
        """Test that default values work with file-loadable fields."""
        config = build_config_from_cli(
            FileLoadableConfig,
            [
                "--welcome-message",
                "Welcome message",
                "--name",
                "DefaultApp",
                # system_prompt should use default
            ],
        )

        assert config.welcome_message == "Welcome message"
        assert config.name == "DefaultApp"
        assert config.system_prompt == "You are helpful"  # Default value

    def test_file_loading_error_handling(self):
        """Test error handling when file loading fails."""
        # Test that configuration errors are properly raised (not SystemExit)
        from dataclass_cli.exceptions import ConfigurationError

        with pytest.raises((SystemExit, ConfigurationError, ValueError)):
            build_config_from_cli(
                FileLoadableConfig,
                [
                    "--welcome-message",
                    "test",
                    "--name",
                    "ErrorApp",
                    "--system-prompt",
                    "@/nonexistent/file.txt",
                ],
            )

    def test_utf8_encoding(self):
        """Test that files are properly read as UTF-8."""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            unicode_content = "Hello 世界! Café naïve résumé 🚀"
            f.write(unicode_content)
            f.flush()

            try:
                config = build_config_from_cli(
                    FileLoadableConfig,
                    [
                        "--welcome-message",
                        "Welcome",
                        "--name",
                        "UnicodeApp",
                        "--system-prompt",
                        f"@{f.name}",
                    ],
                )

                assert config.system_prompt == unicode_content

            finally:
                os.unlink(f.name)


class TestFileLoadableEdgeCases:
    """Test edge cases for file loading."""

    def test_empty_file(self):
        """Test loading an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # Write empty content
            f.write("")
            f.flush()

            try:
                config = build_config_from_cli(
                    FileLoadableConfig,
                    [
                        "--welcome-message",
                        "Welcome",
                        "--name",
                        "EmptyApp",
                        "--system-prompt",
                        f"@{f.name}",
                    ],
                )

                assert config.system_prompt == ""

            finally:
                os.unlink(f.name)

    def test_whitespace_only_file(self):
        """Test loading a file with only whitespace."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            whitespace_content = "   \n\t  \n  "
            f.write(whitespace_content)
            f.flush()

            try:
                config = build_config_from_cli(
                    FileLoadableConfig,
                    [
                        "--welcome-message",
                        "Welcome",
                        "--name",
                        "WhitespaceApp",
                        "--system-prompt",
                        f"@{f.name}",
                    ],
                )

                assert config.system_prompt == whitespace_content

            finally:
                os.unlink(f.name)

    def test_large_file(self):
        """Test loading a reasonably large file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # Create a file with ~1MB of content
            large_content = "This is a test line.\n" * 50000
            f.write(large_content)
            f.flush()

            try:
                config = build_config_from_cli(
                    FileLoadableConfig,
                    [
                        "--welcome-message",
                        "Welcome",
                        "--name",
                        "LargeApp",
                        "--system-prompt",
                        f"@{f.name}",
                    ],
                )

                assert config.system_prompt == large_content
                assert len(config.system_prompt) > 1000000  # ~1MB

            finally:
                os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__])
