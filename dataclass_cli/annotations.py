"""
Annotations for controlling CLI field exposure.

Provides decorators and metadata for marking dataclass fields that should
be excluded from CLI argument generation or have special behaviors.
"""

from dataclasses import field
from typing import Any, Dict


def cli_exclude(**kwargs) -> Any:
    """
    Mark a dataclass field to be excluded from CLI arguments.

    This is a convenience function that adds metadata to a dataclass field
    to indicate it should not be exposed as a CLI argument.

    Args:
        **kwargs: Additional field parameters (default, default_factory, etc.)

    Returns:
        Field object with CLI exclusion metadata

    Example:
        @dataclass
        class Config:
            public_field: str                    # Will be CLI argument
            private_field: str = cli_exclude()   # Won't be CLI argument
            secret: str = cli_exclude(default="hidden")  # Won't be CLI argument
    """
    field_kwargs = kwargs.copy()
    metadata = field_kwargs.pop("metadata", {})
    metadata["cli_exclude"] = True
    field_kwargs["metadata"] = metadata
    return field(**field_kwargs)


def cli_include(**kwargs) -> Any:
    """
    Explicitly mark a dataclass field to be included in CLI arguments.

    This is useful when using include-only mode or for documentation purposes.

    Args:
        **kwargs: Additional field parameters (default, default_factory, etc.)

    Returns:
        Field object with CLI inclusion metadata

    Example:
        @dataclass
        class Config:
            included_field: str = cli_include()
            other_field: str = "default"  # Included by default anyway
    """
    field_kwargs = kwargs.copy()
    metadata = field_kwargs.pop("metadata", {})
    metadata["cli_include"] = True
    field_kwargs["metadata"] = metadata
    return field(**field_kwargs)


def cli_help(help_text: str, **kwargs) -> Any:
    """
    Add custom help text for a CLI argument.

    Args:
        help_text: Custom help text for the CLI argument
        **kwargs: Additional field parameters

    Returns:
        Field object with help text metadata

    Example:
        @dataclass
        class Config:
            host: str = cli_help("Database host address")
            port: int = cli_help("Database port number", default=5432)
    """
    field_kwargs = kwargs.copy()
    metadata = field_kwargs.pop("metadata", {})
    metadata["cli_help"] = help_text
    field_kwargs["metadata"] = metadata
    return field(**field_kwargs)


def cli_file_loadable(**kwargs) -> Any:
    """
    Mark a string field as file-loadable via '@' prefix.

    When a CLI argument value starts with '@', the remaining part is treated as a file path.
    The file is read as UTF-8 encoded text and used as the field value.

    Args:
        **kwargs: Additional field parameters (default, default_factory, etc.)

    Returns:
        Field object with file-loadable metadata

    Example:
        @dataclass
        class Config:
            message: str = cli_file_loadable()
            system_prompt: str = cli_file_loadable(default="You are a helpful assistant.")

            # For combining with help text, use field() directly:
            enhanced: str = field(
                default="",
                metadata={'cli_help': "Message content", 'cli_file_loadable': True}
            )

        # Usage:
        # --message "Hello world"           # Uses literal value
        # --message "@/path/to/file.txt"    # Reads file content
    """
    field_kwargs = kwargs.copy()
    metadata = field_kwargs.pop("metadata", {})
    metadata["cli_file_loadable"] = True
    field_kwargs["metadata"] = metadata
    return field(**field_kwargs)


def combine_annotations(*annotations, **field_kwargs) -> Any:
    """
    Combine multiple CLI annotations into a single field.

    Args:
        *annotations: List of annotation functions (cli_help, cli_file_loadable, etc.)
        **field_kwargs: Additional field parameters

    Returns:
        Field object with combined metadata

    Example:
        @dataclass
        class Config:
            message: str = combine_annotations(
                cli_help("Message content"),
                cli_file_loadable(),
                default="Default message"
            )
    """
    combined_metadata = field_kwargs.pop("metadata", {})

    # Extract metadata from each annotation
    for annotation in annotations:
        if hasattr(annotation, "metadata") and annotation.metadata:
            combined_metadata.update(annotation.metadata)

    field_kwargs["metadata"] = combined_metadata
    return field(**field_kwargs)


def is_cli_excluded(field_info: Dict[str, Any]) -> bool:
    """
    Check if a field should be excluded from CLI arguments.

    Args:
        field_info: Field information dictionary from GenericConfigBuilder

    Returns:
        True if field should be excluded from CLI
    """
    # Check for explicit CLI exclusion metadata
    field_obj = field_info.get("field_obj")
    if field_obj and hasattr(field_obj, "metadata"):
        return field_obj.metadata.get("cli_exclude", False)

    return False


def is_cli_included(field_info: Dict[str, Any]) -> bool:
    """
    Check if a field is explicitly marked for CLI inclusion.

    Args:
        field_info: Field information dictionary from GenericConfigBuilder

    Returns:
        True if field is explicitly marked for CLI inclusion
    """
    field_obj = field_info.get("field_obj")
    if field_obj and hasattr(field_obj, "metadata"):
        return field_obj.metadata.get("cli_include", False)

    return False


def is_cli_file_loadable(field_info: Dict[str, Any]) -> bool:
    """
    Check if a field is marked as file-loadable via '@' prefix.

    Args:
        field_info: Field information dictionary from GenericConfigBuilder

    Returns:
        True if field supports file loading via '@' prefix
    """
    field_obj = field_info.get("field_obj")
    if field_obj and hasattr(field_obj, "metadata"):
        return field_obj.metadata.get("cli_file_loadable", False)

    return False


def get_cli_help(field_info: Dict[str, Any]) -> str:
    """
    Get custom help text for a CLI argument.

    Args:
        field_info: Field information dictionary from GenericConfigBuilder

    Returns:
        Custom help text if available, otherwise empty string
    """
    field_obj = field_info.get("field_obj")
    if field_obj and hasattr(field_obj, "metadata"):
        help_text = field_obj.metadata.get("cli_help", "")

        # Add file-loadable hint to help text if applicable
        if field_obj.metadata.get("cli_file_loadable", False):
            if help_text:
                help_text += " (supports @file.txt to load from file)"
            else:
                help_text = "supports @file.txt to load from file"

        return help_text

    return ""


def annotation_filter(field_name: str, field_info: Dict[str, Any]) -> bool:
    """
    Filter function that respects field annotations.

    This filter function excludes fields marked with cli_exclude() and
    can be used with GenericConfigBuilder.

    Args:
        field_name: Name of the field
        field_info: Field information dictionary

    Returns:
        True if field should be included in CLI

    Example:
        builder = GenericConfigBuilder(MyConfig, field_filter=annotation_filter)
    """
    return not is_cli_excluded(field_info)
