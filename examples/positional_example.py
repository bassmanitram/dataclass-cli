#!/usr/bin/env python3
"""
Example demonstrating positional arguments with dataclass-args.

This example shows various positional argument patterns including:
- Required positionals
- Optional positionals (nargs='?')
- Variable positionals (nargs='+')
- Mixing positionals with optional arguments
"""

from dataclasses import dataclass
from typing import List

from dataclass_args import (
    build_config,
    cli_choices,
    cli_help,
    cli_positional,
    cli_short,
    combine_annotations,
)


@dataclass
class CopyCommand:
    """Simple copy command with source and destination."""

    source: str = cli_positional(help="Source file")
    dest: str = cli_positional(help="Destination file")
    recursive: bool = cli_short("r", default=False)
    verbose: bool = cli_short("v", default=False)


@dataclass
class GitCommit:
    """Git-style command with multiple files."""

    command: str = combine_annotations(
        cli_positional(),
        cli_choices(["commit", "add", "rm"]),
        cli_help("Git command to execute"),
    )

    files: List[str] = combine_annotations(
        cli_positional(nargs="+"), cli_help("Files to process")
    )

    message: str = cli_short("m", default="")
    amend: bool = cli_short("a", default=False)


@dataclass
class Convert:
    """File converter with optional output."""

    input_file: str = combine_annotations(
        cli_positional(), cli_help("Input file to convert")
    )

    output_file: str = combine_annotations(
        cli_positional(nargs="?"),
        cli_help("Output file (default: stdout)"),
        default="stdout",
    )

    format: str = combine_annotations(
        cli_short("f"),
        cli_choices(["json", "yaml", "xml", "toml"]),
        cli_help("Output format"),
        default="json",
    )

    pretty: bool = cli_short("p", default=False)


@dataclass
class PlotPoint:
    """Plot a point with X,Y coordinates."""

    coordinates: List[float] = combine_annotations(
        cli_positional(nargs=2, metavar="X Y"), cli_help("X and Y coordinates")
    )

    label: str = combine_annotations(
        cli_positional(nargs="?"), cli_help("Optional point label"), default=""
    )

    color: str = combine_annotations(
        cli_short("c"), cli_choices(["red", "blue", "green", "black"]), default="black"
    )

    show_grid: bool = cli_short("g", default=False)


def demo_copy() -> None:
    """Demonstrate copy command."""
    print("\n" + "=" * 70)
    print("Example 1: Copy Command (cp-style)")
    print("=" * 70)

    config = build_config(
        CopyCommand, args=["source.txt", "destination.txt", "-r", "-v"]
    )

    print(f"Source: {config.source}")
    print(f"Destination: {config.dest}")
    print(f"Recursive: {config.recursive}")
    print(f"Verbose: {config.verbose}")

    print("\nCLI Usage:")
    print("  python positional_example.py source.txt destination.txt -r -v")


def demo_git() -> None:
    """Demonstrate git-style command."""
    print("\n" + "=" * 70)
    print("Example 2: Git-Style Command")
    print("=" * 70)

    config = build_config(
        GitCommit,
        args=[
            "commit",
            "file1.py",
            "file2.py",
            "file3.py",
            "-m",
            "Add new feature",
            "-a",
        ],
    )

    print(f"Command: {config.command}")
    print(f"Files: {config.files}")
    print(f"Message: {config.message}")
    print(f"Amend: {config.amend}")

    print("\nCLI Usage:")
    print("  python git.py commit file1.py file2.py file3.py -m 'Message' -a")


def demo_convert_with_output() -> None:
    """Demonstrate converter with output."""
    print("\n" + "=" * 70)
    print("Example 3a: Converter with Output File")
    print("=" * 70)

    config = build_config(
        Convert, args=["input.json", "output.yaml", "-f", "yaml", "-p"]
    )

    print(f"Input: {config.input_file}")
    print(f"Output: {config.output_file}")
    print(f"Format: {config.format}")
    print(f"Pretty: {config.pretty}")

    print("\nCLI Usage:")
    print("  python convert.py input.json output.yaml -f yaml -p")


def demo_convert_no_output() -> None:
    """Demonstrate converter without output (uses default)."""
    print("\n" + "=" * 70)
    print("Example 3b: Converter to stdout (no output file)")
    print("=" * 70)

    config = build_config(Convert, args=["input.json", "-f", "xml"])

    print(f"Input: {config.input_file}")
    print(f"Output: {config.output_file}")
    print(f"Format: {config.format}")
    print(f"Pretty: {config.pretty}")

    print("\nCLI Usage:")
    print("  python convert.py input.json -f xml")
    print("  (Output file defaults to 'stdout')")


def demo_plot_with_label() -> None:
    """Demonstrate plot with label."""
    print("\n" + "=" * 70)
    print("Example 4a: Plot Point with Label")
    print("=" * 70)

    config = build_config(PlotPoint, args=["1.5", "2.5", "Point A", "-c", "red", "-g"])

    print(f"Coordinates: {config.coordinates}")
    print(f"Label: {config.label}")
    print(f"Color: {config.color}")
    print(f"Show Grid: {config.show_grid}")

    print("\nCLI Usage:")
    print("  python plot.py 1.5 2.5 'Point A' -c red -g")


def demo_plot_no_label() -> None:
    """Demonstrate plot without label."""
    print("\n" + "=" * 70)
    print("Example 4b: Plot Point without Label")
    print("=" * 70)

    config = build_config(PlotPoint, args=["3.0", "4.0", "-c", "blue"])

    print(f"Coordinates: {config.coordinates}")
    print(f"Label: {config.label!r}")
    print(f"Color: {config.color}")
    print(f"Show Grid: {config.show_grid}")

    print("\nCLI Usage:")
    print("  python plot.py 3.0 4.0 -c blue")
    print("  (Label defaults to empty string)")


def demo_flags_anywhere() -> None:
    """Demonstrate that flags can appear anywhere."""
    print("\n" + "=" * 70)
    print("Example 5: Flags Can Appear Anywhere")
    print("=" * 70)

    # Flags before positionals
    config1 = build_config(CopyCommand, args=["-r", "source.txt", "dest.txt"])
    print("Flags before positionals:")
    print(f"  CLI: -r source.txt dest.txt")
    print(
        f"  Result: source={config1.source}, dest={config1.dest}, recursive={config1.recursive}"
    )

    # Flags between positionals
    config2 = build_config(CopyCommand, args=["source.txt", "-r", "dest.txt"])
    print("\nFlags between positionals:")
    print(f"  CLI: source.txt -r dest.txt")
    print(
        f"  Result: source={config2.source}, dest={config2.dest}, recursive={config2.recursive}"
    )

    # Flags after positionals
    config3 = build_config(CopyCommand, args=["source.txt", "dest.txt", "-r"])
    print("\nFlags after positionals:")
    print(f"  CLI: source.txt dest.txt -r")
    print(
        f"  Result: source={config3.source}, dest={config3.dest}, recursive={config3.recursive}"
    )


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Positional Arguments Examples")
    print("=" * 70)
    print("\nDemonstrating various positional argument patterns.\n")

    try:
        demo_copy()
        demo_git()
        demo_convert_with_output()
        demo_convert_no_output()
        demo_plot_with_label()
        demo_plot_no_label()
        demo_flags_anywhere()

        print("\n" + "=" * 70)
        print("✅ All Examples Completed Successfully!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("  • Positional args don't need -- prefix")
        print("  • Order matters for positionals")
        print("  • Optional flags can appear anywhere in command")
        print("  • Positional lists (nargs='+') must be last")
        print("  • Combine with other annotations for full power")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
