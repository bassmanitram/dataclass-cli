#!/usr/bin/env python3
"""
Example demonstrating boolean flag functionality with --flag and --no-flag.

Boolean fields automatically get both positive (--flag, -f) and negative (--no-flag)
forms, allowing explicit control over boolean settings.
"""

from dataclasses import dataclass

from dataclass_config import build_config, cli_help, cli_short, combine_annotations


@dataclass
class BuildConfig:
    """Configuration for build pipeline."""

    # Project settings
    project: str = combine_annotations(cli_short("p"), cli_help("Project name"))

    # Build steps (default: enabled)
    build: bool = combine_annotations(
        cli_short("b"), cli_help("Run build step"), default=True
    )

    test: bool = combine_annotations(
        cli_short("t"), cli_help("Run tests"), default=True
    )

    lint: bool = combine_annotations(
        cli_short("l"), cli_help("Run linter"), default=True
    )

    # Optional steps (default: disabled)
    deploy: bool = combine_annotations(
        cli_short("d"), cli_help("Deploy after build"), default=False
    )

    notify: bool = combine_annotations(
        cli_short("n"), cli_help("Send notifications"), default=False
    )

    # Debug options (default: disabled)
    debug: bool = combine_annotations(
        cli_short("D"), cli_help("Enable debug mode"), default=False
    )

    verbose: bool = combine_annotations(
        cli_short("v"), cli_help("Verbose output"), default=False
    )


def main() -> None:
    """Run example build pipeline."""
    config = build_config(BuildConfig)

    print("Build Configuration:")
    print(f"  Project: {config.project}")
    print(f"\nBuild Steps:")
    print(f"  Build:  {'✓' if config.build else '✗'}")
    print(f"  Test:   {'✓' if config.test else '✗'}")
    print(f"  Lint:   {'✓' if config.lint else '✗'}")
    print(f"\nDeployment:")
    print(f"  Deploy: {'✓' if config.deploy else '✗'}")
    print(f"  Notify: {'✓' if config.notify else '✗'}")
    print(f"\nDebug:")
    print(f"  Debug:   {'✓' if config.debug else '✗'}")
    print(f"  Verbose: {'✓' if config.verbose else '✗'}")


if __name__ == "__main__":
    """
    Examples:

    # Full pipeline (all defaults)
    ./boolean_flags_example.py -p myapp

    # Quick build (skip slow steps)
    ./boolean_flags_example.py -p myapp --no-test --no-lint

    # Production deploy
    ./boolean_flags_example.py -p myapp -d -n

    # Debug build
    ./boolean_flags_example.py -p myapp -D -v

    # Minimal build (only compilation)
    ./boolean_flags_example.py -p myapp --no-test --no-lint

    # Full pipeline with debug
    ./boolean_flags_example.py -p myapp -d -n -D -v

    # See all options
    ./boolean_flags_example.py --help
    """
    main()
