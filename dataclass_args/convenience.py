"""
Public entry points for building dataclass configurations.

This module provides the user-facing API functions that hide the internal
machinery (GenericConfigBuilder, FieldAnalyzer, ArgumentRegistry, ConfigResolver).

Functions:
    build_config(cls)              → Parse sys.argv, return dataclass instance
    build_config_from_cli(cls, …) → Parse args list with options, return instance
    build_config_from_dict(cls, d) → Build from dict (no CLI, for programmatic use)

All functions return an instance of the provided dataclass type.
"""

import argparse
import sys
from typing import Any, Dict, List, Optional, Type, Union

from .builder import GenericConfigBuilder
from .formatter import RangeAppendHelpFormatter

# Type alias for base_configs parameter
BaseConfigInput = Union[str, Dict[str, Any], List[Union[str, Dict[str, Any]]]]


def build_config_from_cli(
    config_class: Type,
    args: Optional[List[str]] = None,
    base_config_name: str = "config",
    base_configs: Optional[BaseConfigInput] = None,
    description: Optional[str] = None,
) -> Any:
    """
    Build dataclass instance from CLI arguments with optional base configs.

    Configuration sources are merged in the following order (later sources override earlier):
    1. base_configs (if provided) - files loaded and applied in order
    2. Config file from --config argument (if provided)
    3. CLI argument overrides

    Args:
        config_class: Dataclass type to build
        args: Command-line arguments (defaults to sys.argv[1:])
        base_config_name: Name for base config file argument (default: "config")
        base_configs: Optional base configuration(s). Can be:
                     - str: Path to a single config file
                     - dict: A single configuration dictionary
                     - List[Union[str, dict]]: Multiple configs applied in order
        description: Optional description for ArgumentParser help text.
                    If not provided, uses "Build {ClassName} from CLI"

    Returns:
        Instance of config_class built from merged configurations

    Example:
        # Single file
        config = build_config_from_cli(MyConfig, base_configs='defaults.yaml')

        # Single dict
        config = build_config_from_cli(MyConfig, base_configs={'debug': True})

        # With custom description
        config = build_config_from_cli(
            MyConfig,
            description="Configure the application server"
        )

        # Mixed list
        config = build_config_from_cli(
            MyConfig,
            args=['--config', 'prod.yaml', '--name', 'override'],
            base_configs=[
                'company-defaults.yaml',
                {'team': 'platform'},
                'env-staging.json',
            ]
        )
    """
    if args is None:
        args = sys.argv[1:]

    builder = GenericConfigBuilder(config_class, description=description)

    desc = (
        builder.description
        if builder.description is not None
        else f"Build {config_class.__name__} from CLI"
    )
    parser = argparse.ArgumentParser(
        description=desc, formatter_class=RangeAppendHelpFormatter
    )
    builder.add_arguments(parser, base_config_name)

    parsed_args = parser.parse_args(args)
    return builder.build_config(parsed_args, base_config_name, base_configs)


def build_config(
    config_class: Type,
    args: Optional[List[str]] = None,
    base_configs: Optional[BaseConfigInput] = None,
    description: Optional[str] = None,
) -> Any:
    """
    Simplified convenience function to build dataclass from CLI arguments.

    Configuration sources are merged in the following order (later sources override earlier):
    1. base_configs (if provided) - files loaded and applied in order
    2. Config file from --config argument (if provided)
    3. CLI argument overrides

    Args:
        config_class: Dataclass type to build
        args: Command-line arguments (defaults to sys.argv[1:])
        base_configs: Optional base configuration(s). Can be:
                     - str: Path to a single config file
                     - dict: A single configuration dictionary
                     - List[Union[str, dict]]: Multiple configs applied in order
        description: Optional description for ArgumentParser help text.
                    If not provided, uses "Build {ClassName} from CLI"

    Returns:
        Instance of config_class built from merged configurations

    Example:
        # Simple usage
        config = build_config(Config)

        # With base config file
        config = build_config(Config, base_configs='defaults.yaml')

        # With custom description
        config = build_config(
            Config,
            description="My application configuration tool"
        )

        # With mixed sources
        config = build_config(
            Config,
            args=['--count', '100'],
            base_configs=[
                'base.yaml',
                {'environment': 'prod'},
            ]
        )
    """
    return build_config_from_cli(
        config_class, args, base_configs=base_configs, description=description
    )


def build_config_from_dict(
    config_class: type,
    config: dict,
):
    """
    Build a dataclass instance from a dictionary, processing values as CLI values.

    Dict values are processed exactly as if they came from the CLI:
    - @file reference loading (for cli_file_loadable fields)
    - Dict field structured file loading
    - cli_resolve() post-load resolution
    - Nested dataclass reconstruction

    This is the recommended entry point for non-CLI contexts such as
    Lambda handlers, programmatic SDKs, and test harnesses.

    Args:
        config_class: Dataclass type to instantiate
        config: Dictionary of field values (processed as if from CLI)

    Returns:
        Instance of config_class with all values resolved

    Raises:
        ConfigurationError: If resolution fails
        TypeError: If config is not a dict

    Example:
        config = build_config_from_dict(AppConfig, {
            "model": "bedrock:claude-3",
            "system_prompt": "@/path/to/prompt.txt",
            "temperature": 0.7,
        })
    """
    if not isinstance(config, dict):
        raise TypeError(
            f"build_config_from_dict requires a dict, got {type(config).__name__}. "
            f"Use build_config_from_cli() with base_configs for file paths or lists."
        )

    # Build CLI infrastructure (parser, field analysis) without parsing real args
    builder = GenericConfigBuilder(config_class)
    parser = argparse.ArgumentParser()
    builder.add_arguments(parser)

    # Parse empty args to get a Namespace with argparse defaults/SUPPRESS
    args = parser.parse_args([])

    # Separate nested dict fields and excluded fields from CLI-processable fields
    base_config_values = {}
    cli_values = {}
    for key, value in config.items():
        arg_key = key.replace("-", "_")
        field_info = builder._config_fields.get(key) or builder._config_fields.get(
            arg_key
        )

        if field_info is None:
            # Field not in config_fields (e.g., cli_exclude) - route through base_configs
            base_config_values[key] = value
        elif field_info.get("is_nested_dataclass") and isinstance(value, dict):
            # Nested dict - route through base_configs for reconstruction
            base_config_values[key] = value
        else:
            # Regular field - process through CLI pipeline
            cli_values[arg_key] = value

    # Inject CLI-processable values into Namespace
    for key, value in cli_values.items():
        setattr(args, key, value)

    # Run build pipeline with base_config_values for excluded/nested fields
    return builder.build_config(
        args, base_configs=base_config_values if base_config_values else None
    )
