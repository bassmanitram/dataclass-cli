#!/usr/bin/env python3
"""
Advanced example demonstrating file loading and complex types.

Run with:
    python advanced_example.py --name "WebServer" --system-prompt "@prompts/server_prompt.txt"
    python advanced_example.py --config server_config.yaml --port 8080
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Add parent directory to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclass_args import build_config, cli_exclude, cli_file_loadable, cli_help


@dataclass
class ServerConfig:
    """Advanced server configuration with file loading and complex types."""

    # Required fields first
    name: str = cli_help("Server application name")

    # Optional fields with defaults
    host: str = cli_help("Server bind address", default="127.0.0.1")
    port: int = cli_help("Server port number", default=8000)
    workers: int = cli_help("Number of worker processes", default=1)

    # File-loadable strings with help text
    system_prompt: str = field(
        default="You are a helpful web server assistant.",
        metadata={
            "cli_help": "System prompt for the server (supports @file.txt to load from file)",
            "cli_file_loadable": True,
        },
    )
    welcome_message: str = field(
        default="",
        metadata={
            "cli_help": "Welcome message content (supports @file.txt to load from file)",
            "cli_file_loadable": True,
        },
    )

    # Complex types with defaults
    allowed_hosts: List[str] = cli_help("Allowed host headers", default_factory=list)
    middleware_config: Dict[str, Any] = cli_help(
        "Middleware configuration", default_factory=dict
    )

    # Optional settings
    ssl_cert_path: Optional[str] = cli_help("Path to SSL certificate", default=None)
    log_level: str = cli_help("Logging level", default="INFO")

    # Debug settings
    debug: bool = cli_help("Enable debug mode", default=False)

    # Hidden from CLI
    _server_id: str = cli_exclude(default="server-001")
    _startup_time: str = cli_exclude(default_factory=lambda: "auto-generated")


def main() -> None:
    """Main application entry point."""
    print("Advanced Dataclass CLI Example")
    print("=" * 35)

    # Build configuration from CLI arguments
    config = build_config(ServerConfig)

    print(f"Server Configuration:")
    print(f"  Name: {config.name}")
    print(f"  Address: {config.host}:{config.port}")
    print(f"  Workers: {config.workers}")
    print(f"  Debug: {config.debug}")
    print(f"  Log Level: {config.log_level}")

    if config.allowed_hosts:
        print(f"  Allowed Hosts: {', '.join(config.allowed_hosts)}")

    if config.ssl_cert_path:
        print(f"  SSL Certificate: {config.ssl_cert_path}")

    print(f"\nSystem Prompt:")
    print(f"  {config.system_prompt}")

    if config.welcome_message:
        print(f"\nWelcome Message:")
        print(f"  {config.welcome_message}")

    if config.middleware_config:
        print(f"\nMiddleware Configuration:")
        for key, value in config.middleware_config.items():
            print(f"  {key}: {value}")

    print(f"\nInternal Server ID: {config._server_id}")

    if config.debug:
        print("\n[DEBUG] Debug mode is enabled!")
        print("[DEBUG] Server configuration loaded successfully")

    print(f"\n🚀 Starting {config.name} server on {config.host}:{config.port}")


if __name__ == "__main__":
    main()
