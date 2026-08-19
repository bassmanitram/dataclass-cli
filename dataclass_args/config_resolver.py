"""
Configuration resolution pipeline: merge multiple sources into a dataclass instance.

This module implements the multi-stage pipeline that takes raw inputs (base configs,
config files, CLI arguments) and produces a fully-resolved dataclass instance.

Pipeline Stages:
    1. Normalize base_configs → List[Dict]  (files loaded, types validated)
    2. Apply base_configs → merged Dict      (shallow merge in order)
    3. Apply config file → merged Dict       (--config file merged on top)
    4. Apply CLI overrides → merged Dict     (per-field: file loading, dict loading, scalars)
    5. Reconstruct nested fields             (flat dict → nested dataclass instances)
    6. Validate append ranges                (min_args/max_args enforcement)
    7. Resolve fields                        (cli_resolve transformations)
    8. Instantiate dataclass                 (Dict → dataclass instance)

Precedence (later wins):
    base_configs[0] < base_configs[1] < ... < --config file < CLI arguments

Key Design Decisions:
    - CLI values trigger per-field processing (file loading for @file, structured
      file loading for dicts, property overrides for --abbrev key:value)
    - base_configs values are treated as pre-resolved (no @file processing)
    - None from argparse means "not specified" (field skipped, default preserved)
"""

import argparse
from typing import Any, Dict, List, Optional, Union

from .annotations import (
    get_cli_append_max_args,
    get_cli_append_min_args,
    get_cli_resolver,
    is_cli_append,
    is_cli_resolve,
)
from .config_applicator import ConfigApplicator
from .exceptions import ConfigurationError
from .file_loading import process_file_loadable_value
from .nested_processor import NestedFieldProcessor
from .utils import load_structured_file

# Type alias for base_configs parameter
BaseConfigInput = Union[str, Dict[str, Any], List[Union[str, Dict[str, Any]]]]


class ConfigResolver:
    """
    Resolves and merges configuration from multiple sources.

    Handles the complete pipeline:
    1. Base config normalization and merging
    2. Config file loading
    3. CLI override application
    4. Nested field reconstruction
    5. Append field validation
    6. Field resolution (cli_resolve)
    7. Dataclass instantiation
    """

    def __init__(
        self,
        config_class: type,
        config_fields: Dict[str, Dict[str, Any]],
        field_analyzer: Any,
    ):
        """
        Initialize config resolver.

        Args:
            config_class: Dataclass type to build
            config_fields: Dictionary of analyzed field information
            field_analyzer: FieldAnalyzer instance for nested field operations
        """
        self.config_class = config_class
        self.config_fields = config_fields
        self.field_analyzer = field_analyzer

    def build_config(
        self,
        args: argparse.Namespace,
        base_config_name: str = "config",
        base_configs: Optional[BaseConfigInput] = None,
    ) -> Any:
        """
        Build dataclass instance from parsed CLI arguments with hierarchical config merging.

        Configuration sources are merged in the following order (later sources override earlier):
        1. Programmatic base_configs (if provided) - files loaded and applied in order
        2. Config file from --config argument (if provided)
        3. CLI argument overrides

        Args:
            args: Parsed CLI arguments from argparse
            base_config_name: Name of the base config file argument (default: "config")
            base_configs: Optional base configuration(s) to apply before --config file.
                         Can be:
                         - str: Path to a single config file
                         - dict: A single configuration dictionary
                         - List[Union[str, dict]]: Multiple configs (files and/or dicts) applied in order

        Returns:
            Instance of the configured dataclass type

        Raises:
            ConfigurationError: If configuration is invalid or files cannot be loaded

        Example:
            # Single file path
            config = resolver.build_config(args, base_configs='defaults.yaml')

            # Single dict
            config = resolver.build_config(args, base_configs={'debug': True})

            # Mixed list
            config = resolver.build_config(
                args,
                base_configs=[
                    'base.yaml',              # Load file
                    {'env': 'staging'},       # Use dict
                    'overrides.json',         # Load file
                ]
            )
        """

        # Stage 1: Normalize and apply base configs
        normalized_configs = self.normalize_base_configs(base_configs)
        config_dict = self.apply_base_configs(normalized_configs)

        # Stage 2: Apply config file from --config argument
        config_dict = self.apply_config_file(config_dict, args, base_config_name)

        # Stage 4: Apply CLI argument overrides
        config_dict = self.apply_cli_overrides(config_dict, args)

        # Stage 5: Reconstruct nested dataclass instances
        config_dict = self.reconstruct_nested_fields(config_dict, args)

        # Stage 6: Validate append field ranges (if min_args/max_args specified)
        self.validate_append_ranges(config_dict)

        # Stage 7: Resolve fields (cli_resolve post-load transformation)
        config_dict = self.resolve_fields(config_dict)

        # Stage 8: Instantiate dataclass
        try:
            return self.config_class(**config_dict)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create {self.config_class.__name__}: {e}"
            ) from e

    def normalize_base_configs(
        self, base_configs: Optional[BaseConfigInput]
    ) -> List[Dict[str, Any]]:
        """
        Normalize base_configs input to list of dicts.

        Accepts:
        - None: Returns empty list
        - str: Load file, return list with one dict
        - dict: Return list with one dict
        - list: Process each element (load files, keep dicts)

        Args:
            base_configs: Configuration input in various formats

        Returns:
            List of configuration dictionaries

        Raises:
            ConfigurationError: If file cannot be loaded or invalid type
        """
        if base_configs is None:
            return []

        # Single string path
        if isinstance(base_configs, str):
            return [self._normalize_single_config(base_configs, None)]

        # Single dict
        if isinstance(base_configs, dict):
            return [base_configs]

        # List of strings and/or dicts
        if isinstance(base_configs, list):
            result = []
            for i, item in enumerate(base_configs):
                result.append(self._normalize_single_config(item, i))
            return result

        raise ConfigurationError(
            f"base_configs must be str, dict, or list, got {type(base_configs).__name__}"
        )

    def _normalize_single_config(
        self, item: Union[str, Dict[str, Any]], index: Optional[int]
    ) -> Dict[str, Any]:
        """
        Normalize a single config item (string path or dict).

        Args:
            item: Config item to normalize (str or dict)
            index: Index in list (None if single item)

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If file cannot be loaded or invalid type
        """
        # Dict: return as-is
        if isinstance(item, dict):
            return item

        # String: load from file
        if isinstance(item, str):
            return self._load_config_file(item, index)

        # Invalid type: raise error
        self._raise_invalid_type_error(item, index)

    def _load_config_file(self, path: str, index: Optional[int]) -> Dict[str, Any]:
        """
        Load configuration from file.

        Args:
            path: File path to load
            index: Index in list (None if single item)

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If file cannot be loaded
        """
        try:
            return load_structured_file(path)
        except Exception as e:
            location = f"base_configs[{index}]" if index is not None else "base_configs"
            raise ConfigurationError(
                f"Failed to load {location} from '{path}': {e}"
            ) from e

    def _raise_invalid_type_error(self, item: Any, index: Optional[int]) -> None:
        """
        Raise error for invalid config item type.

        Args:
            item: Invalid config item
            index: Index in list (None if single item)

        Raises:
            ConfigurationError: Always raises
        """
        type_name = type(item).__name__
        if index is not None:
            raise ConfigurationError(
                f"base_configs[{index}] must be str or dict, got {type_name}"
            )
        else:
            raise ConfigurationError(
                f"base_config item must be str or dict, got {type_name}"
            )

    def apply_base_configs(self, base_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply base configuration dictionaries (delegates to ConfigApplicator)."""
        return ConfigApplicator.apply_base_configs(base_configs)

    def apply_config_file(
        self,
        config: Dict[str, Any],
        args: argparse.Namespace,
        base_config_name: str,
    ) -> Dict[str, Any]:
        """Load and merge config from --config file (delegates to ConfigApplicator)."""
        return ConfigApplicator.apply_config_file(config, args, base_config_name)

    def reconstruct_nested_fields(
        self, config: Dict[str, Any], args: argparse.Namespace
    ) -> Dict[str, Any]:
        """Reconstruct nested fields (delegates to NestedFieldProcessor)."""
        flat_fields = self.field_analyzer.flatten_nested_fields(self.config_fields)
        processor = NestedFieldProcessor(self.config_class, self.config_fields)
        return processor.reconstruct(config, args, flat_fields)

    def apply_cli_overrides(
        self, config: Dict[str, Any], args: argparse.Namespace
    ) -> Dict[str, Any]:
        """
        Apply CLI argument overrides to configuration.

        Args:
            config: Current configuration dictionary
            args: Parsed CLI arguments

        Returns:
            Final configuration dictionary with CLI overrides applied

        Raises:
            ConfigurationError: If CLI argument processing fails

        Note:
            Only processes fields included in the dataclass (not excluded).
            Handles special cases: lists, dicts, file-loadable fields, property overrides, append actions.
        """
        # Only process fields that were included in CLI
        # Skip nested dataclass fields (handled by reconstruct_nested_fields)
        for field_name, info in self.config_fields.items():
            if info.get("is_nested_dataclass", False):
                continue

            cli_value = self._get_cli_value(args, field_name)
            if cli_value is not None:
                self._apply_field_override(config, field_name, info, cli_value)

            self._apply_property_overrides_for_field(config, field_name, info, args)

        return config

    def _get_cli_value(self, args: argparse.Namespace, field_name: str) -> Any:
        """Get CLI value for a field from parsed arguments."""
        arg_name = field_name.replace("-", "_")
        return getattr(args, arg_name, None)

    def _apply_field_override(
        self,
        config: Dict[str, Any],
        field_name: str,
        info: Dict[str, Any],
        cli_value: Any,
    ) -> None:
        """Apply CLI override for a field based on its type."""
        if info["is_list"]:
            self._apply_list_override(config, field_name, cli_value)
        elif info["is_dict"]:
            # Dict field without cli_resolve: load from file path (string) or use dict directly
            self._apply_dict_override(config, field_name, cli_value)
        else:
            # Scalar field OR cli_resolve field: pass through (handles @file, scalars, and resolver inputs)
            self._apply_scalar_override(config, field_name, info, cli_value)

    def _apply_list_override(
        self, config: Dict[str, Any], field_name: str, cli_value: Any
    ) -> None:
        """Apply list override - CLI values replace config values."""
        # CLI values replace config values (standard argparse behavior)
        # With nargs='+' or '*', cli_value is already a list
        # With action='append', cli_value is a list of sub-lists (if nargs specified) or list of values
        config[field_name] = cli_value

    def _apply_dict_override(
        self, config: Dict[str, Any], field_name: str, cli_value: Any
    ) -> None:
        """Apply dict override - load from file if string, use directly if dict."""
        try:
            if isinstance(cli_value, dict):
                # Already a dict (from programmatic usage) - use directly (no merging for cli_resolve)
                dict_config = cli_value
            elif isinstance(cli_value, str):
                # String value - try to load as file, but if looks like non-file string, pass through
                # Check if it looks like a file path (has common config file extension)
                looks_like_file = any(
                    cli_value.endswith(ext)
                    for ext in [".json", ".yaml", ".yml", ".toml"]
                )
                if looks_like_file:
                    # Intended as file path - load it (will error if not found)
                    dict_config = load_structured_file(cli_value)
                else:
                    # Plain string value - pass through directly (for resolvers that accept strings)
                    config[field_name] = cli_value
                    return
            else:
                # Unexpected type - use as-is
                config[field_name] = cli_value
                return

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

    def _apply_scalar_override(
        self,
        config: Dict[str, Any],
        field_name: str,
        info: Dict[str, Any],
        cli_value: Any,
    ) -> None:
        """Apply scalar override - process file-loadable fields if value is string."""
        try:
            if isinstance(cli_value, str):
                processed_value = process_file_loadable_value(
                    cli_value, field_name, info
                )
            else:
                processed_value = cli_value
            config[field_name] = processed_value
        except (ValueError, Exception) as e:
            raise ConfigurationError(
                f"Failed to process field '{field_name}': {e}"
            ) from e

    def _apply_property_overrides_for_field(
        self,
        config: Dict[str, Any],
        field_name: str,
        info: Dict[str, Any],
        args: argparse.Namespace,
    ) -> None:
        """Apply property overrides for dict fields."""
        if not info["is_dict"]:
            return

        override_arg_name = info["override_name"][2:].replace("-", "_")
        override_value = getattr(args, override_arg_name, None)
        if not override_value:
            return

        # Protection for cli_resolve fields with pre-built objects
        if is_cli_resolve(info):
            existing = config.get(field_name)
            if existing is not None and not isinstance(existing, dict):
                raise ConfigurationError(
                    f"Cannot apply property overrides to field '{field_name}': "
                    f"value is already a {type(existing).__name__}, not a dict."
                )

        if field_name not in config:
            config[field_name] = {}

        try:
            ConfigApplicator.apply_property_overrides(
                config[field_name], override_value
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to apply property overrides for field '{field_name}': {e}"
            ) from e

    def validate_append_ranges(self, config_dict: Dict[str, Any]) -> None:
        """
        Validate min/max argument counts for append fields.

        Args:
            config_dict: Configuration dictionary after CLI parsing

        Raises:
            ConfigurationError: If any append field violates min/max constraints
        """
        for field_name, info in self.config_fields.items():
            if not is_cli_append(info):
                continue

            min_args = get_cli_append_min_args(info)
            max_args = get_cli_append_max_args(info)

            # Skip if no range validation specified
            if min_args is None or max_args is None:
                continue

            field_value = config_dict.get(field_name)
            if not field_value:
                continue  # Empty is OK (validated by required/optional)

            # Validate each occurrence
            for i, occurrence in enumerate(field_value):
                self._validate_single_append_range(
                    field_name, i, occurrence, min_args, max_args
                )

    def _validate_single_append_range(
        self, field_name: str, index: int, occurrence: Any, min_args: int, max_args: int
    ) -> None:
        """
        Validate a single append field occurrence.

        Args:
            field_name: Name of the field
            index: Index of the occurrence (0-based)
            occurrence: The occurrence value to validate
            min_args: Minimum number of arguments expected
            max_args: Maximum number of arguments expected

        Raises:
            ConfigurationError: If the occurrence violates min/max constraints
        """
        # Normalize to list
        if not isinstance(occurrence, list):
            occurrence = [occurrence]

        arg_count = len(occurrence)

        if arg_count < min_args:
            raise ConfigurationError(
                f"Field '{field_name}' occurrence #{index+1}: "
                f"Expected at least {min_args} argument(s), got {arg_count}. "
                f"Each occurrence must have between {min_args} and {max_args} argument(s)."
            )

        if arg_count > max_args:
            raise ConfigurationError(
                f"Field '{field_name}' occurrence #{index+1}: "
                f"Expected at most {max_args} argument(s), got {arg_count}. "
                f"Each occurrence must have between {min_args} and {max_args} argument(s)."
            )

    def resolve_fields(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 7: Apply resolver functions to cli_resolve fields.

        For each field annotated with cli_resolve, calls the resolver function
        on the assembled raw value. Skips None values (resolver not called).

        Args:
            config_dict: Configuration dictionary after all merging stages

        Returns:
            Configuration dictionary with resolved field values

        Raises:
            ConfigurationError: If resolver raises an exception (wraps non-ConfigurationError)
        """
        for field_name, info in self.config_fields.items():
            if not is_cli_resolve(info):
                continue

            value = config_dict.get(field_name)
            if value is None:
                continue  # None bypass: resolver never called for None

            resolver = get_cli_resolver(info)
            if resolver is None:
                continue  # pragma: no cover - safety guard for mypy
            try:
                config_dict[field_name] = resolver(value)
            except ConfigurationError:
                raise  # Re-raise without wrapping
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to resolve field '{field_name}': {e}"
                ) from e

        return config_dict
