#!/usr/bin/env python3
"""
Complete example demonstrating all dataclass-args features together.

This example shows how to combine:
- Short options (-n, -e, -r)
- Boolean flags (--debug, --no-cache)
- Value validation (cli_choices)
- Help text (cli_help)
- Combined annotations

Run with --help to see the generated CLI interface.
"""

from dataclasses import dataclass
from typing import List, Optional

from dataclass_args import (
    build_config,
    cli_choices,
    cli_exclude,
    cli_help,
    cli_short,
    combine_annotations,
)


@dataclass
class DeploymentConfig:
    """
    Complete configuration for application deployment.

    Demonstrates all major dataclass-args features working together.
    """

    # ========================================
    # Basic Fields with Short Options
    # ========================================

    name: str = combine_annotations(
        cli_short("n"), cli_help("Application name to deploy")
    )

    version: str = combine_annotations(
        cli_short("v"), cli_help("Version/tag to deploy"), default="latest"
    )

    # ========================================
    # Validated Choices
    # ========================================

    environment: str = combine_annotations(
        cli_short("e"),
        cli_choices(["dev", "staging", "prod"]),
        cli_help("Target deployment environment"),
        default="dev",
    )

    region: str = combine_annotations(
        cli_short("r"),
        cli_choices(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-2"]),
        cli_help("AWS region for deployment"),
        default="us-east-1",
    )

    size: str = combine_annotations(
        cli_short("s"),
        cli_choices(["small", "medium", "large", "xlarge"]),
        cli_help("Instance size"),
        default="medium",
    )

    # ========================================
    # Boolean Flags (with defaults)
    # ========================================

    # Build steps (default: enabled)
    build: bool = combine_annotations(
        cli_short("b"), cli_help("Run build step"), default=True
    )

    test: bool = combine_annotations(
        cli_short("t"), cli_help("Run test suite"), default=True
    )

    # Deployment options (default: disabled)
    deploy: bool = combine_annotations(
        cli_short("d"), cli_help("Actually deploy (not dry-run)"), default=False
    )

    notify: bool = combine_annotations(
        cli_short("N"), cli_help("Send deployment notifications"), default=False
    )

    # Debug and logging (default: disabled)
    debug: bool = combine_annotations(
        cli_short("D"), cli_help("Enable debug logging"), default=False
    )

    verbose: bool = combine_annotations(
        cli_short("V"), cli_help("Verbose output"), default=False
    )

    # Cache control (default: enabled)
    cache: bool = combine_annotations(
        cli_short("c"), cli_help("Use build cache"), default=True
    )

    # ========================================
    # List Fields
    # ========================================

    tags: List[str] = combine_annotations(
        cli_short("T"),
        cli_help("Additional tags for the deployment"),
        default_factory=list,
    )

    # ========================================
    # Optional Fields
    # ========================================

    timeout: Optional[int] = combine_annotations(
        cli_help("Deployment timeout in seconds"), default=None
    )

    # ========================================
    # Hidden/Internal Fields
    # ========================================

    _deployment_id: str = cli_exclude(default="auto-generated")  # Won't appear in CLI


def format_config(config: DeploymentConfig) -> str:
    """Format configuration for display."""
    lines = [
        "=" * 60,
        "DEPLOYMENT CONFIGURATION",
        "=" * 60,
        "",
        "Application:",
        f"  Name:        {config.name}",
        f"  Version:     {config.version}",
        "",
        "Environment:",
        f"  Environment: {config.environment}",
        f"  Region:      {config.region}",
        f"  Size:        {config.size}",
        "",
        "Build Steps:",
        f"  Build:       {'✓' if config.build else '✗'}",
        f"  Test:        {'✓' if config.test else '✗'}",
        f"  Cache:       {'✓' if config.cache else '✗'}",
        "",
        "Deployment:",
        f"  Deploy:      {'✓' if config.deploy else '✗'} {'(DRY RUN)' if not config.deploy else '(LIVE)'}",
        f"  Notify:      {'✓' if config.notify else '✗'}",
        "",
        "Logging:",
        f"  Debug:       {'✓' if config.debug else '✗'}",
        f"  Verbose:     {'✓' if config.verbose else '✗'}",
    ]

    if config.tags:
        lines.extend(["", "Tags:", *[f"  - {tag}" for tag in config.tags]])

    if config.timeout:
        lines.extend(["", f"Timeout: {config.timeout}s"])

    lines.append("=" * 60)

    return "\n".join(lines)


def main() -> None:
    """Run deployment with configuration from CLI."""
    config = build_config(DeploymentConfig)

    print(format_config(config))

    if not config.deploy:
        print("\n⚠️  DRY RUN MODE - No actual deployment will occur")
        print("   Add -d or --deploy to perform actual deployment")
    else:
        print("\n✓ Configuration valid - ready to deploy")


if __name__ == "__main__":
    """
    Example Usage:

    # Basic deployment to dev (dry run)
    ./all_features_example.py -n myapp

    # Deploy specific version to staging
    ./all_features_example.py -n myapp -v 2.1.0 -e staging -d

    # Production deployment with all options
    ./all_features_example.py -n myapp -v 2.1.0 -e prod -r us-west-2 -s large -d -N

    # Quick build without tests
    ./all_features_example.py -n myapp --no-test -d

    # Debug build with verbose output
    ./all_features_example.py -n myapp -D -V

    # With tags and timeout
    ./all_features_example.py -n myapp -T release stable v2.1.0 --timeout 600

    # Disable cache
    ./all_features_example.py -n myapp --no-cache

    # See all options
    ./all_features_example.py --help

    Example Scenarios:

    1. Development Testing:
       ./all_features_example.py -n myapp -e dev -D -V

    2. Staging Deployment:
       ./all_features_example.py -n myapp -v 2.1.0 -e staging -d -N

    3. Production Release:
       ./all_features_example.py -n myapp -v 2.1.0 -e prod -r us-west-2 -s xlarge -d -N -T stable

    4. Quick Dry Run:
       ./all_features_example.py -n myapp

    5. Skip Tests and Deploy:
       ./all_features_example.py -n myapp --no-test -d
    """
    main()
