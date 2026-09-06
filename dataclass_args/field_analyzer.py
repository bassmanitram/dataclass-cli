"""
Field analysis and validation for dataclass CLI generation.

This module inspects dataclass field definitions (types, defaults, metadata
annotations) and produces a normalized dictionary of field information that
drives all downstream processing — argument registration, config resolution,
and collision detection.

Data Flow:
    Dataclass Type
        → analyze_config_fields()
            → For each field: type inspection, nested detection, default extraction
            → Filtering (cli_exclude), resolve compatibility checks
            → Positional argument validation
        → Dict[field_name, field_info]  (consumed by ArgumentRegistry, ConfigResolver)

Key Concepts:
    - field_info dict: Normalized representation of one field with keys like
      'type', 'is_list', 'is_dict', 'is_nested_dataclass', 'cli_name', etc.
    - Collision detection: Ensures flattened nested fields don't produce
      duplicate CLI argument names or short options.
    - Positional constraints: At most one greedy positional (nargs='*'/'+'),
      must be last.
"""

from dataclasses import MISSING, fields, is_dataclass
from typing import Any, Dict, Optional, Tuple, Type

# Import typing utilities with Python 3.8+ compatibility
try:
    from typing import get_type_hints  # type: ignore[attr-defined,no-redef]
except ImportError:  # pragma: no cover
    from typing_extensions import get_type_hints  # type: ignore[assignment,no-redef]  # noqa: E501  # pragma: no cover

from .annotations import (
    get_cli_nested_prefix,
    get_cli_override_name,
    get_cli_positional_nargs,
    get_cli_short,
    is_cli_append,
    is_cli_excluded,
    is_cli_file_loadable,
    is_cli_nested,
    is_cli_positional,
    is_cli_resolve,
)
from .exceptions import ConfigBuilderError
from .nested_processor import NestedFieldProcessor
from .type_inspector import TypeInspector


class FieldAnalyzer:
    """
    Analyzes and validates dataclass fields for CLI argument generation.

    Responsible for:
    - Type inspection and categorization
    - Field naming (CLI names, override names)
    - Validation of field annotations and constraints
    - Detection of field collisions
    """

    def __init__(self, config_class: Type):
        """
        Initialize field analyzer for a dataclass.

        Args:
            config_class: Dataclass type to analyze

        Raises:
            ConfigBuilderError: If config_class is not a dataclass
        """
        if not is_dataclass(config_class):
            raise ConfigBuilderError(
                f"config_class must be a dataclass, got {config_class}"
            )
        self.config_class = config_class

    def should_include_field(self, field_name: str, field_info: Dict[str, Any]) -> bool:
        """Determine if a field should be included in CLI arguments."""

        # Apply annotation filter
        if is_cli_excluded(field_info):
            return False

        # Default: include all fields
        return True

    def analyze_config_fields(self) -> Dict[str, Dict[str, Any]]:
        """Analyze dataclass fields for type information."""
        fields_info = {}
        type_hints = get_type_hints(self.config_class)

        for field_obj in fields(self.config_class):
            field_info = self._analyze_single_field(field_obj, type_hints)

            # Only include field if it passes filtering
            if self.should_include_field(field_obj.name, field_info):
                fields_info[field_obj.name] = field_info

        # Validate positional arguments
        self.validate_positional_arguments(fields_info)

        return fields_info

    def _analyze_single_field(
        self, field_obj: Any, type_hints: Dict[str, Type]
    ) -> Dict[str, Any]:
        """
        Analyze a single field and return its info dictionary.

        Extracts type information, nested dataclass metadata, and default values.
        This is the core analysis function that builds the normalized field_info
        representation used throughout the pipeline.

        Args:
            field_obj: The dataclass field object
            type_hints: Type hints dictionary for the class

        Returns:
            Dictionary containing field analysis information
        """
        field_type = type_hints.get(field_obj.name, field_obj.type)

        # Determine field category
        is_optional = TypeInspector.is_optional(field_type)
        if is_optional:
            # Extract the non-None type from Optional[T]
            field_type = TypeInspector.unwrap_optional(field_type)

        origin, args = TypeInspector.get_origin_and_args(field_type)
        is_list = TypeInspector.is_list_type(field_type)
        is_dict = TypeInspector.is_dict_type(field_type)

        # Check if this is a nested dataclass with cli_nested annotation
        is_nested_dataclass, nested_prefix = self._determine_nested_prefix(
            field_type, field_obj
        )

        # Extract default value or factory
        default_value = self._extract_default_value(field_obj)
        has_default = (
            field_obj.default is not MISSING or field_obj.default_factory is not MISSING
        )

        field_info = {
            "type": field_type,
            "origin": origin,
            "args": args,
            "is_optional": is_optional,
            "is_list": is_list,
            "is_dict": is_dict,
            "is_nested_dataclass": is_nested_dataclass,
            "nested_prefix": nested_prefix,
            "default": default_value,
            "has_default": has_default,
            "cli_name": self.field_to_cli_name(field_obj.name),
            "override_name": self.field_to_override_name(field_obj.name, field_obj),
            "field_obj": field_obj,  # Include field object for metadata access
        }

        # Check for cli_resolve and validate/force appropriate behavior
        self._apply_resolve_overrides(field_info, field_obj, is_list)

        return field_info

    def _determine_nested_prefix(
        self, field_type: Type, field_obj: Any
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if field is a nested dataclass and compute its prefix.

        Nested dataclass fields with cli_nested annotation are "flattened" into
        the parent CLI namespace. The prefix determines how their names are
        prefixed to avoid collisions (e.g., agent-name, model-type).

        Args:
            field_type: The type of the field
            field_obj: The dataclass field object

        Returns:
            Tuple of (is_nested_dataclass, nested_prefix)
        """
        if not is_dataclass(field_type):
            return False, None

        # Check if it has cli_nested annotation
        temp_info = {"field_obj": field_obj}
        is_nested_dataclass = is_cli_nested(temp_info)

        if not is_nested_dataclass:
            return False, None

        # Determine prefix
        prefix_value = get_cli_nested_prefix(temp_info)
        if prefix_value is None:
            # Auto-prefix with field name
            nested_prefix = f"{field_obj.name}-"
        elif prefix_value == "":
            # No prefix (flatten completely)
            nested_prefix = ""
        else:
            # Custom prefix (ensure it ends with hyphen for consistency)
            nested_prefix = (
                f"{prefix_value}-" if not prefix_value.endswith("-") else prefix_value
            )

        return True, nested_prefix

    def _extract_default_value(self, field_obj: Any) -> Any:
        """
        Extract the default value from a field object.

        Handles both direct defaults (field: int = 42) and default factories
        (field: list = field(default_factory=list)).

        Args:
            field_obj: The dataclass field object

        Returns:
            The default value, or None if no default
        """
        has_default = field_obj.default is not MISSING
        has_default_factory = field_obj.default_factory is not MISSING

        if has_default:
            return field_obj.default
        elif has_default_factory and callable(field_obj.default_factory):
            # Call factory to get default value
            return field_obj.default_factory()
        else:
            return None

    def _apply_resolve_overrides(
        self, field_info: Dict[str, Any], field_obj: Any, is_list: bool
    ) -> None:
        """
        Apply cli_resolve annotation overrides to field info.

        cli_resolve fields undergo post-load transformation via a resolver function.
        For non-list fields, we force dict behavior to enable file loading + property
        overrides (the dict is passed to the resolver for transformation).

        Args:
            field_info: Field info dictionary to modify
            field_obj: The dataclass field object
            is_list: Whether the field is a list type
        """
        temp_info = {"field_obj": field_obj}
        if not is_cli_resolve(temp_info):
            return

        self.validate_resolve_compatibility(field_obj, temp_info)
        if is_list:
            # List field: keep list behavior, resolver transforms entire list
            pass
        else:
            # Non-list field: force dict behavior (file path + overrides)
            field_info["is_dict"] = True
            field_info["is_list"] = False

    def validate_resolve_compatibility(
        self, field_obj: Any, temp_info: Dict[str, Any]
    ) -> None:
        """
        Validate that cli_resolve is not combined with incompatible annotations.

        Args:
            field_obj: The dataclass field object
            temp_info: Temporary field info dict for metadata access

        Raises:
            ConfigBuilderError: If incompatible annotations are detected
        """
        incompatible = []
        if is_cli_positional(temp_info):
            incompatible.append("cli_positional")
        if is_cli_nested(temp_info):
            incompatible.append("cli_nested")
        if is_cli_append(temp_info):
            incompatible.append("cli_append")
        if is_cli_excluded(temp_info):
            incompatible.append("cli_exclude")
        if is_cli_file_loadable(temp_info):
            incompatible.append("cli_file_loadable")

        if incompatible:
            raise ConfigBuilderError(
                f"Field '{field_obj.name}': cli_resolve cannot be combined with "
                f"{', '.join(incompatible)}"
            )

    def validate_positional_arguments(
        self, fields_info: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Validate positional argument constraints.

        Rules:
        1. At most ONE positional field can use nargs='*' or '+'
        2. If present, positional list must be the LAST positional argument

        Raises:
            ConfigBuilderError: If validation fails
        """
        positional_fields = []
        positional_list_fields = []

        for field_name, info in fields_info.items():
            if is_cli_positional(info):
                positional_fields.append((field_name, info))

                nargs = get_cli_positional_nargs(info)
                # Check if this is a "list" positional (greedy)
                if nargs in ("*", "+"):
                    positional_list_fields.append((field_name, nargs))

        # Rule 1: At most one positional list
        if len(positional_list_fields) > 1:
            field_names = [
                f"'{name}' (nargs='{nargs}')" for name, nargs in positional_list_fields
            ]
            raise ConfigBuilderError(
                f"Only one positional list argument allowed, found {len(positional_list_fields)}: "
                f"{', '.join(field_names)}. Use optional lists with flags for additional lists:\n"
                f"  Example: field: List[str] = cli_short('f')  # Use --field instead"
            )

        # Rule 2: Positional list must be last
        if positional_list_fields:
            self._validate_positional_list_is_last(
                positional_fields, positional_list_fields
            )

    def _validate_positional_list_is_last(
        self,
        positional_fields: list,
        positional_list_fields: list,
    ) -> None:
        """
        Validate that positional list field is the last positional argument.

        This is an argparse requirement: greedy positionals consume all remaining
        arguments, so nothing can come after them.

        Args:
            positional_fields: List of all positional fields
            positional_list_fields: List of positional list fields

        Raises:
            ConfigBuilderError: If positional list is not last
        """
        list_field_name, list_nargs = positional_list_fields[0]
        list_field_index = self._find_positional_list_index(
            positional_fields, list_field_name
        )

        # Check if there are any positionals after the list
        if list_field_index < len(positional_fields) - 1:
            later_fields = [
                name for name, _ in positional_fields[list_field_index + 1 :]
            ]
            raise ConfigBuilderError(
                f"Positional list argument '{list_field_name}' (nargs='{list_nargs}') must be last.\n"
                f"Found positional argument(s) after it: {', '.join([repr(f) for f in later_fields])}.\n"
                f"Consider making them optional arguments with flags:\n"
                f"  Example: {later_fields[0]}: str = cli_short('{later_fields[0][0]}', default='value')"
            )

    def _find_positional_list_index(
        self, positional_fields: list, list_field_name: str
    ) -> int:
        """
        Find the index of the positional list field.

        Args:
            positional_fields: List of all positional fields
            list_field_name: Name of the list field to find

        Returns:
            Index of the list field
        """
        return next(
            i
            for i, (name, _) in enumerate(positional_fields)
            if name == list_field_name
        )

    def field_to_cli_name(self, field_name: str) -> str:
        """Convert field name to CLI argument name."""
        return "--" + field_name.replace("_", "-")

    def field_to_override_name(self, field_name: str, field_obj: Any = None) -> str:
        """
        Convert field name to override argument name.

        Uses cli_override_name annotation if present, otherwise generates
        an abbreviation from the first letter of each underscore-separated word.

        Args:
            field_name: The dataclass field name
            field_obj: Optional field object to check for cli_override_name annotation

        Returns:
            Override argument name with -- prefix (e.g., '--sc', '--sk')
        """
        # Check for explicit override name annotation
        if field_obj is not None:
            temp_info = {"field_obj": field_obj}
            custom_name = get_cli_override_name(temp_info)
            if custom_name is not None:
                return "--" + custom_name

        # Fall back to algorithmic abbreviation
        words = field_name.split("_")
        if len(words) == 1:
            return "--" + field_name[0]
        else:
            return "--" + "".join(word[0] for word in words if word)

    def flatten_nested_fields(
        self, config_fields: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Flatten nested fields (delegates to NestedFieldProcessor)."""
        processor = NestedFieldProcessor(self.config_class, config_fields)
        return processor.flatten()

    def validate_nested_collisions(
        self, config_fields: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Validate that there are no field name collisions when flattening nested dataclasses.

        Raises:
            ConfigBuilderError: If collisions are detected
        """
        flat_fields = self.flatten_nested_fields(config_fields)
        cli_names = self._collect_nested_cli_names(flat_fields)

        if cli_names["collisions"]:  # pragma: no cover
            self._raise_nested_collision_error(cli_names["collisions"])

    def _collect_nested_cli_names(self, flat_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect CLI names and detect collisions.

        Iterates through flattened fields to build a map of CLI names. If the same
        CLI name appears twice, records it as a collision. This is a secondary
        safeguard; the primary detection happens in NestedFieldProcessor.

        Args:
            flat_fields: Flattened field mappings

        Returns:
            Dictionary with 'names' (mapping) and 'collisions' (list)
        """
        # Check for duplicate CLI names
        # NOTE: This collision detection is a secondary safeguard. The primary
        # detection is in NestedFieldProcessor._check_collision() which raises
        # during flatten_nested_fields(). This code is unreachable in practice.
        cli_names: Dict[str, Dict[str, Any]] = {}
        collisions: list = []

        for cli_name, mapping in flat_fields.items():
            if cli_name in cli_names:  # pragma: no cover
                # Collision detected
                prev_mapping = cli_names[cli_name]

                # Build descriptive collision info
                if mapping.get("parent_field"):
                    source1 = f"{mapping['parent_field']}.{mapping['nested_field']}"
                else:
                    source1 = mapping["field_name"]

                if prev_mapping.get("parent_field"):
                    source2 = (
                        f"{prev_mapping['parent_field']}.{prev_mapping['nested_field']}"
                    )
                else:
                    source2 = prev_mapping["field_name"]

                collisions.append((cli_name, source1, source2))
            else:
                cli_names[cli_name] = mapping

        return {"names": cli_names, "collisions": collisions}

    def _raise_nested_collision_error(self, collisions: list) -> None:
        """
        Raise a detailed error about nested field collisions.

        Args:
            collisions: List of collision tuples (cli_name, source1, source2)

        Raises:
            ConfigBuilderError: Always raises with detailed message
        """
        # Build error message
        error_lines = [
            "Field name collision detected when flattening nested dataclasses:",
            "",
        ]

        for cli_name, source1, source2 in collisions:
            error_lines.append(f"  {cli_name}")
            error_lines.append(f"    - {source1}")
            error_lines.append(f"    - {source2}")
            error_lines.append("")

        error_lines.extend(
            [
                "Solutions:",
                "  1. Add prefix to nested fields:",
                "     nested: NestedClass = cli_nested(prefix='n')",
                "  2. Rename conflicting fields",
                "  3. Use auto-prefix (don't specify prefix='')",
            ]
        )

        raise ConfigBuilderError("\n".join(error_lines))

    def validate_short_option_collisions(
        self, config_fields: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Validate that there are no short option collisions when nested fields have no prefix.

        Short options are only checked for nested fields with empty prefix (prefix="").
        Nested fields with non-empty prefix do not support short options.

        Raises:
            ConfigBuilderError: If short option collisions are detected
        """
        flat_fields = self.flatten_nested_fields(config_fields)
        short_options, collisions = self._collect_short_options(flat_fields)

        if collisions:
            self._raise_short_option_collision_error(collisions)

    def _collect_short_options(
        self, flat_fields: Dict[str, Any]
    ) -> Tuple[Dict[str, Tuple[str, str]], list]:
        """
        Collect short options and detect collisions.

        Builds a map of short options to their source fields. Short options are
        single-character flags (e.g., -h, -v) that can be used as aliases for
        long options. Multiple fields with the same short option cause collisions.

        Args:
            flat_fields: Flattened field mappings

        Returns:
            Tuple of (short_options dict, collisions list)
        """
        # Map short option -> (cli_name, source_description)
        short_options: Dict[str, tuple[str, str]] = {}
        collisions: list = []

        for cli_name, mapping in flat_fields.items():
            if mapping.get("parent_field"):
                # Nested field - only check if no prefix
                prefix = mapping["prefix"]
                if prefix == "":
                    info = mapping["nested_info"]
                    short = get_cli_short(info)
                    if short:
                        source = f"{mapping['parent_field']}.{mapping['nested_field']}"
                        self._check_short_option_collision(
                            short, cli_name, source, short_options, collisions
                        )
            else:
                # Regular field
                info = mapping["field_info"]
                if not info.get("is_nested_dataclass", False):
                    short = get_cli_short(info)
                    if short:
                        source = mapping["field_name"]
                        self._check_short_option_collision(
                            short, cli_name, source, short_options, collisions
                        )

        return short_options, collisions

    def _check_short_option_collision(
        self,
        short: str,
        cli_name: str,
        source: str,
        short_options: Dict[str, Tuple[str, str]],
        collisions: list,
    ) -> None:
        """
        Check for and record a short option collision.

        Args:
            short: The short option character
            cli_name: CLI name for the field
            source: Source description for the field
            short_options: Dictionary of existing short options
            collisions: List to append collision info to
        """
        if short in short_options:
            prev_cli_name, prev_source = short_options[short]
            collisions.append(
                (
                    f"-{short}",
                    cli_name,
                    source,
                    prev_cli_name,
                    prev_source,
                )
            )
        else:
            short_options[short] = (cli_name, source)

    def _raise_short_option_collision_error(self, collisions: list) -> None:
        """
        Raise a detailed error about short option collisions.

        Args:
            collisions: List of collision tuples

        Raises:
            ConfigBuilderError: Always raises with detailed message
        """
        # Build error message
        error_lines = ["Short option collision detected:", ""]

        for short_opt, cli_name1, source1, cli_name2, source2 in collisions:
            error_lines.append(f"  {short_opt}")
            error_lines.append(f"    - {source1} ({cli_name1})")
            error_lines.append(f"    - {source2} ({cli_name2})")
            error_lines.append("")

        error_lines.extend(
            [
                "Solutions:",
                "  1. Remove short option from one of the fields",
                "  2. Use different short options",
                "  3. Add prefix to nested field:",
                "     nested: NestedClass = cli_nested(prefix='n')",
            ]
        )

        raise ConfigBuilderError("\n".join(error_lines))

    def validate_override_name_collisions(
        self, config_fields: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Detect and report override name collisions between dict fields.

        Two dict fields that generate the same override abbreviation (e.g.,
        sandbox_config and skills_config both → --sc) will cause argparse
        to raise an error. This method detects the collision early with a
        clear error message.

        Args:
            config_fields: Analyzed field information dictionary

        Raises:
            ConfigBuilderError: If two dict fields share the same override name
        """
        seen: Dict[str, str] = {}
        for field_name, info in config_fields.items():
            if not info.get("is_dict", False):
                continue
            override = info.get("override_name", "")
            if not override:
                continue
            if override in seen:
                raise ConfigBuilderError(
                    f"Override name collision detected:\n"
                    f"  {override}\n"
                    f"    - {seen[override]}\n"
                    f"    - {field_name}\n"
                    f"Use cli_override_name() to set a custom override for one of them."
                )
            seen[override] = field_name
