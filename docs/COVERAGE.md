# Code Coverage Report

## Overview

This project maintains **97.63%** code coverage with comprehensive testing and branch coverage enabled.

## Current Coverage Statistics (v1.9.0)

| Module | Statements | Missing | Branches | Partial | Coverage |
|--------|------------|---------|----------|---------|----------|
| `__init__.py` | 8 | 0 | 0 | 0 | **100.00%** |
| `annotations.py` | 166 | 0 | 46 | 0 | **100.00%** |
| `append_action.py` | 6 | 0 | 0 | 0 | **100.00%** |
| `argument_registry.py` | 201 | 1 | 78 | 5 | **97.85%** |
| `builder.py` | 33 | 0 | 4 | 0 | **100.00%** |
| `cli_overrides.py` | 74 | 2 | 30 | 1 | **97.12%** |
| `config_applicator.py` | 49 | 0 | 16 | 0 | **100.00%** |
| `config_merging.py` | 41 | 1 | 16 | 1 | **96.49%** |
| `config_resolver.py` | 33 | 0 | 0 | 0 | **100.00%** |
| `convenience.py` | 44 | 0 | 18 | 0 | **100.00%** |
| `exceptions.py` | 8 | 0 | 0 | 0 | **100.00%** |
| `field_analyzer.py` | 189 | 11 | 84 | 5 | **93.41%** |
| `file_loading.py` | 40 | 0 | 16 | 0 | **100.00%** |
| `formatter.py` | 9 | 0 | 4 | 0 | **100.00%** |
| `instantiate.py` | 185 | 0 | 72 | 0 | **100.00%** |
| `nested_processor.py` | 111 | 3 | 46 | 1 | **97.45%** |
| `type_inspector.py` | 73 | 3 | 32 | 3 | **94.29%** |
| `utils.py` | 63 | 0 | 22 | 0 | **100.00%** |
| `value_resolution.py` | 83 | 5 | 42 | 2 | **94.40%** |
| **TOTAL** | **1416** | **26** | **526** | **18** | **97.63%** |

## Test Suite

- **Total Tests:** 685
- **Test Execution Time:** ~3.5s
- **All Tests Passing:** ✅
- **Python Version:** 3.8+ (tested on 3.8–3.12)

## Coverage Requirements

- **Minimum Required:** 88%
- **Current Coverage:** 97.63% ✅
- **Modules at 100%:** 11 of 19

## Coverage History

| Version | Tests | Coverage | Change |
|---------|-------|----------|--------|
| v1.4.3 | 429 | 92.24% | baseline |
| v1.5.0 | 501 | 91.35% | +72 tests (new module) |
| v1.6.0 | 633 | 98.74% | +132 tests, gap coverage |
| v1.7.0 | 660 | 98.76% | +27 tests (build_config_from_dict) |
| v1.8.1 | 675 | 97.74% | +15 tests, major refactor |
| v1.9.0 | 685 | 97.63% | +10 tests (cli_override_name) |

## Architecture (v1.9.0)

```
dataclass_args/
├── builder.py              # Orchestrator: ties FieldAnalyzer + ArgumentRegistry + ConfigResolver
├── field_analyzer.py       # Phase 1: Field inspection, validation, collision detection
├── argument_registry.py    # Phase 2: argparse argument registration
├── config_resolver.py      # Phase 3: Pipeline orchestrator (delegates to stage modules)
│   ├── config_merging.py   # Stages 1-2: Normalize & merge base_configs + config files
│   ├── cli_overrides.py    # Stage 3: Apply CLI argument overrides
│   └── value_resolution.py # Stages 4-7: File resolution, validation, cli_resolve
├── convenience.py          # Public entry points (build_config, build_config_from_dict)
├── annotations.py          # Field metadata annotations (cli_short, cli_nested, etc.)
├── config_applicator.py    # Dict merge utilities
├── nested_processor.py     # Nested dataclass flattening/reconstruction
├── type_inspector.py       # Type system utilities
├── file_loading.py         # @file syntax processing
├── utils.py                # Structured file loading (JSON/YAML/TOML)
├── instantiate.py          # Object instantiation from config
├── formatter.py            # Help text formatting
├── append_action.py        # Custom argparse append action
└── exceptions.py           # Exception hierarchy
```

## Running Coverage Reports

### Quick Commands

```bash
# Run tests with coverage (automatic via pytest config)
pytest

# Run with HTML report
pytest --cov-report=html
open htmlcov/index.html

# Run specific module coverage
pytest --cov=dataclass_args.builder tests/

# Coverage summary only
pytest --cov=dataclass_args --cov-report=term-missing
```

## Test Organization

```
tests/
├── test_annotations.py             # Annotation functionality
├── test_basic.py                   # Basic configuration building
├── test_boolean_*.py               # Boolean flag handling
├── test_build_config_from_dict.py  # Programmatic dict-based config
├── test_builder_advanced.py        # Builder advanced paths
├── test_cli_append.py              # Append action
├── test_cli_choices.py             # Choice validation
├── test_cli_nested.py              # Nested dataclasses
├── test_cli_override_name.py       # Custom dict override names
├── test_cli_resolve.py             # Post-load field resolution
├── test_cli_short.py               # Short options
├── test_collisions.py              # Collision detection
├── test_config_applicator.py       # Config application
├── test_config_merging_*.py        # Config merging
├── test_description.py             # Help text customization
├── test_file_loading.py            # File loading (@file)
├── test_instantiate.py             # Object instantiation
├── test_nested_help_text.py        # Nested help text
├── test_pep604_union.py            # PEP 604 union type support
├── test_positional.py              # Positional arguments
├── test_type_inspector.py          # Type inspection
└── test_utils.py                   # File format loading
```

## Quality Metrics

- **Test Execution:** Fast (~3.5s for 685 tests)
- **Test Reliability:** 100% (no flaky tests)
- **Cognitive Complexity:** All functions CC≤10
- **Test Clarity:** High (class-based organization, one class per concern)
- **Edge Case Coverage:** Comprehensive
- **Integration Tests:** Included
- **Mocking:** Minimal (only for truly untestable paths)

## Continuous Integration

All tests run automatically on:
- Every push
- Every pull request
- Multiple Python versions (3.8, 3.9, 3.10, 3.11, 3.12)
- Multiple platforms (Linux, macOS, Windows)

---

**Last Updated:** 2026-09-06
**Version:** 1.9.0
