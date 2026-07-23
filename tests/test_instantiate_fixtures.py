"""Fixture classes for instantiate() tests."""

from types import SimpleNamespace
from typing import List, Optional


class SimpleClass:
    """Basic class with simple __init__ parameters."""

    def __init__(self, name: str = "default", count: int = 0):
        self.name = name
        self.count = count


class Storage:
    """Storage configuration class."""

    def __init__(self, path: str = "/tmp", readonly: bool = False):
        self.path = path
        self.readonly = readonly


class App:
    """Application class with nested Storage dependency."""

    def __init__(self, name: str = "app", storage: Optional[Storage] = None):
        self.name = name
        self.storage = storage


class Database:
    """Database connection class."""

    def __init__(self, host: str = "localhost", port: int = 5432):
        self.host = host
        self.port = port


class Server:
    """Server with database and list of plugins."""

    def __init__(
        self,
        name: str = "server",
        database: Optional[Database] = None,
        plugins: Optional[List] = None,
    ):
        self.name = name
        self.database = database
        self.plugins = plugins if plugins is not None else []


class Toolkit:
    """Class with nested attributes for _attr_ traversal testing."""

    def __init__(self):
        self.tools = SimpleNamespace(
            search=SimpleNamespace(engine="default"),
            format=SimpleNamespace(style="compact"),
        )
        self.version = "1.0"


class ModuleContainer:
    """Class with a module attribute for deeper traversal."""

    def __init__(self, label: str = "container"):
        self.label = label
        self.inner = SimpleNamespace(deep=SimpleNamespace(value="found_it"))


class FailsToConstruct:
    """Class that always fails during construction."""

    def __init__(self):
        raise RuntimeError("always fails")


class FailsWithArgs:
    """Class that fails with specific args."""

    def __init__(self, value: int = 0):
        if value < 0:
            raise ValueError(f"value must be non-negative, got {value}")
        self.value = value


class InnerClass:
    """Class containing a nested class for import path testing."""

    class Nested:
        """Nested inner class."""

        def __init__(self, value: int = 42):
            self.value = value

    class DeepNested:
        """Double-nested inner class."""

        class Deeper:
            def __init__(self, x: int = 0):
                self.x = x


class NoAnnotations:
    """Class with no type annotations on __init__."""

    def __init__(self, a, b, c="default"):
        self.a = a
        self.b = b
        self.c = c


class CustomInit:
    """Class with custom initialization that validates."""

    def __init__(self, *, required_param: str):
        self.required_param = required_param


class RequiresArgs:
    """Class with required __init__ parameter (no default)."""

    def __init__(self, required: str):
        self.required = required


class HasListAnnotation:
    """Class with a List[str] annotated parameter."""

    def __init__(self, items: Optional[List[str]] = None):
        self.items = items


class BrokenAnnotations:
    """Class with unresolvable forward reference in annotations.

    typing.get_type_hints() will fail on this class because 'UndefinedType'
    cannot be resolved, triggering the fallback path in _get_init_annotations.
    """

    def __init__(self, x: "UndefinedType" = None):  # noqa: F821
        self.x = x


class HasOptionalStr:
    """Class with Optional[str] annotation for builtin-unwrap testing."""

    def __init__(self, name: str = "default", label: Optional[str] = None):
        self.name = name
        self.label = label
