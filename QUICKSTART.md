# Quick Start Guide

Get started with dataclass-cli in 5 minutes.

## Installation

```bash
pip install dataclass-cli
```

## 1. Basic Usage

**Create a dataclass, call `build_config()`, done:**

```python
from dataclasses import dataclass
from dataclass_cli import build_config

@dataclass
class Config:
    name: str
    port: int = 8000

config = build_config(Config)
print(f"{config.name} on port {config.port}")
```

```bash
$ python app.py --name myapp --port 9000
myapp on port 9000
```

## 2. Add Short Options

**Use `cli_short()` for concise `-n` flags:**

```python
from dataclass_cli import cli_short

@dataclass
class Config:
    name: str = cli_short('n')
    port: int = cli_short('p', default=8000)

config = build_config(Config)
```

```bash
$ python app.py -n myapp -p 9000
```

## 3. Boolean Flags

**Booleans automatically get `--flag` and `--no-flag`:**

```python
@dataclass
class Config:
    name: str = cli_short('n')
    debug: bool = cli_short('d', default=False)
    optimize: bool = True  # Default enabled

config = build_config(Config)
```

```bash
$ python app.py -n myapp -d              # Enable debug
$ python app.py -n myapp --no-optimize   # Disable optimize
```

## 4. Validate Values

**Use `cli_choices()` to restrict values:**

```python
from dataclass_cli import cli_choices

@dataclass
class Config:
    name: str = cli_short('n')
    environment: str = cli_choices(['dev', 'staging', 'prod'], default='dev')

config = build_config(Config)
```

```bash
$ python app.py -n myapp --environment prod   # ✓ Valid
$ python app.py -n myapp --environment test   # ✗ Error: invalid choice
```

## 5. Combine Everything

**Use `combine_annotations()` to use multiple features together:**

```python
from dataclass_cli import combine_annotations, cli_short, cli_choices, cli_help

@dataclass
class Config:
    name: str = combine_annotations(
        cli_short('n'),
        cli_help("Application name")
    )

    environment: str = combine_annotations(
        cli_short('e'),
        cli_choices(['dev', 'staging', 'prod']),
        cli_help("Deployment environment"),
        default='dev'
    )

    debug: bool = combine_annotations(
        cli_short('d'),
        cli_help("Enable debug mode"),
        default=False
    )

config = build_config(Config)
```

```bash
# Concise and powerful
$ python app.py -n myapp -e prod -d

# Help is automatically generated
$ python app.py --help
options:
  -n NAME, --name NAME  Application name
  -e {dev,staging,prod}, --environment {dev,staging,prod}
                        Deployment environment (default: dev)
  -d, --debug           Enable debug mode (default: False)
  --no-debug            Disable Enable debug mode
```

## Complete Example

```python
from dataclasses import dataclass
from dataclass_cli import build_config, combine_annotations, cli_short, cli_choices, cli_help

@dataclass
class ServerConfig:
    """My server configuration."""

    # Required field
    name: str = combine_annotations(
        cli_short('n'),
        cli_help("Server name")
    )

    # Optional with default
    port: int = combine_annotations(
        cli_short('p'),
        cli_help("Port number"),
        default=8000
    )

    # Validated choice
    environment: str = combine_annotations(
        cli_short('e'),
        cli_choices(['dev', 'staging', 'prod']),
        cli_help("Environment"),
        default='dev'
    )

    # Boolean flags
    debug: bool = combine_annotations(
        cli_short('d'),
        cli_help("Enable debug logging"),
        default=False
    )

    reload: bool = combine_annotations(
        cli_short('r'),
        cli_help("Auto-reload on changes"),
        default=True
    )

if __name__ == "__main__":
    config = build_config(ServerConfig)

    print(f"Starting {config.name}")
    print(f"  Environment: {config.environment}")
    print(f"  Port: {config.port}")
    print(f"  Debug: {config.debug}")
    print(f"  Auto-reload: {config.reload}")
```

**Usage examples:**

```bash
# Production server
$ python server.py -n prod-server -e prod -p 443 --no-reload

# Development with debug
$ python server.py -n dev-server -d -r

# Staging environment
$ python server.py -n staging-1 -e staging -p 8080

# See all options
$ python server.py --help
```

## Next Steps

- Read the full [README.md](README.md) for advanced features
- Check out [examples/](examples/) for more complete examples
- Learn about file-loadable parameters for loading content from files
- Explore configuration file merging for complex setups

## Common Patterns

### Deploy Script

```python
@dataclass
class DeployConfig:
    app: str = cli_short('a')
    version: str = cli_short('v', default='latest')
    environment: str = cli_short('e', choices=['dev', 'prod'], default='dev')
    dry_run: bool = cli_short('d', default=False)

config = build_config(DeployConfig)
```

```bash
$ python deploy.py -a myapp -v 2.1.0 -e prod
$ python deploy.py -a myapp -d  # Dry run
```

### Database Migration

```python
@dataclass
class MigrationConfig:
    database_url: str = cli_short('u')
    direction: str = cli_choices(['up', 'down'], default='up')
    steps: int = cli_short('s', default=1)
    force: bool = cli_short('f', default=False)

config = build_config(MigrationConfig)
```

```bash
$ python migrate.py -u postgres://localhost/db
$ python migrate.py -u postgres://localhost/db --direction down -s 3
$ python migrate.py -u postgres://localhost/db -f  # Force
```

### Build Pipeline

```python
@dataclass
class BuildConfig:
    project: str = cli_short('p')
    build: bool = cli_short('b', default=True)
    test: bool = cli_short('t', default=True)
    deploy: bool = cli_short('d', default=False)
    verbose: bool = cli_short('v', default=False)

config = build_config(BuildConfig)
```

```bash
$ python build.py -p myapp                      # Build and test
$ python build.py -p myapp --no-test            # Skip tests
$ python build.py -p myapp -d -v                # Deploy with verbose
```

That's it! You now know enough to build powerful CLIs with dataclass-cli. 🚀
