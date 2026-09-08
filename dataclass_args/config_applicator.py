"""
Configuration application utilities.

Consolidates logic for applying configurations from various sources.
"""

import argparse
from typing import Any, Dict, List

from .exceptions import ConfigurationError
from .utils import load_structured_file


class ConfigApplicator:
    """
    Apply configurations from various sources (base configs, files, CLI overrides).

    Consolidates repeated patterns in _apply_* methods.
    """

    @staticmethod
    def apply_base_configs(base_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply base configuration dictionaries in order.

        Args:
            base_configs: List of configuration dictionaries to merge in order

        Returns:
            Merged configuration dictionary

        Note:
            Each config is applied sequentially with shallow merge.
            Later configs override earlier ones.
        """
        config = {}

        for base_config in base_configs:
            if not isinstance(base_config, dict):
                raise ConfigurationError(
                    f"base_configs must contain dictionaries, got {type(base_config)}"
                )
            config.update(base_config)

        return config

    @staticmethod
    def apply_config_file(
        config: Dict[str, Any],
        args: argparse.Namespace,
        base_config_name: str,
    ) -> Dict[str, Any]:
        """
        Load and merge configuration from --config file argument.

        Args:
            config: Current configuration dictionary
            args: Parsed CLI arguments
            base_config_name: Name of the config file argument

        Returns:
            Updated configuration dictionary with file config merged

        Raises:
            ConfigurationError: If file cannot be loaded
        """
        base_config_value = getattr(args, base_config_name.replace("-", "_"), None)

        if base_config_value:
            try:
                file_config = load_structured_file(base_config_value)
                config.update(file_config)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load config file '{base_config_value}': {e}"
                ) from e

        return config

    @staticmethod
    def apply_property_overrides(
        target_dict: Dict[str, Any], overrides: List[str]
    ) -> None:
        """
        Apply property path overrides to target dictionary.

        Args:
            target_dict: Dictionary to apply overrides to (modified in place)
            overrides: List of "key.path:value" override strings

        Raises:
            ValueError: If override format is invalid
        """
        for override in overrides:
            if ":" not in override:
                raise ValueError(
                    f"Invalid override format: {override} (expected key.path:value)"
                )

            path, value_str = override.split(":", 1)
            ConfigApplicator.set_nested_property(target_dict, path, value_str)

    @staticmethod
    def set_nested_property(target: Dict[str, Any], path: str, value_str: str) -> None:
        """
        Set nested property using dot notation with list index support.

        Supports:
        - Dict navigation: "outer.inner.key" → target["outer"]["inner"]["key"]
        - List indexing: "items.0" → target["items"][0] (when items is a list)
        - List append: "items.+" → target["items"].append(value)
        - Mixed: "data.0.name" → target["data"][0]["name"]

        List indexing is determined by the runtime type of the container:
        - If the container is a list and the key is a non-negative integer, index into it
        - If the container is a dict, the key is always a string key (even "0" or "+")
        - Missing intermediate keys always create dicts (never auto-create lists)

        Args:
            target: Target dictionary
            path: Property path (e.g., "outer.inner.key" or "items.0.name")
            value_str: String value to parse and set

        Raises:
            ValueError: If list index is out of range, or navigation fails
        """
        keys = path.split(".")
        current = target

        # Navigate to parent of final key
        for key in keys[:-1]:
            if isinstance(current, list):
                current = ConfigApplicator._navigate_list(current, key)
            elif isinstance(current, dict):
                if key not in current:
                    current[key] = {}
                current = current[key]
            else:
                raise ValueError(
                    f"Cannot set nested property: {key} is not a dictionary"
                )

        # Set final value
        final_key = keys[-1]
        parsed_value = ConfigApplicator.parse_value(value_str)

        if isinstance(current, list):
            ConfigApplicator._set_list_element(current, final_key, parsed_value)
        elif isinstance(current, dict):
            current[final_key] = parsed_value
        else:
            raise ValueError(
                f"Cannot set nested property: {final_key} is not a dictionary"
            )

    @staticmethod
    def _navigate_list(container: list, key: str) -> Any:
        """
        Navigate into a list element during path traversal.

        Args:
            container: The list to index into
            key: Path segment (must be a non-negative integer)

        Returns:
            The list element at the given index

        Raises:
            ValueError: If key is not a valid index or is out of range
        """
        if not key.isdigit():
            raise ValueError(f"Cannot navigate list with non-numeric key: {key}")
        index = int(key)
        if index >= len(container):
            raise ValueError(
                f"List index out of range: {index} "
                f"for list of length {len(container)}"
            )
        return container[index]

    @staticmethod
    def _set_list_element(container: list, key: str, value: Any) -> None:
        """
        Set an element in a list by index or append with '+'.

        Args:
            container: The list to modify
            key: Index string or '+' for append
            value: Parsed value to set

        Raises:
            ValueError: If key is not a valid index or is out of range
        """
        if key == "+":
            container.append(value)
        elif key.isdigit():
            index = int(key)
            if index >= len(container):
                raise ValueError(
                    f"List index out of range: {index} "
                    f"for list of length {len(container)}"
                )
            container[index] = value
        else:
            raise ValueError(f"Cannot set list element with non-numeric key: {key}")

    @staticmethod
    def parse_value(value_str: str) -> Any:
        """
        Parse string value to appropriate type.

        Tries JSON parsing first (for numbers, bools, etc.), falls back to string.
        """
        import json

        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            return value_str
