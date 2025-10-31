"""
Dataclass CLI - Zero-boilerplate CLI generation for Python dataclasses.

This package provides automatic CLI interface generation from Python dataclasses
with advanced features including:

- Type-safe argument parsing for all standard Python types
- File-loadable string parameters using @filename syntax
- Configuration file merging with CLI overrides
- Hierarchical property overrides for dictionary fields
- Comprehensive validation and error handling
- Automatic help text generation

Basic Usage:
    from dataclasses import dataclass
    from dataclass_cli import build_config

    @dataclass
    class Config:
        name: str
        count: int = 10

    config = build_config(Config)  # Automatically parses sys.argv

Advanced Usage:
    from dataclass_cli import cli_help, cli_file_loadable, GenericConfigBuilder

    @dataclass
    class Config:
        host: str = cli_help("Server hostname")
        message: str = cli_file_loadable()  # Supports @filename loading

    builder = GenericConfigBuilder(Config)
    # Full control over argument parsing
"""

from .annotations import (
    cli_exclude,
    cli_file_loadable,
    cli_help,
    cli_include,
    combine_annotations,
    is_cli_excluded,
    is_cli_file_loadable,
    is_cli_included,
)
from .builder import GenericConfigBuilder, build_config, build_config_from_cli
from .exceptions import ConfigBuilderError, ConfigurationError, FileLoadingError
from .file_loading import is_file_loadable_value, load_file_content
from .utils import exclude_internal_fields, load_structured_file

__version__ = "0.1.0"

__all__ = [
    # Main API
    "build_config",
    "build_config_from_cli",
    "GenericConfigBuilder",
    # Annotations
    "cli_help",
    "cli_exclude",
    "cli_include",
    "cli_file_loadable",
    "combine_annotations",
    "is_cli_file_loadable",
    "is_cli_excluded",
    "is_cli_included",
    # File loading
    "load_file_content",
    "is_file_loadable_value",
    # Utilities
    "exclude_internal_fields",
    "load_structured_file",
    # Exceptions
    "ConfigBuilderError",
    "ConfigurationError",
    "FileLoadingError",
]
