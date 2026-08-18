#!/usr/bin/env python3
"""
Programmatic Configuration Example - No CLI Required

Demonstrates build_config_from_dict() for non-CLI contexts:
- Lambda handlers
- Programmatic SDKs
- Test harnesses
- Any context where config comes from a dict (API payload, DynamoDB, etc.)

This example shows that you can use dataclass-args without any CLI involvement.
Features that work: nested dataclasses, resolvers, defaults, type handling.

Note: @file loading (cli_file_loadable) does NOT resolve via build_config_from_dict
because file loading happens in the argparse layer. If you need file loading in
programmatic contexts, load the file yourself before passing the value.
"""

from dataclasses import dataclass
from typing import Optional

from dataclass_args import build_config_from_dict, cli_help, cli_nested, cli_resolve


def create_backend_instance(config) -> str:
    """Resolver function to create backend instances from config dicts."""
    if isinstance(config, dict):
        backend_type = config.get("type", "default")
        print(f"  ✨ Resolver fired: creating {backend_type} backend from dict")
        return f"BackendInstance(type={backend_type})"
    return str(config)


@dataclass
class DatabaseConfig:
    """Nested database configuration."""

    host: str = "localhost"
    port: int = 5432
    name: str = "app_db"


@dataclass
class AppConfig:
    """Application configuration demonstrating programmatic usage."""

    # Basic field types
    app_name: str = cli_help("Application name", default="my-app")
    port: int = cli_help("Server port", default=8000)
    debug: bool = cli_help("Enable debug mode", default=False)
    workers: int = cli_help("Number of workers", default=4)

    # Optional field
    api_key: Optional[str] = cli_help("API key", default=None)

    # Nested dataclass
    database: DatabaseConfig = cli_nested(prefix="db", default_factory=DatabaseConfig)

    # Resolver field - dict gets transformed into a typed object
    backend: str = cli_resolve(resolver=create_backend_instance, default="default")


def example_lambda_handler():
    """Simulate a Lambda handler that builds config from event/environment."""
    print("=" * 60)
    print("EXAMPLE 1: Lambda Handler Pattern")
    print("=" * 60)

    # Simulated config from Lambda event + environment merge
    merged_config = {
        "app_name": "production-api",
        "port": 8080,
        "debug": False,
        "workers": 16,
        "api_key": "sk-prod-xxxxx",
        "database": {
            "host": "rds-prod.amazonaws.com",
            "port": 5432,
            "name": "prod_db",
        },
        "backend": {"type": "uvicorn", "workers": 4},
    }

    print("\n📦 Config dict (from Lambda event/env):")
    for key, value in merged_config.items():
        print(f"    {key}: {value}")

    print("\n🔧 Building config...")
    config = build_config_from_dict(AppConfig, merged_config)

    print(f"\n✅ Result:")
    print(f"    app_name: {config.app_name}")
    print(f"    port: {config.port}")
    print(f"    debug: {config.debug}")
    print(f"    workers: {config.workers}")
    print(f"    api_key: {config.api_key}")
    print(f"    backend: {config.backend}")
    print(f"    database.host: {config.database.host}")
    print(f"    database.port: {config.database.port}")
    print(f"    database.name: {config.database.name}")
    return config


def example_defaults_only():
    """Demonstrate using empty/partial dicts with defaults."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Partial Config (defaults fill the gaps)")
    print("=" * 60)

    # Only override what you need — defaults handle the rest
    minimal_config = {
        "app_name": "dev-server",
        "debug": True,
    }

    print(f"\n📦 Minimal config: {minimal_config}")
    print("\n🔧 Building config...")
    config = build_config_from_dict(AppConfig, minimal_config)

    print(f"\n✅ Result (note defaults applied):")
    print(f"    app_name: {config.app_name}")
    print(f"    port: {config.port} (default)")
    print(f"    debug: {config.debug}")
    print(f"    workers: {config.workers} (default)")
    print(f"    api_key: {config.api_key} (default: None)")
    print(f"    database.host: {config.database.host} (default)")
    return config


def example_test_harness():
    """Demonstrate using build_config_from_dict in tests."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Test Harness Pattern")
    print("=" * 60)

    # In tests, you build config directly from fixtures
    test_config = {
        "app_name": "test-app",
        "port": 9999,
        "debug": True,
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "test_db",
        },
    }

    print(f"\n📦 Test fixture config")
    print("\n🔧 Building config...")
    config = build_config_from_dict(AppConfig, test_config)

    # Simulate test assertions
    assert config.app_name == "test-app"
    assert config.port == 9999
    assert config.debug is True
    assert config.database.host == "localhost"
    assert config.database.name == "test_db"

    print("\n✅ All assertions passed!")
    print("    (This is how you'd use it in pytest fixtures)")
    return config


if __name__ == "__main__":
    print("🚀 Programmatic Configuration with build_config_from_dict()")
    print("   No CLI, no sys.argv, no argparse — just dicts in, dataclass out.\n")

    example_lambda_handler()
    example_defaults_only()
    example_test_harness()

    print("\n" + "=" * 60)
    print("🎯 Summary: build_config_from_dict() provides:")
    print("  ✓ Nested dataclass reconstruction from nested dicts")
    print("  ✓ cli_resolve() resolver execution")
    print("  ✓ Default value handling for omitted fields")
    print("  ✓ Clean one-liner: no argparse ceremony needed")
    print("  ✓ TypeError if you accidentally pass non-dict")
    print("=" * 60)
