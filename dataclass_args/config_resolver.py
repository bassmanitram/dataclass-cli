"""
Configuration resolution pipeline orchestrator.

Coordinates the multi-stage pipeline by delegating to stage-specific processors:
    - ConfigMerger: Normalize and merge base_configs + config files
    - CliOverrideProcessor: Apply CLI argument overrides
    - ValueResolver: Resolve raw values, validate, apply cli_resolve
    - NestedFieldProcessor: Reconstruct nested dataclass instances

Pipeline Stages:
    1. Normalize base_configs → List[Dict]  (files loaded, types validated)
    2. Apply base_configs → merged Dict      (shallow merge in order)
    3. Apply config file → merged Dict       (--config file merged on top)
    4. Apply CLI overrides → merged Dict     (per-field: file loading, dict loading, scalars)
    5. Resolve raw values                    (process base_configs values that weren't overridden)
    6. Reconstruct nested fields             (flat dict → nested dataclass instances)
    7. Validate append ranges                (min_args/max_args enforcement)
    8. Resolve fields                        (cli_resolve transformations)
    9. Instantiate dataclass                 (Dict → dataclass instance)

Precedence (later wins):
    base_configs[0] < base_configs[1] < ... < --config file < CLI arguments
"""

import argparse
from typing import Any, Dict, List, Optional, Union

from .cli_overrides import CliOverrideProcessor
from .config_merging import ConfigMerger
from .exceptions import ConfigurationError
from .nested_processor import NestedFieldProcessor
from .value_resolution import ValueResolver

# Type alias for base_configs parameter
BaseConfigInput = Union[str, Dict[str, Any], List[Union[str, Dict[str, Any]]]]


class ConfigResolver:
    """
    Orchestrates the config resolution pipeline.

    Delegates to stage-specific processors:
    - ConfigMerger: file loading and merging
    - CliOverrideProcessor: CLI argument processing
    - ValueResolver: value resolution and validation
    - NestedFieldProcessor: nested dataclass reconstruction
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

        # Initialize stage-specific processors
        self.merger = ConfigMerger()
        self.cli_processor = CliOverrideProcessor(config_fields)
        self.value_resolver = ValueResolver(config_fields)

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
        """

        # Stage 1-2: Normalize and merge base configs
        normalized_configs = self.merger.normalize_base_configs(base_configs)
        config_dict = self.merger.apply_base_configs(normalized_configs)

        # Stage 3: Apply config file from --config argument
        config_dict = self.merger.apply_config_file(config_dict, args, base_config_name)

        # Stage 4: Apply CLI argument overrides
        config_dict = self.cli_processor.apply_cli_overrides(config_dict, args)

        # Stage 5: Resolve raw values from base_configs/config file
        config_dict = self.value_resolver.resolve_raw_values(config_dict, args)

        # Stage 6: Reconstruct nested dataclass instances
        config_dict = self._reconstruct_nested_fields(config_dict, args)

        # Stage 7: Validate append field ranges
        self.value_resolver.validate_append_ranges(config_dict)

        # Stage 8: Resolve fields (cli_resolve)
        config_dict = self.value_resolver.resolve_fields(config_dict)

        # Stage 9: Instantiate dataclass
        try:
            return self.config_class(**config_dict)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create {self.config_class.__name__}: {e}"
            ) from e

    def _reconstruct_nested_fields(
        self, config: Dict[str, Any], args: argparse.Namespace
    ) -> Dict[str, Any]:
        """Reconstruct nested fields (delegates to NestedFieldProcessor)."""
        flat_fields = self.field_analyzer.flatten_nested_fields(self.config_fields)
        processor = NestedFieldProcessor(self.config_class, self.config_fields)
        return processor.reconstruct(config, args, flat_fields)
