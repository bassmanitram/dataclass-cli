#!/usr/bin/env python3
"""
Example demonstrating cli_choices() for validated restricted values.

Run with:
    python cli_choices_example.py -n myapp -e prod -r us-west-2 -s large
    python cli_choices_example.py --name myapp --environment staging --region eu-west-1
    python cli_choices_example.py -n test -e invalid  # Shows error with valid choices
"""

import os
import sys
from dataclasses import dataclass

# Add parent directory to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclass_args import (
    build_config,
    cli_choices,
    cli_help,
    cli_short,
    combine_annotations,
)


@dataclass
class DeploymentConfig:
    """Deployment configuration with validated choices."""

    # Required field with short option
    name: str = combine_annotations(cli_short("n"), cli_help("Application name"))

    # Simple choices with default
    environment: str = combine_annotations(
        cli_short("e"),
        cli_choices(["dev", "staging", "prod"]),
        cli_help("Deployment environment"),
        default="dev",
    )

    # AWS region choices
    region: str = combine_annotations(
        cli_short("r"),
        cli_choices(["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]),
        cli_help("AWS region"),
        default="us-east-1",
    )

    # Instance size choices
    size: str = combine_annotations(
        cli_short("s"),
        cli_choices(["small", "medium", "large", "xlarge"]),
        cli_help("Instance size"),
        default="medium",
    )

    # Database engine choices
    database: str = combine_annotations(
        cli_choices(["postgres", "mysql", "mongodb"]),
        cli_help("Database engine"),
        default="postgres",
    )


def main() -> None:
    """Main application entry point."""
    print("CLI Choices Example - Validated Deployment")
    print("=" * 50)

    try:
        # Build configuration from CLI arguments
        config = build_config(DeploymentConfig)

        print(f"\n✓ Configuration Validated Successfully!")
        print(f"\nDeployment Details:")
        print(f"  Application:  {config.name}")
        print(f"  Environment:  {config.environment}")
        print(f"  Region:       {config.region}")
        print(f"  Instance Size: {config.size}")
        print(f"  Database:     {config.database}")

        # Deployment simulation
        print(f"\n🚀 Deploying {config.name} to {config.environment}...")
        print(f"   Region: {config.region}")
        print(f"   Size: {config.size}")
        print(f"   DB: {config.database}")

        if config.environment == "prod":
            print("\n⚠️  PRODUCTION DEPLOYMENT - Extra validation enabled")

    except SystemExit as e:
        if e.code != 0:
            print("\n❌ Configuration validation failed!")
            print("   Use --help to see valid choices for each option")
        raise


if __name__ == "__main__":
    main()
