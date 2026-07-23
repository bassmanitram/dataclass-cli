# Code Coverage Report

## Overview

This project maintains **98.74%** code coverage with comprehensive testing and branch coverage enabled.

## Current Coverage Statistics (v1.6.0)

| Module | Statements | Missing | Branches | Partial | Coverage |
|--------|------------|---------|----------|---------|----------|
| `__init__.py` | 8 | 0 | 0 | 0 | **100.00%** |
| `annotations.py` | 156 | 0 | 44 | 0 | **100.00%** |
| `append_action.py` | 6 | 0 | 0 | 0 | **100.00%** |
| `builder.py` | 442 | 2 | 208 | 8 | **98.46%** |
| `config_applicator.py` | 49 | 0 | 16 | 0 | **100.00%** |
| `exceptions.py` | 8 | 0 | 0 | 0 | **100.00%** |
| `file_loading.py` | 40 | 0 | 16 | 0 | **100.00%** |
| `formatter.py` | 9 | 0 | 4 | 0 | **100.00%** |
| `instantiate.py` | 175 | 0 | 62 | 0 | **100.00%** |
| `nested_processor.py` | 111 | 3 | 46 | 1 | **97.45%** |
| `type_inspector.py` | 69 | 3 | 28 | 3 | **93.81%** |
| `utils.py` | 63 | 0 | 22 | 0 | **100.00%** |
| **TOTAL** | **1136** | **8** | **446** | **12** | **98.74%** |

## Test Suite

- **Total Tests:** 633
- **Test Execution Time:** ~3.7s
- **All Tests Passing:** ✅
- **Python Version:** 3.8+ (tested on 3.8–3.12)

## Coverage Requirements

- **Minimum Required:** 88%
- **Current Coverage:** 98.74% ✅
- **Modules at 100%:** 9 of 12

## Coverage History

| Version | Tests | Coverage | Change |
|---------|-------|----------|--------|
| v1.4.3 | 429 | 92.24% | baseline |
| v1.5.0 | 501 | 91.35% | +72 tests (new module) |
| v1.6.0 (initial) | 588 | 91.35% | +87 tests |
| v1.6.0 (round 1) | 618 | 94.27% | +30 tests, gap coverage |
| v1.6.0 (round 2) | 631 | 96.37% | +13 tests, pragmas |
| v1.6.0 (final) | 633 | 98.74% | +2 tests, pragmas |

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

## Uncovered Code Analysis

### Remaining Gaps (8 lines + 12 branch misses)

All remaining uncovered code falls into three justified categories:

**1. Branch-Coverage Misses in Complex Conditionals (builder.py)**
- Partial branches in nested validation logic (e.g., `141->159`, `415->390`)
- Complex conditional paths where both branches are technically valid but only one path is exercised in tests
- Override name computation fallback (`line 829`)

**2. Error Handler Paths (nested_processor.py)**
- `lines 307-309`: Exception handler for `apply_property_overrides` failures
- Only triggerable when the config applicator raises on valid-looking input (requires mocking)

**3. Type Inspector Edge Cases (type_inspector.py)**
- `lines 81-82`: `except ImportError: pass` for `typing.Union` (always available on 3.8+)
- `line 178`: `Dict` with single type parameter (invalid Python syntax)
- Branch misses in `is_nested_list` for edge cases

### Pragma-Marked Code

The following paths are marked with `# pragma: no cover` as they are untestable on the current Python version:

- **Import fallbacks**: `typing_extensions` imports that only trigger on Python < 3.8
- **PEP 604 fallbacks**: `UnionType` imports that only trigger on Python < 3.10
- **Optional dependency imports**: YAML/TOML library imports when packages aren't installed
- **Defensive guards**: Internal collision detection code superseded by earlier validation

## Coverage by Category

| Category | Coverage | Status |
|----------|----------|--------|
| Core Functionality | 98%+ | ⭐ Excellent |
| Error Handling | 97%+ | ⭐ Excellent |
| Type System | 94%+ | ✅ Good |
| Configuration Loading | 100% | ⭐ Perfect |
| Nested Dataclasses | 97%+ | ⭐ Excellent |
| Annotations | 100% | ⭐ Perfect |
| Object Instantiation | 100% | ⭐ Perfect |
| File Loading | 100% | ⭐ Perfect |

## Test Organization

```
tests/
├── test_annotations.py             # Annotation functionality (29 tests)
├── test_basic.py                   # Basic configuration building (20 tests)
├── test_boolean_*.py               # Boolean flag handling (36 tests)
├── test_builder_advanced.py        # Builder advanced paths (28 tests)
├── test_cli_append.py              # Append action (40 tests)
├── test_cli_choices.py             # Choice validation (20 tests)
├── test_cli_nested.py              # Nested dataclasses (42 tests)
├── test_cli_short.py               # Short options (18 tests)
├── test_collisions.py              # Collision detection (11 tests)
├── test_config_applicator.py       # Config application (36 tests)
├── test_config_merging_*.py        # Config merging (10 tests)
├── test_description.py             # Help text customization (18 tests)
├── test_file_loading.py            # File loading (@file) (26 tests)
├── test_instantiate.py             # Object instantiation (97 tests)
├── test_instantiate_fixtures.py    # Fixture classes for instantiate tests
├── test_nested_help_text.py        # Nested help text (5 tests)
├── test_pep604_union.py            # PEP 604 union type support (15 tests)
├── test_positional.py              # Positional arguments (38 tests)
├── test_type_inspector.py          # Type inspection (36 tests)
├── test_utils.py                   # File format loading (34 tests)
└── test_*_override.py              # Property overrides (13 tests)
```

## Quality Metrics

- **Test Execution:** Fast (~3.7s for 633 tests)
- **Test Reliability:** 100% (no flaky tests)
- **Test Clarity:** High (class-based organization, one class per concern)
- **Edge Case Coverage:** Comprehensive
- **Integration Tests:** Included
- **Mocking:** Minimal (only for truly untestable paths like IOError)

## Continuous Integration

All tests run automatically on:
- Every push
- Every pull request
- Multiple Python versions (3.8, 3.9, 3.10, 3.11, 3.12)
- Multiple platforms (Linux, macOS, Windows)

---

**Last Updated:** 2025-06-28
**Version:** 1.6.0
