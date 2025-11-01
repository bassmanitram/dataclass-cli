# Dataclass Argparse

Generate command-line interfaces from Python dataclasses.

[![Tests](https://github.com/bassmanitram/dataclass-config/actions/workflows/test.yml/badge.svg)](https://github.com/bassmanitram/dataclass-config/actions/workflows/test.yml)
[![Code Quality](https://github.com/bassmanitram/dataclass-config/actions/workflows/lint.yml/badge.svg)](https://github.com/bassmanitram/dataclass-config/actions/workflows/lint.yml)
[![Examples](https://github.com/bassmanitram/dataclass-config/actions/workflows/examples.yml/badge.svg)](https://github.com/bassmanitram/dataclass-config/actions/workflows/examples.yml)
[![codecov](https://codecov.io/gh/bassmanitram/dataclass-config/branch/main/graph/badge.svg)](https://codecov.io/gh/bassmanitram/dataclass-config)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/dataclass-config.svg)](https://badge.fury.io/py/dataclass-config)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Automatic CLI Generation** - Generate CLI from dataclass definitions
- **Type-Safe Parsing** - Type-aware argument parsing for standard Python types
- **Positional Arguments** - Support for positional args with `cli_positional()`
- **Short Options** - Concise `-n` flags in addition to `--name`
- **Boolean Flags** - Proper `--flag` and `--no-flag` boolean handling
- **Value Validation** - Restrict values with `cli_choices()`
- **File Loading** - Load parameters from files using `@filename` syntax
- **Config Merging** - Combine configuration files with CLI overrides
- **Flexible Types** - Support for `List`, `Dict`, `Optional`, and custom types
- **Rich Annotations** - Custom help text, exclusions, and combinations
- **Minimal Dependencies** - Lightweight with optional format support

## Quick Start

### Installation

```bash
pip install dataclass-config

# With optional format support
pip install "dataclass-config[yaml,toml]"  # YAML and TOML config files
pip install "dataclass-config[all]"        # All optional dependencies
```

### Basic Usage

```python
from dataclasses import dataclass
from dataclass_config import build_config

@dataclass
class Config:
    name: str
    count: int = 10
    debug: bool = False

# Generate CLI from dataclass
config = build_config(Config)

# Use your config
print(f"Running {config.name} with count={config.count}, debug={config.debug}")
```

```bash
$ python app.py --name "MyApp" --count 5 --debug
Running MyApp with count=5, debug=True

$ python app.py --help
usage: app.py [-h] [--config CONFIG] [--name NAME] [--count COUNT] [--debug] [--no-debug]

Build Config from CLI

options:
  -h, --help       show this help message and exit
  --config CONFIG  Base configuration file (JSON, YAML, or TOML)
  --name NAME      name
  --count COUNT    count
  --debug          debug (default: False)
  --no-debug       Disable debug
```

## Core Features

### Short Options

Add concise short flags to your CLI:

```python
from dataclass_config import cli_short

@dataclass
class ServerConfig:
    host: str = cli_short('h', default="localhost")
    port: int = cli_short('p', default=8000)
    debug: bool = cli_short('d', default=False)
```

```bash
# Use short forms
$ python server.py -h 0.0.0.0 -p 9000 -d

# Or long forms
$ python server.py --host 0.0.0.0 --port 9000 --debug

# Mix and match
$ python server.py -h 0.0.0.0 --port 9000 -d
```

### Boolean Flags

Booleans work as proper CLI flags with negative forms:

```python
@dataclass
class BuildConfig:
    test: bool = True      # Default enabled
    deploy: bool = False   # Default disabled
```

```bash
# Enable a flag
$ python build.py --deploy

# Disable a flag
$ python build.py --no-test

# Use defaults (omit flags)
$ python build.py  # test=True, deploy=False
```

With short options:

```python
@dataclass
class Config:
    verbose: bool = cli_short('v', default=False)
    debug: bool = cli_short('d', default=False)
```

```bash
$ python app.py -v -d              # Short flags
$ python app.py --verbose --debug  # Long flags
$ python app.py --no-verbose       # Negative form
```

### Value Choices

Restrict field values to a valid set:

```python
from dataclass_config import cli_choices

@dataclass
class DeployConfig:
    environment: str = cli_choices(['dev', 'staging', 'prod'])
    region: str = cli_choices(['us-east-1', 'us-west-2', 'eu-west-1'], default='us-east-1')
    size: str = cli_choices(['small', 'medium', 'large'], default='medium')
```

```bash
# Valid choices
$ python deploy.py --environment prod --region us-west-2

# Invalid choice shows error
$ python deploy.py --environment invalid
error: argument --environment: invalid choice: 'invalid' (choose from 'dev', 'staging', 'prod')
```



### Positional Arguments

Add positional arguments that don't require `--` prefixes:

```python
from dataclass_config import cli_positional

@dataclass
class CopyCommand:
    source: str = cli_positional(help="Source file")
    dest: str = cli_positional(help="Destination file")
    recursive: bool = cli_short('r', default=False)
```

```bash
# Positional arguments are matched by position
$ python cp.py source.txt destination.txt -r

# Optional flags can appear anywhere
$ python cp.py -r source.txt destination.txt
```

#### Variable Number of Arguments

Use `nargs` to accept multiple values:

```python
from typing import List

@dataclass
class GitCommit:
    command: str = cli_positional(help="Git command")
    files: List[str] = cli_positional(nargs='+', help="Files to commit")
    message: str = cli_short('m', default="")

# CLI: python git.py commit file1.py file2.py file3.py -m "Add feature"
```

**nargs Options:**
- `None` (default) - Exactly one value (required)
- `'?'` - Zero or one value (optional)
- `'*'` - Zero or more values (optional list)
- `'+'` - One or more values (required list)
- `int` (e.g., `2`) - Exact count (required list)

#### Optional Positional Arguments

```python
@dataclass
class Convert:
    input_file: str = cli_positional(help="Input file")
    output_file: str = cli_positional(
        nargs='?',
        default='stdout',
        help="Output file (default: stdout)"
    )
    format: str = cli_short('f', default='json')
```

```bash
# With output file
$ python convert.py input.json output.yaml -f yaml

# Without output file (uses default)
$ python convert.py input.json -f xml
```

#### ⚠️ Positional List Constraints

Positional arguments with variable length have important constraints:

**Rules:**
1. At most ONE positional field can use `nargs='*'` or `'+'`
2. If present, the positional list must be the LAST positional argument
3. For multiple lists, use optional arguments with flags

**Valid:**
```python
@dataclass
class Valid:
    command: str = cli_positional()          # First
    files: List[str] = cli_positional(nargs='+')  # Last (OK!)
    exclude: List[str] = cli_short('e', default_factory=list)  # Optional list with flag (OK!)
```

**Invalid:**
```python
@dataclass
class Invalid:
    files: List[str] = cli_positional(nargs='+')  # Positional list
    output: str = cli_positional()                 # ERROR: positional after list!

# ConfigBuilderError: Positional list argument must be last.
# Fix: Make output an optional argument with a flag
```

**Why?** Positional lists are greedy and consume all remaining values. The parser can't determine where one positional list ends and another begins without `--` flags.

### Combining Annotations

Use `combine_annotations()` to merge multiple features:

```python
from dataclass_config import combine_annotations, cli_short, cli_choices, cli_help

@dataclass
class AppConfig:
    # Combine short option + help text
    name: str = combine_annotations(
        cli_short('n'),
        cli_help("Application name")
    )

    # Combine short + choices + help
    environment: str = combine_annotations(
        cli_short('e'),
        cli_choices(['dev', 'staging', 'prod']),
        cli_help("Deployment environment"),
        default='dev'
    )

    # Boolean with short + help
    debug: bool = combine_annotations(
        cli_short('d'),
        cli_help("Enable debug mode"),
        default=False
    )
```

```bash
# Concise CLI usage
$ python app.py -n myapp -e prod -d

# Clear help output
$ python app.py --help
options:
  -n NAME, --name NAME  Application name
  -e {dev,staging,prod}, --environment {dev,staging,prod}
                        Deployment environment (default: dev)
  -d, --debug           Enable debug mode (default: False)
  --no-debug            Disable Enable debug mode
```

### Real-World Example

```python
from dataclasses import dataclass
from dataclass_config import build_config, cli_short, cli_choices, cli_help, combine_annotations

@dataclass
class DeploymentConfig:
    """Configuration for application deployment."""

    # Basic settings with short options
    name: str = combine_annotations(
        cli_short('n'),
        cli_help("Application name")
    )

    version: str = combine_annotations(
        cli_short('v'),
        cli_help("Version to deploy"),
        default='latest'
    )

    # Validated choices
    environment: str = combine_annotations(
        cli_short('e'),
        cli_choices(['dev', 'staging', 'prod']),
        cli_help("Target environment"),
        default='dev'
    )

    region: str = combine_annotations(
        cli_short('r'),
        cli_choices(['us-east-1', 'us-west-2', 'eu-west-1']),
        cli_help("AWS region"),
        default='us-east-1'
    )

    size: str = combine_annotations(
        cli_short('s'),
        cli_choices(['small', 'medium', 'large', 'xlarge']),
        cli_help("Instance size"),
        default='medium'
    )

    # Boolean flags
    dry_run: bool = combine_annotations(
        cli_short('d'),
        cli_help("Perform dry run without deploying"),
        default=False
    )

    notify: bool = combine_annotations(
        cli_short('N'),
        cli_help("Send deployment notifications"),
        default=True
    )

if __name__ == "__main__":
    config = build_config(DeploymentConfig)

    print(f"Deploying {config.name} v{config.version}")
    print(f"Environment: {config.environment}")
    print(f"Region: {config.region}")
    print(f"Size: {config.size}")
    print(f"Dry run: {config.dry_run}")
    print(f"Notify: {config.notify}")
```

```bash
# Production deployment
$ python deploy.py -n myapp -v 2.1.0 -e prod -r us-west-2 -s large

# Dry run in staging
$ python deploy.py -n myapp -e staging -d --no-notify

# Help shows everything clearly
$ python deploy.py --help
```

## Advanced Features

### File-Loadable Parameters

Load string parameters from files using the `@filename` syntax:

```python
from dataclass_config import cli_file_loadable

@dataclass
class AppConfig:
    name: str = cli_help("Application name")
    system_prompt: str = cli_file_loadable(default="You are a helpful assistant")
    welcome_message: str = cli_file_loadable()

config = build_config(AppConfig)
```

```bash
# Use literal values
$ python app.py --system-prompt "You are a coding assistant"

# Load from files
$ python app.py --system-prompt "@prompts/coding_assistant.txt" --welcome-message "@messages/welcome.txt"

# Mix literal and file-loaded values
$ python app.py --name "MyApp" --system-prompt "@prompts/assistant.txt"
```

### Configuration File Merging

Combine base configuration files with CLI overrides:

```yaml
# config.yaml
name: "DefaultApp"
count: 100
database:
  host: "localhost"
  port: 5432
  timeout: 30
```

```python
@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    timeout: float = 30.0

@dataclass
class AppConfig:
    name: str
    count: int = 10
    database: Dict[str, Any] = None

config = build_config_from_cli(AppConfig, [
    '--config', 'config.yaml',  # Load base configuration
    '--name', 'OverriddenApp',  # Override name
    '--database', 'db.json',    # Load additional database config
    '--d', 'timeout:60'         # Override database.timeout property
])
```

### Custom Help and Annotations

```python
from dataclass_config import cli_help, cli_exclude, cli_file_loadable

@dataclass
class ServerConfig:
    # Custom help text
    host: str = cli_help("Server bind address", default="127.0.0.1")
    port: int = cli_help("Server port number", default=8000)

    # File-loadable with help
    ssl_cert: str = cli_file_loadable(cli_help("SSL certificate content"))

    # Hidden from CLI
    secret_key: str = cli_exclude(default="auto-generated")

    # Multiple values
    allowed_hosts: List[str] = cli_help("Allowed host headers", default_factory=list)
```

### Complex Types and Validation

```python
from typing import List, Dict, Optional
from pathlib import Path

@dataclass
class MLConfig:
    # Basic types
    model_name: str = cli_help("Model identifier")
    learning_rate: float = cli_help("Learning rate", default=0.001)
    epochs: int = cli_help("Training epochs", default=100)

    # Complex types
    layer_sizes: List[int] = cli_help("Neural network layer sizes", default_factory=lambda: [128, 64])
    hyperparameters: Dict[str, Any] = cli_help("Model hyperparameters")

    # Optional types
    checkpoint_path: Optional[Path] = cli_help("Path to model checkpoint")

    # File-loadable configurations
    training_config: str = cli_file_loadable(cli_help("Training configuration"))

    def __post_init__(self):
        # Custom validation
        if self.learning_rate <= 0:
            raise ValueError("Learning rate must be positive")
        if self.epochs <= 0:
            raise ValueError("Epochs must be positive")
```

## API Reference

> **📖 Full API Documentation:** See [docs/API.md](docs/API.md) for complete API reference with detailed examples.

### Quick API Reference

### Main Functions

#### `build_config(config_class, args=None)`

Generate CLI from dataclass and parse arguments.

```python
config = build_config(MyDataclass)  # Uses sys.argv automatically
```

#### `build_config_from_cli(config_class, args=None, **options)`

Generate CLI with additional options.

```python
config = build_config_from_cli(
    MyDataclass,
    args=['--name', 'test'],
    exclude_fields={'internal_field'},
    use_annotations=True
)
```

### Annotations

#### `cli_short(letter, **kwargs)`

Add a short option flag to a field.

```python
field: str = cli_short('f', default="value")

# Or combine with other annotations
field: str = combine_annotations(
    cli_short('f'),
    cli_help("Help text"),
    default="value"
)
```

#### `cli_choices(choices_list, **kwargs)`

Restrict field to a set of valid choices.

```python
env: str = cli_choices(['dev', 'prod'], default='dev')

# Or combine
env: str = combine_annotations(
    cli_short('e'),
    cli_choices(['dev', 'prod']),
    cli_help("Environment"),
    default='dev'
)
```

#### `cli_help(help_text, **kwargs)`

Add custom help text to CLI arguments.

```python
field: str = cli_help("Custom help text", default="default_value")
```



#### `cli_positional(nargs=None, metavar=None, **kwargs)`

Mark a field as a positional CLI argument (no `--` prefix required).

```python
# Required positional
source: str = cli_positional(help="Source file")

# Optional positional
output: str = cli_positional(nargs='?', default='stdout')

# Variable number (list)
files: List[str] = cli_positional(nargs='+', help="Files")

# Exact count
coords: List[float] = cli_positional(nargs=2, metavar='X Y')

# Combined with other annotations
input: str = combine_annotations(
    cli_positional(),
    cli_help("Input file path")
)
```

**Important:** At most one positional can use `nargs='*'` or `'+'`, and it must be the last positional.

#### `cli_exclude(**kwargs)`

Exclude fields from CLI argument generation.

```python
internal_field: str = cli_exclude(default="hidden")
```

#### `cli_file_loadable(**kwargs)`

Mark string fields as file-loadable via '@filename' syntax.

```python
content: str = cli_file_loadable(default="default content")
```

#### `combine_annotations(*annotations, **kwargs)`

Combine multiple annotations on a single field.

```python
field: str = combine_annotations(
    cli_short('f'),
    cli_choices(['a', 'b', 'c']),
    cli_help("Description"),
    default='a'
)
```

## Type Support

Dataclass CLI supports standard Python types:

| Type | CLI Behavior | Example |
|------|--------------|---------|
| `str` | Direct string value | `--name "hello"` |
| `int` | Parsed as integer | `--count 42` |
| `float` | Parsed as float | `--rate 0.1` |
| `bool` | Flag with negative | `--debug` or `--no-debug` |
| `List[T]` | Multiple values | `--items a b c` |
| `Dict[str, Any]` | Config file + overrides | `--config file.json --c key:value` |
| `Optional[T]` | Optional parameter | `--timeout 30` (or omit) |
| `Path` | Path object | `--output /path/to/file` |
| Custom types | String representation | `--custom "value"` |

## Configuration File Formats

Supports multiple configuration file formats:

### JSON
```json
{
  "name": "MyApp",
  "count": 42,
  "database": {
    "host": "localhost",
    "port": 5432
  }
}
```

### YAML (requires `pip install "dataclass-config[yaml]"`)
```yaml
name: MyApp
count: 42
database:
  host: localhost
  port: 5432
```

### TOML (requires `pip install "dataclass-config[toml]"`)
```toml
name = "MyApp"
count = 42

[database]
host = "localhost"
port = 5432
```

## Examples

Check the [`examples/`](examples/) directory for complete working examples:

- **`positional_example.py`** - Positional arguments and variable length args
- **`boolean_flags_example.py`** - Boolean flags with `--flag` and `--no-flag`
- **`cli_choices_example.py`** - Value validation with choices
- **`cli_short_example.py`** - Short option flags
- **`all_features_example.py`** - All features together
- And more...

### Web Server Configuration

```python
from dataclasses import dataclass
from typing import List
from dataclass_config import build_config, cli_short, cli_help, cli_exclude, cli_file_loadable, combine_annotations

@dataclass
class ServerConfig:
    # Basic server settings
    host: str = combine_annotations(
        cli_short('h'),
        cli_help("Server bind address"),
        default="127.0.0.1"
    )

    port: int = combine_annotations(
        cli_short('p'),
        cli_help("Server port number"),
        default=8000
    )

    workers: int = combine_annotations(
        cli_short('w'),
        cli_help("Number of worker processes"),
        default=1
    )

    # Security settings
    ssl_cert: str = cli_file_loadable(cli_help("SSL certificate content"))
    ssl_key: str = cli_file_loadable(cli_help("SSL private key content"))

    # Application settings
    debug: bool = combine_annotations(
        cli_short('d'),
        cli_help("Enable debug mode"),
        default=False
    )

    allowed_hosts: List[str] = cli_help("Allowed host headers", default_factory=list)

    # Internal fields (hidden from CLI)
    _server_id: str = cli_exclude(default_factory=lambda: f"server-{os.getpid()}")

if __name__ == "__main__":
    config = build_config(ServerConfig)
    print(f"Starting server on {config.host}:{config.port}")
```

```bash
# Start server with short options
$ python server.py -h 0.0.0.0 -p 9000 -w 4 -d

# Load SSL certificates from files
$ python server.py --ssl-cert "@certs/server.crt" --ssl-key "@certs/server.key"
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/bassmanitram/dataclass-config.git
cd dataclass-config
pip install -e ".[dev,all]"
```

### Development Setup

```bash
git clone https://github.com/bassmanitram/dataclass-config.git
cd dataclass-config
pip install -e ".[dev,all]"
make setup  # Install dev dependencies and pre-commit hooks
```

### Running Tests

```bash
# Run all tests (coverage is automatic)
pytest
make test

# Run tests with detailed coverage report
make coverage

# Run tests with coverage and open HTML report
make coverage-html

# Run specific test file
pytest tests/test_cli_short.py

# Verbose output
pytest -v
```

### Code Coverage

This project maintains **94%+ code coverage**. Coverage reports are generated automatically when running tests.

- **Quick check**: `make coverage`
- **Detailed report**: See `htmlcov/index.html`
- **Coverage docs**: [COVERAGE.md](COVERAGE.md)

All code changes should maintain or improve coverage. The minimum required coverage is 90%.

### Code Formatting

```bash
# Format code
make format
black dataclass_config/ tests/ examples/
isort dataclass_config/ tests/ examples/

# Check formatting
make lint
black --check dataclass_config/ tests/
flake8 dataclass_config/ tests/
mypy dataclass_config/
```

### Full Check (like CI)

```bash
# Run all checks: linting, tests, and examples
make check
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Support

- **Issues**: [GitHub Issues](https://github.com/bassmanitram/dataclass-config/issues)
- **Documentation**: This README and comprehensive docstrings
- **Examples**: See the [examples/](examples/) directory

## Quick Reference

```python
from dataclasses import dataclass
from dataclass_config import (
    build_config,                # Main function
    cli_short,                   # Short options: -n
    cli_positional,              # Positional args
    cli_choices,                 # Value validation
    cli_help,                    # Custom help text
    cli_exclude,                 # Hide from CLI
    cli_file_loadable,           # @file loading
    combine_annotations,         # Combine features
)

@dataclass
class Config:
    # Simple field
    name: str

    # Positional argument
    input_file: str = cli_positional()

    # With short option
    port: int = cli_short('p', default=8000)

    # With choices
    env: str = cli_choices(['dev', 'prod'], default='dev')

    # Boolean flag
    debug: bool = False  # Creates --debug and --no-debug

    # Combine everything
    region: str = combine_annotations(
        cli_short('r'),
        cli_choices(['us-east-1', 'us-west-2']),
        cli_help("AWS region"),
        default='us-east-1'
    )

    # Hidden from CLI
    secret: str = cli_exclude(default="hidden")

    # File-loadable
    config_text: str = cli_file_loadable(default="")

# Build and use
config = build_config(Config)
```

Define your dataclass, add annotations as needed, and call `build_config()` to parse command-line arguments.
