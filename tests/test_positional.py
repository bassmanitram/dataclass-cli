"""
Tests for positional argument support.
"""

from dataclasses import dataclass
from typing import List, Optional

import pytest

from dataclass_args import (
    ConfigBuilderError,
    build_config,
    cli_choices,
    cli_help,
    cli_positional,
    cli_short,
    combine_annotations,
)


class TestBasicPositional:
    """Tests for basic positional argument functionality."""

    def test_single_required_positional(self):
        """Test single required positional argument."""

        @dataclass
        class Config:
            source: str = cli_positional()

        config = build_config(Config, args=["input.txt"])
        assert config.source == "input.txt"

    def test_multiple_required_positionals(self):
        """Test multiple required positional arguments."""

        @dataclass
        class Config:
            source: str = cli_positional()
            dest: str = cli_positional()

        config = build_config(Config, args=["input.txt", "output.txt"])
        assert config.source == "input.txt"
        assert config.dest == "output.txt"

    def test_positional_with_help(self):
        """Test positional with custom help text."""

        @dataclass
        class Config:
            source: str = cli_positional(help="Source file path")

        config = build_config(Config, args=["test.txt"])
        assert config.source == "test.txt"

    def test_positional_with_metavar(self):
        """Test positional with custom metavar."""

        @dataclass
        class Config:
            source: str = cli_positional(metavar="FILE")

        config = build_config(Config, args=["test.txt"])
        assert config.source == "test.txt"

    def test_positional_with_type_conversion(self):
        """Test positional with type conversion."""

        @dataclass
        class Config:
            count: int = cli_positional()
            rate: float = cli_positional()

        config = build_config(Config, args=["42", "3.14"])
        assert config.count == 42
        assert config.rate == 3.14


class TestOptionalPositional:
    """Tests for optional positional arguments (nargs='?')."""

    def test_optional_positional_provided(self):
        """Test optional positional when value is provided."""

        @dataclass
        class Config:
            input: str = cli_positional()
            output: str = cli_positional(nargs="?", default="stdout")

        config = build_config(Config, args=["input.txt", "output.txt"])
        assert config.input == "input.txt"
        assert config.output == "output.txt"

    def test_optional_positional_omitted(self):
        """Test optional positional when value is omitted."""

        @dataclass
        class Config:
            input: str = cli_positional()
            output: str = cli_positional(nargs="?", default="stdout")

        config = build_config(Config, args=["input.txt"])
        assert config.input == "input.txt"
        assert config.output == "stdout"


class TestPositionalList:
    """Tests for positional list arguments (nargs='*', '+', int)."""

    def test_positional_list_one_or_more(self):
        """Test positional list with nargs='+'."""

        @dataclass
        class Config:
            command: str = cli_positional()
            files: List[str] = cli_positional(nargs="+")

        config = build_config(Config, args=["commit", "f1.txt", "f2.txt", "f3.txt"])
        assert config.command == "commit"
        assert config.files == ["f1.txt", "f2.txt", "f3.txt"]

    def test_positional_list_zero_or_more(self):
        """Test positional list with nargs='*'."""

        @dataclass
        class Config:
            command: str = cli_positional()
            files: List[str] = cli_positional(nargs="*", default_factory=list)

        # With files
        config1 = build_config(Config, args=["commit", "f1.txt", "f2.txt"])
        assert config1.command == "commit"
        assert config1.files == ["f1.txt", "f2.txt"]

        # Without files
        config2 = build_config(Config, args=["commit"])
        assert config2.command == "commit"
        assert config2.files == []

    def test_positional_list_exact_count(self):
        """Test positional list with exact count."""

        @dataclass
        class Config:
            coordinates: List[float] = cli_positional(nargs=2, metavar="X Y")

        config = build_config(Config, args=["1.5", "2.5"])
        assert config.coordinates == [1.5, 2.5]

    def test_positional_list_as_last_argument(self):
        """Test that positional list can be the last argument."""

        @dataclass
        class Config:
            cmd: str = cli_positional()
            opt1: int = cli_positional()
            files: List[str] = cli_positional(nargs="+")

        config = build_config(Config, args=["commit", "5", "a.txt", "b.txt"])
        assert config.cmd == "commit"
        assert config.opt1 == 5
        assert config.files == ["a.txt", "b.txt"]


class TestPositionalWithOptional:
    """Tests for mixing positional and optional arguments."""

    def test_positional_with_optional_flag(self):
        """Test positional mixed with optional flag."""

        @dataclass
        class Config:
            source: str = cli_positional()
            dest: str = cli_positional()
            verbose: bool = cli_short("v", default=False)

        config = build_config(Config, args=["in.txt", "out.txt", "-v"])
        assert config.source == "in.txt"
        assert config.dest == "out.txt"
        assert config.verbose is True

    def test_positional_with_optional_value(self):
        """Test positional mixed with optional value argument."""

        @dataclass
        class Config:
            input: str = cli_positional()
            output: str = cli_positional()
            format: str = cli_short("f", default="json")

        config = build_config(Config, args=["in.txt", "out.txt", "-f", "yaml"])
        assert config.input == "in.txt"
        assert config.output == "out.txt"
        assert config.format == "yaml"

    def test_positional_with_optional_list(self):
        """Test positional with optional list (using flag)."""

        @dataclass
        class Config:
            input: str = cli_positional()
            items: List[str] = cli_short("i", default_factory=list)

        config = build_config(Config, args=["in.txt", "--items", "a", "b", "c"])
        assert config.input == "in.txt"
        assert config.items == ["a", "b", "c"]

    def test_flags_can_appear_anywhere(self):
        """Test that optional flags can appear before or after positionals."""

        @dataclass
        class Config:
            source: str = cli_positional()
            dest: str = cli_positional()
            verbose: bool = cli_short("v", default=False)

        # Flags before positionals
        config1 = build_config(Config, args=["-v", "in.txt", "out.txt"])
        assert config1.source == "in.txt"
        assert config1.dest == "out.txt"
        assert config1.verbose is True

        # Flags after positionals
        config2 = build_config(Config, args=["in.txt", "out.txt", "-v"])
        assert config2.source == "in.txt"
        assert config2.dest == "out.txt"
        assert config2.verbose is True

        # Flags between positionals
        config3 = build_config(Config, args=["in.txt", "-v", "out.txt"])
        assert config3.source == "in.txt"
        assert config3.dest == "out.txt"
        assert config3.verbose is True


class TestPositionalWithChoices:
    """Tests for positional arguments with choices."""

    def test_positional_with_valid_choice(self):
        """Test positional with choices - valid choice."""

        @dataclass
        class Config:
            command: str = combine_annotations(
                cli_positional(), cli_choices(["start", "stop", "restart"])
            )

        config = build_config(Config, args=["start"])
        assert config.command == "start"

    def test_positional_with_invalid_choice(self):
        """Test positional with choices - invalid choice."""

        @dataclass
        class Config:
            command: str = combine_annotations(
                cli_positional(), cli_choices(["start", "stop", "restart"])
            )

        with pytest.raises(SystemExit):  # argparse exits on invalid choice
            build_config(Config, args=["invalid"])


class TestPositionalValidationBasic:
    """Tests for positional argument validation."""

    def test_multiple_positional_lists_error(self):
        """Test that multiple positional lists raise error."""
        with pytest.raises(ConfigBuilderError, match="Only one positional list"):

            @dataclass
            class Invalid:
                inputs: List[str] = cli_positional(nargs="+")
                outputs: List[str] = cli_positional(nargs="+")

            build_config(Invalid, args=[])

    def test_positional_list_not_last_error(self):
        """Test that positional list not last raises error."""
        with pytest.raises(ConfigBuilderError, match="must be last"):

            @dataclass
            class Invalid:
                files: List[str] = cli_positional(nargs="+")
                output: str = cli_positional()

            build_config(Invalid, args=[])

    def test_positional_list_with_star_not_last_error(self):
        """Test that positional list with nargs='*' not last raises error."""
        with pytest.raises(ConfigBuilderError, match="must be last"):

            @dataclass
            class Invalid:
                files: List[str] = cli_positional(nargs="*")
                output: str = cli_positional()

            build_config(Invalid, args=[])

    def test_exact_count_not_greedy(self):
        """Test that exact count (nargs=2) is not treated as greedy list."""

        @dataclass
        class Valid:
            coords: List[float] = cli_positional(nargs=2, metavar="X Y")
            label: str = cli_positional()

        # This should work - exact count is not greedy
        config = build_config(Valid, args=["1.5", "2.5", "PointA"])
        assert config.coords == [1.5, 2.5]
        assert config.label == "PointA"


class TestCombineAnnotations:
    """Tests for combining positional with other annotations."""

    def test_positional_with_help(self):
        """Test combining positional with help text."""

        @dataclass
        class Config:
            source: str = combine_annotations(
                cli_positional(), cli_help("Source file path")
            )

        config = build_config(Config, args=["test.txt"])
        assert config.source == "test.txt"

    def test_positional_with_choices_and_help(self):
        """Test combining positional with choices and help."""

        @dataclass
        class Config:
            env: str = combine_annotations(
                cli_positional(),
                cli_choices(["dev", "staging", "prod"]),
                cli_help("Environment to deploy to"),
            )

        config = build_config(Config, args=["prod"])
        assert config.env == "prod"


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_git_style_cli(self):
        """Test Git-style CLI (command + files)."""

        @dataclass
        class GitCommit:
            command: str = cli_positional(help="Git command")
            files: List[str] = cli_positional(nargs="+", help="Files to commit")
            message: str = cli_short("m", default="")
            verbose: bool = cli_short("v", default=False)

        config = build_config(
            GitCommit,
            args=["commit", "file1.py", "file2.py", "-m", "Add feature", "-v"],
        )
        assert config.command == "commit"
        assert config.files == ["file1.py", "file2.py"]
        assert config.message == "Add feature"
        assert config.verbose is True

    def test_copy_style_cli(self):
        """Test copy-style CLI (source + dest + options)."""

        @dataclass
        class Copy:
            source: str = cli_positional(help="Source file")
            dest: str = cli_positional(help="Destination file")
            recursive: bool = cli_short("r", default=False)
            exclude: List[str] = cli_short("e", default_factory=list)

        config = build_config(
            Copy, args=["source.txt", "dest.txt", "-r", "--exclude", "*.tmp", "*.log"]
        )
        assert config.source == "source.txt"
        assert config.dest == "dest.txt"
        assert config.recursive is True
        assert config.exclude == ["*.tmp", "*.log"]

    def test_converter_style_cli(self):
        """Test converter-style CLI (input + optional output)."""

        @dataclass
        class Convert:
            input: str = cli_positional(help="Input file")
            output: str = cli_positional(nargs="?", default="stdout", help="Output")
            format: str = cli_short("f", default="json")

        # With output
        config1 = build_config(Convert, args=["in.txt", "out.txt", "-f", "yaml"])
        assert config1.input == "in.txt"
        assert config1.output == "out.txt"
        assert config1.format == "yaml"

        # Without output (uses default)
        config2 = build_config(Convert, args=["in.txt", "-f", "xml"])
        assert config2.input == "in.txt"
        assert config2.output == "stdout"
        assert config2.format == "xml"

    def test_plot_point_style_cli(self):
        """Test CLI with exact count positional."""

        @dataclass
        class PlotPoint:
            coordinates: List[float] = cli_positional(nargs=2, metavar="X Y")
            label: str = cli_positional(nargs="?", default="", help="Point label")
            show_grid: bool = cli_short("g", default=False)

        # With label
        config1 = build_config(PlotPoint, args=["1.5", "2.5", "PointA", "-g"])
        assert config1.coordinates == [1.5, 2.5]
        assert config1.label == "PointA"
        assert config1.show_grid is True

        # Without label
        config2 = build_config(PlotPoint, args=["3.0", "4.0"])
        assert config2.coordinates == [3.0, 4.0]
        assert config2.label == ""
        assert config2.show_grid is False


class TestPositionalValidation:
    """Tests for positional argument validation."""

    def test_multiple_positional_lists_rejected(self):
        """Test that multiple positional lists are rejected."""
        with pytest.raises(ConfigBuilderError) as exc_info:

            @dataclass
            class Invalid:
                inputs: List[str] = cli_positional(nargs="+")
                outputs: List[str] = cli_positional(nargs="+")

            build_config(Invalid, args=[])

        assert "Only one positional list" in str(exc_info.value)
        assert "'inputs'" in str(exc_info.value)
        assert "'outputs'" in str(exc_info.value)

    def test_positional_list_not_last_rejected(self):
        """Test that positional list not last is rejected."""
        with pytest.raises(ConfigBuilderError) as exc_info:

            @dataclass
            class Invalid:
                files: List[str] = cli_positional(nargs="+")
                output: str = cli_positional()

            build_config(Invalid, args=[])

        assert "must be last" in str(exc_info.value)
        assert "'files'" in str(exc_info.value)

    def test_positional_star_list_not_last_rejected(self):
        """Test that positional list with nargs='*' not last is rejected."""
        with pytest.raises(ConfigBuilderError) as exc_info:

            @dataclass
            class Invalid:
                files: List[str] = cli_positional(nargs="*")
                output: str = cli_positional()

            build_config(Invalid, args=[])

        assert "must be last" in str(exc_info.value)

    def test_exact_count_positional_not_greedy(self):
        """Test that exact count positional is not treated as greedy."""

        # This should NOT raise an error
        @dataclass
        class Valid:
            coords: List[float] = cli_positional(nargs=2)
            label: str = cli_positional()

        config = build_config(Valid, args=["1.0", "2.0", "MyLabel"])
        assert config.coords == [1.0, 2.0]
        assert config.label == "MyLabel"


class TestPositionalEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_missing_required_positional(self):
        """Test error when required positional is missing."""

        @dataclass
        class Config:
            source: str = cli_positional()

        with pytest.raises(SystemExit):  # argparse exits on missing required
            build_config(Config, args=[])

    def test_too_many_positionals(self):
        """Test error when too many positionals provided."""

        @dataclass
        class Config:
            source: str = cli_positional()

        with pytest.raises(SystemExit):  # argparse exits on extra args
            build_config(Config, args=["file1.txt", "file2.txt"])

    def test_positional_only_cli(self):
        """Test CLI with only positional arguments (no optionals)."""

        @dataclass
        class Config:
            source: str = cli_positional()
            dest: str = cli_positional()

        config = build_config(Config, args=["in.txt", "out.txt"])
        assert config.source == "in.txt"
        assert config.dest == "out.txt"

    def test_optional_only_cli(self):
        """Test that existing optional-only CLIs still work."""

        @dataclass
        class Config:
            name: str = cli_short("n", default="app")
            count: int = 10

        config = build_config(Config, args=["-n", "test"])
        assert config.name == "test"
        assert config.count == 10


class TestHelpDisplay:
    """Tests for help text display with positionals."""

    def test_positional_help_displayed(self):
        """Test that positional help text is displayed correctly."""

        @dataclass
        class Config:
            source: str = cli_positional(help="Source file")
            dest: str = cli_positional(help="Destination file")

        # This should display help without error
        # We can't easily test the output, but we can verify it doesn't crash
        try:
            build_config(Config, args=["--help"])
        except SystemExit:
            pass  # --help causes sys.exit(0), which is expected


class TestBackwardCompatibility:
    """Tests to ensure positionals don't break existing functionality."""

    def test_existing_tests_still_pass(self):
        """Test that non-positional configs still work."""

        @dataclass
        class Config:
            name: str = cli_short("n")
            env: str = cli_choices(["dev", "prod"], default="dev")
            debug: bool = False

        config = build_config(Config, args=["-n", "myapp", "--env", "prod", "--debug"])
        assert config.name == "myapp"
        assert config.env == "prod"
        assert config.debug is True

    def test_optional_list_still_works(self):
        """Test that optional List[T] fields still work."""

        @dataclass
        class Config:
            items: List[str] = cli_short("i", default_factory=list)

        config = build_config(Config, args=["--items", "a", "b", "c"])
        assert config.items == ["a", "b", "c"]
