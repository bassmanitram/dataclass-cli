# Dataclass CLI

Generate command-line interfaces from Python dataclasses.

[![Tests](https://github.com/bassmanitram/dataclass-cli/actions/workflows/test.yml/badge.svg)](https://github.com/bassmanitram/dataclass-cli/actions/workflows/test.yml)
[![Code Quality](https://github.com/bassmanitram/dataclass-cli/actions/workflows/lint.yml/badge.svg)](https://github.com/bassmanitram/dataclass-cli/actions/workflows/lint.yml)
[![Examples](https://github.com/bassmanitram/dataclass-cli/actions/workflows/examples.yml/badge.svg)](https://github.com/bassmanitram/dataclass-cli/actions/workflows/examples.yml)
[![codecov](https://codecov.io/gh/bassmanitram/dataclass-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/bassmanitram/dataclass-cli)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/dataclass-cli.svg)](https://badge.fury.io/py/dataclass-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Generate CLI automatically from dataclass definitions
- Type-safe argument parsing for standard Python types
- Load string parameters from files using `@filename` syntax
- Merge configuration files with CLI overrides
- Support for `List`, `Dict`, `Optional`, and custom types
- Automatic help text generation with custom annotations
- Custom field filters and processors
- Minimal dependencies and overhead

## Quick Start

### Installation

```bash
pip install dataclass-cli

# With optional format support
pip install "dataclass-cli[yaml,toml]"  # YAML and TOML config files
pip install "dataclass-cli[all]"        # All optional dependencies
```

### Basic Usage

```python
from dataclasses import dataclass
from dataclass_cli import build_config

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
$ python app.py --name "MyApp" --count 5 --debug true
Running MyApp with count=5, debug=True

$ python app.py --help
usage: app.py [-h] [--config CONFIG] [--name NAME] [--count COUNT] [--debug DEBUG]

Build Config from CLI

optional arguments:
  -h, --help       show this help message and exit
  --config CONFIG  Base configuration file (JSON, YAML, or TOML)
  --name NAME      name
  --count COUNT    count
  --debug DEBUG    debug
```

## Advanced Features

### File-Loadable Parameters

Load string parameters from files using the `@filename` syntax:

```python
from dataclass_cli import cli_file_loadable, cli_help

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
from dataclass_cli import cli_help, cli_exclude, cli_file_loadable

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

#### `cli_help(help_text, **kwargs)`

Add custom help text to CLI arguments.

```python
field: str = cli_help("Custom help text", default="default_value")
```

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

#### `cli_include(**kwargs)`

Explicitly mark fields for CLI inclusion.

```python
field: str = cli_include(default="included")
```

### Advanced Usage

#### Custom Field Filters

```python
from dataclass_cli import GenericConfigBuilder, exclude_internal_fields

def my_filter(field_name: str, field_info: dict) -> bool:
    """Custom filter to exclude sensitive fields."""
    sensitive_terms = ['password', 'secret', 'token']
    return not any(term in field_name.lower() for term in sensitive_terms)

builder = GenericConfigBuilder(MyConfig, field_filter=my_filter)
parser = argparse.ArgumentParser()
builder.add_arguments(parser)
```

#### Property Overrides for Dictionaries

```python
@dataclass
class Config:
    database_config: Dict[str, Any] = None
    model_params: Dict[str, Any] = None

# CLI usage with property overrides
config = build_config_from_cli(Config, [
    '--database-config', 'db.json',        # Load base config
    '--d', 'host:remote-server',           # Override database_config.host
    '--d', 'port:5433',                    # Override database_config.port
    '--model-params', 'model.json',        # Load base params
    '--m', 'learning_rate:0.001',          # Override model_params.learning_rate
    '--m', 'batch_size:32'                 # Override model_params.batch_size
])
```

#### Include/Exclude Fields

```python
# Only include specific fields
config = build_config_from_cli(
    MyConfig,
    include_fields={'host', 'port', 'debug'}
)

# Exclude specific fields
config = build_config_from_cli(
    MyConfig,
    exclude_fields={'internal_state', 'cache'}
)
```

## Type Support

Dataclass CLI supports standard Python types:

| Type | CLI Behavior | Example |
|------|--------------|---------|
| `str` | Direct string value | `--name "hello"` |
| `int` | Parsed as integer | `--count 42` |
| `float` | Parsed as float | `--rate 0.1` |
| `bool` | Parsed as boolean | `--debug true` |
| `List[T]` | Multiple values | `--items a --items b` |
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

### YAML (requires `pip install "dataclass-cli[yaml]"`)
```yaml
name: MyApp
count: 42
database:
  host: localhost
  port: 5432
```

### TOML (requires `pip install "dataclass-cli[toml]"`)
```toml
name = "MyApp"
count = 42

[database]
host = "localhost"
port = 5432
```

## Examples

### Web Server Configuration

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from dataclass_cli import build_config, cli_help, cli_exclude, cli_file_loadable

@dataclass
class ServerConfig:
    # Basic server settings
    host: str = cli_help("Server bind address", default="127.0.0.1")
    port: int = cli_help("Server port number", default=8000)
    workers: int = cli_help("Number of worker processes", default=1)

    # Security settings
    ssl_cert: str = cli_file_loadable(cli_help("SSL certificate content"))
    ssl_key: str = cli_file_loadable(cli_help("SSL private key content"))

    # Application settings
    debug: bool = cli_help("Enable debug mode", default=False)
    allowed_hosts: List[str] = cli_help("Allowed host headers", default_factory=list)

    # Advanced configuration
    middleware_config: Dict[str, Any] = cli_help("Middleware configuration")

    # Internal fields (hidden from CLI)
    _server_id: str = cli_exclude(default_factory=lambda: f"server-{os.getpid()}")

if __name__ == "__main__":
    config = build_config(ServerConfig)
    print(f"Starting server on {config.host}:{config.port}")
```

### Machine Learning Configuration

```python
@dataclass
class MLTrainingConfig:
    # Model configuration
    model_type: str = cli_help("Model architecture type")
    model_config: Dict[str, Any] = cli_help("Model hyperparameters")

    # Training parameters
    learning_rate: float = cli_help("Learning rate", default=0.001)
    batch_size: int = cli_help("Batch size", default=32)
    epochs: int = cli_help("Training epochs", default=100)

    # Data configuration
    train_data: str = cli_help("Training data path")
    val_data: Optional[str] = cli_help("Validation data path")

    # Training prompts/configs (file-loadable)
    system_prompt: str = cli_file_loadable(cli_help("System prompt for the model"))
    training_instructions: str = cli_file_loadable(cli_help("Training instructions"))

    # Output configuration
    output_dir: str = cli_help("Output directory", default="./outputs")
    save_checkpoints: bool = cli_help("Save model checkpoints", default=True)

# Usage:
# python train.py --model-type transformer --learning-rate 0.0001 \
#   --system-prompt "@prompts/expert_coder.txt" \
#   --model-config model_params.json --mc dropout:0.1 --mc attention_heads:8
```

### Database Migration Tool

```python
@dataclass
class MigrationConfig:
    # Database connection
    database_url: str = cli_help("Database connection URL")

    # Migration settings
    migration_dir: str = cli_help("Directory containing migration files", default="migrations")
    target_version: Optional[str] = cli_help("Target migration version")

    # SQL customization (file-loadable)
    pre_migration_sql: str = cli_file_loadable(cli_help("Pre-migration SQL commands"), default="")
    post_migration_sql: str = cli_file_loadable(cli_help("Post-migration SQL commands"), default="")

    # Execution options
    dry_run: bool = cli_help("Show what would be done without executing", default=False)
    force: bool = cli_help("Force migration even if dangerous", default=False)
    batch_size: int = cli_help("Number of migrations to run in one batch", default=1)

# Usage:
# python migrate.py --database-url postgresql://user:pass@localhost/db \
#   --target-version 2024_01_15_001 \
#   --pre-migration-sql "@sql/backup_tables.sql" \
#   --dry-run true
```

## Contributing

Contributions are welcome. Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/bassmanitram/dataclass-cli.git
cd dataclass-cli
pip install -e ".[dev,all]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black dataclass_cli/
isort dataclass_cli/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Support

- **Issues**: [GitHub Issues](https://github.com/bassmanitram/dataclass-cli/issues)
- **Documentation**: This README and comprehensive docstrings
- **Examples**: See the [examples/](examples/) directory
