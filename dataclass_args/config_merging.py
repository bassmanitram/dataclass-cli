"""
Configuration merging: normalize and merge base_configs + config files.

This module handles the first two stages of the config resolution pipeline:
    1. Normalize base_configs → List[Dict]  (files loaded, types validated)
    2. Apply base_configs → merged Dict      (shallow merge in order)
    3. Apply config file → merged Dict       (--config file merged on top)

Precedence (later wins):
    base_configs[0] < base_configs[1] < ... < --config file
"""

import argparse
from typing import Any, Dict, List, Optional, Union

from .config_applicator import ConfigApplicator
from .exceptions import ConfigurationError
from .utils import load_structured_file

# Type alias for base_configs parameter
BaseConfigInput = Union[str, Dict[str, Any], List[Union[str, Dict[str, Any]]]]


class ConfigMerger:
    """
    Handles normalization and merging of base configs and config files.

    Responsibilities:
    - Normalize base_configs input (strings, dicts, lists) to List[Dict]
    - Load config files
    - Merge configs in order (shallow merge)
    - Apply --config file on top of base_configs
    """

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
