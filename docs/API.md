# API Documentation

This document provides detailed API reference for dataclass-cli.

## Main Functions

### build_config(config_class, args=None)

Simplified convenience function to build any dataclass from CLI arguments.

Uses default settings suitable for most use cases.

**Parameters:**
- `config_class`: Dataclass type to build
- `args`: Command-line arguments (defaults to sys.argv[1:])

**Returns:** Instance of config_class built from CLI arguments

**Example:**
```python
from dataclasses import dataclass
from dataclass_cli import build_config

@dataclass
class Config:
    name: str
    count: int = 10

config = build_config(Config)  # Parses sys.argv automatically
```

### build_config_from_cli(config_class, args=None, **options)

Convenience function to build any dataclass from CLI arguments with full options.

**Parameters:**
- `config_class`: Dataclass type to build
- `args`: Command-line arguments (defaults to sys.argv[1:])
- `base_config_name`: Name for base config file argument
- `exclude_fields`: Set of field names to exclude from CLI
- `include_fields`: Set of field names to include in CLI
- `field_filter`: Custom function to determine field inclusion
- `use_annotations`: Whether to respect cli_exclude() annotations (default: True)

**Returns:** Instance of config_class built from CLI arguments

## Annotations

### cli_help(help_text, **kwargs)

Add custom help text for a CLI argument.

**Parameters:**
- `help_text`: Custom help text for the CLI argument
- `**kwargs`: Additional field parameters

**Returns:** Field object with help text metadata

### cli_exclude(**kwargs)

Mark a dataclass field to be excluded from CLI arguments.

**Parameters:**
- `**kwargs`: Additional field parameters (default, default_factory, etc.)

**Returns:** Field object with CLI exclusion metadata

### cli_file_loadable(**kwargs)

Mark a string field as file-loadable via '@' prefix.

When a CLI argument value starts with '@', the remaining part is treated as a file path.
The file is read as UTF-8 encoded text and used as the field value.

**Parameters:**
- `**kwargs`: Additional field parameters (default, default_factory, etc.)

**Returns:** Field object with file-loadable metadata

### cli_include(**kwargs)

Explicitly mark a dataclass field to be included in CLI arguments.

**Parameters:**
- `**kwargs`: Additional field parameters (default, default_factory, etc.)

**Returns:** Field object with CLI inclusion metadata

## Advanced Classes

### GenericConfigBuilder

Builds dataclass instances from CLI arguments and optional base config file.

Supports any dataclass type with:
- Optional base config file loading
- Type-aware CLI argument parsing
- List parameter handling with multiple values
- Object parameter file loading with property overrides
- File-loadable string parameters via '@' prefix
- Hierarchical merging of configuration sources
- Field filtering via annotations or custom filters

**Constructor Parameters:**
- `config_class`: Dataclass type to build configurations for
- `exclude_fields`: Set of field names to exclude from CLI
- `include_fields`: Set of field names to include in CLI (exclusive with exclude_fields)
- `field_filter`: Custom function to determine field inclusion
- `use_annotations`: Whether to respect cli_exclude() annotations (default: True)

**Methods:**

#### add_arguments(parser, base_config_name='config', base_config_help='...')

Add all dataclass arguments to parser.

#### build_config(args, base_config_name='config')

Build dataclass instance from parsed CLI arguments.

## Utilities

### exclude_internal_fields(field_name, field_info)

Filter function that excludes internal fields (starting with underscore).

### load_structured_file(file_path)

Load structured data from JSON, YAML, or TOML file.

Automatically detects file format based on extension and attempts to parse.

## File Loading

### load_file_content(file_path)

Load content from a file as UTF-8 encoded text.

### is_file_loadable_value(value)

Check if a value is a file-loadable string (starts with '@').

## Exceptions

### ConfigBuilderError

Base exception for configuration builder errors.

### ConfigurationError

Exception raised for configuration validation errors.

### FileLoadingError

Exception raised when file loading fails.
