"""
Generic configuration builder for dataclass types from CLI arguments.

Provides type-aware parsing of command-line arguments and merging
with optional base configuration files for any dataclass.
"""

import argparse
import json
import sys
from dataclasses import fields, is_dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

# Import typing utilities with Python 3.8+ compatibility
try:
    from typing import (  # type: ignore[attr-defined,no-redef]
        get_args,
        get_origin,
        get_type_hints,
    )
except ImportError:
    from typing_extensions import get_args, get_origin, get_type_hints  # type: ignore[assignment,no-redef]

from .annotations import get_cli_choices, get_cli_help, get_cli_short, is_cli_excluded
from .exceptions import ConfigBuilderError, ConfigurationError
from .file_loading import process_file_loadable_value
from .utils import load_structured_file


class GenericConfigBuilder:
    """
    Builds dataclass instances from CLI arguments and optional base config file.

    Supports any dataclass type with:
    - Optional base config file loading
    - Type-aware CLI argument parsing
    - List parameter accumulation
    - Object parameter file loading with property overrides
    - File-loadable string parameters via '@' prefix
    - Hierarchical merging of configuration sources
    - Field filtering via annotations or custom filters
    """

    def __init__(
        self,
        config_class: Type,
        exclude_fields: Optional[Set[str]] = None,
        include_fields: Optional[Set[str]] = None,
        field_filter: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
        use_annotations: bool = True,
    ):
        """
        Initialize builder for a specific dataclass type.

        Args:
            config_class: Dataclass type to build configurations for
            exclude_fields: Set of field names to exclude from CLI
            include_fields: Set of field names to include in CLI (exclusive with exclude_fields)
            field_filter: Custom function to determine field inclusion
            use_annotations: Whether to respect cli_exclude() annotations (default: True)

        Raises:
            ConfigBuilderError: If config_class is not a dataclass or conflicting filters provided
        """
        if not is_dataclass(config_class):
            raise ConfigBuilderError(
                f"config_class must be a dataclass, got {config_class}"
            )

        if exclude_fields and include_fields:
            raise ConfigBuilderError(
                "Cannot specify both exclude_fields and include_fields"
            )

        self.config_class = config_class
        self.exclude_fields = exclude_fields or set()
        self.include_fields = include_fields
        self.field_filter = field_filter
        self.use_annotations = use_annotations
        self._config_fields = self._analyze_config_fields()

    def _should_include_field(
        self, field_name: str, field_info: Dict[str, Any]
    ) -> bool:
        """Determine if a field should be included in CLI arguments."""

        # Apply annotation filter first if enabled
        if self.use_annotations and is_cli_excluded(field_info):
            return False

        # Apply custom filter if provided
        if self.field_filter:
            return self.field_filter(field_name, field_info)

        # Apply include_fields filter (exclusive)
        if self.include_fields is not None:
            return field_name in self.include_fields

        # Apply exclude_fields filter
        if field_name in self.exclude_fields:
            return False

        # Default: include all fields
        return True

    def _analyze_config_fields(self) -> Dict[str, Dict[str, Any]]:
        """Analyze dataclass fields for type information."""
        fields_info = {}
        type_hints = get_type_hints(self.config_class)

        for field_obj in fields(self.config_class):
            field_type = type_hints.get(field_obj.name, field_obj.type)
            origin = get_origin(field_type)
            args = get_args(field_type)

            # Determine field category
            is_optional = origin is Union and type(None) in args
            if is_optional:
                # Extract the non-None type from Optional[T]
                field_type = next(arg for arg in args if arg is not type(None))
                origin = get_origin(field_type)
                args = get_args(field_type)

            is_list = origin is list
            is_dict = origin is dict

            field_info = {
                "type": field_type,
                "origin": origin,
                "args": args,
                "is_optional": is_optional,
                "is_list": is_list,
                "is_dict": is_dict,
                "default": (
                    field_obj.default
                    if field_obj.default is not field_obj.default_factory
                    else None
                ),
                "cli_name": self._field_to_cli_name(field_obj.name),
                "override_name": self._field_to_override_name(field_obj.name),
                "field_obj": field_obj,  # Include field object for metadata access
            }

            # Only include field if it passes filtering
            if self._should_include_field(field_obj.name, field_info):
                fields_info[field_obj.name] = field_info

        return fields_info

    def _field_to_cli_name(self, field_name: str) -> str:
        """Convert field name to CLI argument name."""
        return "--" + field_name.replace("_", "-")

    def _field_to_override_name(self, field_name: str) -> str:
        """Convert field name to override argument name."""
        # Use abbreviation for override arguments
        words = field_name.split("_")
        if len(words) == 1:
            return "--" + field_name[0]
        else:
            return "--" + "".join(word[0] for word in words if word)

    def add_arguments(
        self,
        parser: argparse.ArgumentParser,
        base_config_name: str = "config",
        base_config_help: str = "Base configuration file (JSON, YAML, or TOML)",
    ) -> None:
        """
        Add all dataclass arguments to parser.

        Args:
            parser: ArgumentParser to add arguments to
            base_config_name: Name for base config file argument
            base_config_help: Help text for base config file argument
        """

        # Base config file argument
        parser.add_argument(f"--{base_config_name}", type=str, help=base_config_help)

        # Add arguments for each config field (filtered)
        for field_name, info in self._config_fields.items():
            self._add_field_argument(parser, field_name, info)

    def _add_field_argument(
        self, parser: argparse.ArgumentParser, field_name: str, info: Dict[str, Any]
    ) -> None:
        """Add CLI argument for a specific config field."""
        # Special handling for boolean fields
        if info["type"] == bool:
            self._add_boolean_argument(parser, field_name, info)
            return

        cli_name = info["cli_name"]

        # Get short option from metadata
        short_option = get_cli_short(info)

        # Build argument names list
        arg_names = []
        if short_option:
            arg_names.append(f"-{short_option}")  # Short comes first: -n
        arg_names.append(cli_name)  # Then long: --name

        # Get custom help text from annotations or use default
        custom_help = get_cli_help(info)
        help_text = custom_help if custom_help else f"{field_name}"

        # Get restricted choices if specified
        choices = get_cli_choices(info)
        if choices:
            # Add choices hint to help text
            choices_str = ", ".join(str(c) for c in choices)
            if help_text:
                help_text += f" (choices: {choices_str})"
            else:
                help_text = f"choices: {choices_str}"

        if info["is_list"]:
            # List parameters accept multiple values after a single flag
            # Use nargs='+' for required lists (one or more values)
            # Use nargs='*' for optional lists (zero or more values)
            if info["is_optional"]:
                nargs_val = "*"  # Zero or more values for Optional[List[T]]
                help_text += " (specify zero or more values)"
            else:
                nargs_val = "+"  # One or more values for List[T]
                help_text += " (specify one or more values)"

            parser.add_argument(
                *arg_names, nargs=nargs_val, choices=choices, help=help_text
            )
        elif info["is_dict"]:
            # Dict parameters are file paths
            dict_help = (
                f"{help_text} configuration file path"
                if help_text
                else "configuration file path"
            )
            parser.add_argument(*arg_names, type=str, help=dict_help)
            # Add override argument for dict fields (no short form for overrides)
            override_help = (
                f"{help_text} property override (format: key.path:value)"
                if help_text
                else "property override (format: key.path:value)"
            )
            parser.add_argument(
                info["override_name"],
                action="append",
                help=override_help,
            )
        else:
            # Simple scalar parameters
            arg_type = self._get_argument_type(info["type"])
            parser.add_argument(
                *arg_names, type=arg_type, choices=choices, help=help_text
            )

    def _add_boolean_argument(
        self, parser: argparse.ArgumentParser, field_name: str, info: Dict[str, Any]
    ) -> None:
        """Add boolean argument with positive and negative forms."""
        cli_name = info["cli_name"]
        dest_name = field_name.replace("-", "_")

        # Get short option from metadata
        short_option = get_cli_short(info)

        # Build argument names for positive form
        positive_args = []
        if short_option:
            positive_args.append(f"-{short_option}")
        positive_args.append(cli_name)

        # Get custom help text
        custom_help = get_cli_help(info)
        help_text = custom_help if custom_help else field_name

        # Get default value
        default_value = info.get("default", False)

        # Set parser default to the field's default value
        parser.set_defaults(**{dest_name: default_value})

        # Add positive form (--flag or -f)
        parser.add_argument(
            *positive_args,
            action="store_true",
            dest=dest_name,
            help=f"{help_text} (default: {default_value})",
        )

        # Add negative form (--no-flag)
        negative_name = f"--no-{field_name.replace('_', '-')}"
        parser.add_argument(
            negative_name,
            action="store_false",
            dest=dest_name,
            help=f"Disable {help_text}",
        )

    def _get_argument_type(self, field_type: Type) -> Callable[[str], Any]:
        """Get appropriate argparse type for field type."""
        # Note: bool is handled separately in _add_boolean_argument
        if field_type in (int, float, str):
            return field_type
        else:
            # For complex types, use string and let validation handle it
            return str

    def build_config(
        self, args: argparse.Namespace, base_config_name: str = "config"
    ) -> Any:
        """
        Build dataclass instance from parsed CLI arguments.

        Args:
            args: Parsed CLI arguments
            base_config_name: Name of base config argument

        Returns:
            Instance of the configured dataclass type

        Raises:
            ConfigurationError: If configuration is invalid
        """

        # Start with base config
        base_config = {}
        base_config_value = getattr(args, base_config_name.replace("-", "_"), None)
        if base_config_value:
            try:
                base_config = load_structured_file(base_config_value)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load base config from {base_config_value}: {e}"
                ) from e

        # Apply CLI argument overrides (only for included fields)
        config_dict = self._merge_cli_args(base_config, args)

        # Create and return config
        try:
            return self.config_class(**config_dict)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create {self.config_class.__name__}: {e}"
            ) from e

    def _merge_cli_args(
        self, base_config: Dict[str, Any], args: argparse.Namespace
    ) -> Dict[str, Any]:
        """Merge CLI arguments into base config."""
        config = base_config.copy()

        # Only process fields that were included in CLI
        for field_name, info in self._config_fields.items():
            # Convert CLI arg name back to field name
            arg_name = field_name.replace("-", "_")
            cli_value = getattr(args, arg_name, None)

            # Get override argument name
            override_arg_name = info["override_name"][2:].replace("-", "_")
            override_value = getattr(args, override_arg_name, None)

            if cli_value is not None:
                if info["is_list"]:
                    # CLI values replace base config values (standard argparse behavior)
                    # With nargs='+' or '*', cli_value is already a list
                    config[field_name] = cli_value
                elif info["is_dict"]:
                    # For dicts, load from file
                    try:
                        dict_config = load_structured_file(cli_value)
                        existing = config.get(field_name, {})
                        if isinstance(existing, dict):
                            existing.update(dict_config)
                            config[field_name] = existing
                        else:
                            config[field_name] = dict_config
                    except Exception as e:
                        raise ConfigurationError(
                            f"Failed to load dictionary config for field '{field_name}' from {cli_value}: {e}"
                        ) from e
                else:
                    # Simple override - check for file-loadable fields
                    try:
                        processed_value = process_file_loadable_value(
                            cli_value, field_name, info
                        )
                        config[field_name] = processed_value
                    except (ValueError, Exception) as e:
                        raise ConfigurationError(
                            f"Failed to process field '{field_name}': {e}"
                        ) from e

            # Apply property overrides for dict fields
            if info["is_dict"] and override_value:
                if field_name not in config:
                    config[field_name] = {}
                try:
                    self._apply_property_overrides(config[field_name], override_value)
                except Exception as e:
                    raise ConfigurationError(
                        f"Failed to apply property overrides for field '{field_name}': {e}"
                    ) from e

        return config

    def _apply_property_overrides(
        self, target_dict: Dict[str, Any], overrides: List[str]
    ) -> None:
        """Apply property path overrides to target dictionary."""
        for override in overrides:
            if ":" not in override:
                raise ValueError(
                    f"Invalid override format: {override} (expected key.path:value)"
                )

            path, value = override.split(":", 1)
            self._set_nested_property(target_dict, path, self._parse_value(value))

    def _set_nested_property(
        self, target: Dict[str, Any], path: str, value: Any
    ) -> None:
        """Set nested property using dot notation."""
        keys = path.split(".")
        current = target

        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set final value
        current[keys[-1]] = value

    def _parse_value(self, value_str: str) -> Any:
        """Parse string value to appropriate type."""
        # Try to parse as JSON first (handles numbers, booleans, etc.)
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            # Return as string if not valid JSON
            return value_str


# Convenience functions


def build_config_from_cli(
    config_class: Type,
    args: Optional[List[str]] = None,
    base_config_name: str = "config",
    exclude_fields: Optional[Set[str]] = None,
    include_fields: Optional[Set[str]] = None,
    field_filter: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
    use_annotations: bool = True,
) -> Any:
    """
    Convenience function to build any dataclass from CLI arguments.

    Args:
        config_class: Dataclass type to build
        args: Command-line arguments (defaults to sys.argv[1:])
        base_config_name: Name for base config file argument
        exclude_fields: Set of field names to exclude from CLI
        include_fields: Set of field names to include in CLI
        field_filter: Custom function to determine field inclusion
        use_annotations: Whether to respect cli_exclude() annotations (default: True)

    Returns:
        Instance of config_class built from CLI arguments

    Example:
        from dataclasses import dataclass
        from dataclass_cli import cli_exclude, cli_help, cli_file_loadable

        @dataclass
        class MyConfig:
            name: str = cli_help("Service name")
            message: str = cli_file_loadable(cli_help("Message text"))
            items: Optional[List[str]] = None
            settings: Optional[dict] = None
            _secret: str = cli_exclude(default="hidden")

        # Usage:
        config = build_config_from_cli(MyConfig, [
            '--name', 'test',
            '--items', 'a', 'b', 'c',
            '--message', '@/path/to/message.txt'
        ])
    """
    if args is None:
        args = sys.argv[1:]

    builder = GenericConfigBuilder(
        config_class,
        exclude_fields=exclude_fields,
        include_fields=include_fields,
        field_filter=field_filter,
        use_annotations=use_annotations,
    )
    parser = argparse.ArgumentParser(
        description=f"Build {config_class.__name__} from CLI"
    )
    builder.add_arguments(parser, base_config_name)

    parsed_args = parser.parse_args(args)
    return builder.build_config(parsed_args, base_config_name)


def build_config(config_class: Type, args: Optional[List[str]] = None) -> Any:
    """
    Simplified convenience function to build any dataclass from CLI arguments.

    Uses default settings suitable for most use cases.

    Args:
        config_class: Dataclass type to build
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Instance of config_class built from CLI arguments

    Example:
        from dataclasses import dataclass
        from dataclass_cli import build_config

        @dataclass
        class Config:
            name: str
            count: int = 10

        config = build_config(Config)  # Parses sys.argv automatically
    """
    return build_config_from_cli(config_class, args)
