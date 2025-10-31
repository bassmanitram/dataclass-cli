"""
Exceptions for dataclass CLI configuration system.
"""


class ConfigBuilderError(Exception):
    """Base exception for configuration builder errors."""

    pass


class ConfigurationError(ConfigBuilderError):
    """Exception raised for configuration validation errors."""

    pass


class FileLoadingError(ConfigBuilderError):
    """Exception raised when file loading fails."""

    pass
