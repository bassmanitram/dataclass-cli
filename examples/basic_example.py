#!/usr/bin/env python3
"""
Basic example demonstrating dataclass-config usage.

Run with:
    python basic_example.py --name "MyApp" --count 5 --debug true
    python basic_example.py --help
"""

import os
import sys
from dataclasses import dataclass

# Add parent directory to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclass_config import build_config


@dataclass
class Config:
    """Basic configuration example."""

    name: str
    count: int = 10
    debug: bool = False


def main() -> None:
    """Main application entry point."""
    print("Basic Dataclass CLI Example")
    print("=" * 30)

    # Build configuration from CLI arguments
    config = build_config(Config)

    print(f"Configuration:")
    print(f"  Name: {config.name}")
    print(f"  Count: {config.count}")
    print(f"  Debug: {config.debug}")

    # Use configuration
    if config.debug:
        print("\n[DEBUG] Debug mode is enabled!")

    print(f"\nRunning {config.name} with count={config.count}")

    for i in range(config.count):
        print(f"  Processing item {i + 1}")
        if config.debug:
            print(f"    [DEBUG] Item {i + 1} details...")


if __name__ == "__main__":
    main()
