#!/usr/bin/env python3
"""
Example demonstrating cli_short() for concise command-line options.

Run with:
    python cli_short_example.py -n MyApp -p 9000 -v true
    python cli_short_example.py --name MyApp --port 9000 --verbose true
    python cli_short_example.py -n MyApp --port 9000 -v true  # Mix and match
"""

import os
import sys
from dataclasses import dataclass

# Add parent directory to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclass_cli import build_config, cli_help, cli_short, combine_annotations


@dataclass
class ServerConfig:
    """Server configuration with short-form options."""

    # Short options only
    name: str = cli_short("n")
    port: int = cli_short("p", default=8080)

    # Short options with help text
    verbose: bool = combine_annotations(
        cli_short("v"), cli_help("Enable verbose output"), default=False
    )

    debug: bool = combine_annotations(
        cli_short("d"), cli_help("Enable debug mode"), default=False
    )

    # No short option (just long form)
    workers: int = cli_help("Number of worker processes", default=4)


def main():
    """Main application entry point."""
    print("CLI Short Options Example")
    print("=" * 40)

    # Build configuration from CLI arguments
    config = build_config(ServerConfig)

    print(f"\nServer Configuration:")
    print(f"  Name:    {config.name}")
    print(f"  Port:    {config.port}")
    print(f"  Workers: {config.workers}")
    print(f"  Verbose: {config.verbose}")
    print(f"  Debug:   {config.debug}")

    if config.verbose:
        print("\n[VERBOSE] Starting server with detailed logging...")

    if config.debug:
        print("[DEBUG] Debug mode is enabled!")
        print(f"[DEBUG] Full config: {config}")

    print(f"\n🚀 Starting {config.name} server on port {config.port}")
    print(f"   Running with {config.workers} workers")


if __name__ == "__main__":
    main()
