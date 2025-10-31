# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-10-30

### Added
- Initial release of dataclass-cli
- Zero-boilerplate CLI generation from Python dataclasses
- Type-safe argument parsing for all standard Python types
- File-loadable string parameters using `@filename` syntax
- Configuration file merging with CLI overrides (JSON, YAML, TOML)
- Hierarchical property overrides for dictionary fields
- Custom field annotations:
  - `cli_help()` for custom help text
  - `cli_exclude()` to hide fields from CLI
  - `cli_file_loadable()` for file loading support
  - `cli_include()` for explicit inclusion
- Advanced type support: `List`, `Dict`, `Optional`, custom types
- Comprehensive validation and error handling
- Automatic help text generation
- Field filtering capabilities
- Custom field processors
- Complete test suite with 95%+ coverage
- Comprehensive documentation and examples

### Features
- **Main API**: `build_config()` and `build_config_from_cli()`
- **Advanced Builder**: `GenericConfigBuilder` for full control
- **File Formats**: JSON, YAML (optional), TOML (optional)
- **Type Support**: All Python standard types plus custom types
- **Error Handling**: Clear error messages and validation
- **Extensibility**: Custom filters, validators, and processors

### Requirements
- Python 3.8+
- No required dependencies (optional: PyYAML, tomli/tomllib)

[Unreleased]: https://github.com/bassmanitram/dataclass-cli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/bassmanitram/dataclass-cli/releases/tag/v0.1.0