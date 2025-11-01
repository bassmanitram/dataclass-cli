# Code Coverage Report

## Overview

This project maintains **94.35%** code coverage with comprehensive testing.

## Current Coverage Statistics

| Module | Statements | Missing | Branches | Partial | Coverage |
|--------|------------|---------|----------|---------|----------|
| `__init__.py` | 7 | 0 | 0 | 0 | **100.00%** |
| `annotations.py` | 113 | 10 | 36 | 6 | **87.92%** |
| `builder.py` | 243 | 4 | 100 | 3 | **97.96%** |
| `exceptions.py` | 6 | 0 | 0 | 0 | **100.00%** |
| `file_loading.py` | 40 | 6 | 16 | 1 | **87.50%** |
| `utils.py` | 72 | 5 | 22 | 0 | **94.68%** |
| **TOTAL** | **481** | **25** | **174** | **10** | **94.35%** |

## Coverage Requirements

- **Minimum Required:** 90%
- **Current Coverage:** 94.35% ✅
- **Target Coverage:** 95%+

## Running Coverage Reports

### Quick Commands

```bash
# Run tests with coverage (automatic via pytest config)
pytest

# Run tests with detailed coverage report
make coverage

# Run tests with coverage and open HTML report in browser
make coverage-html

# Or use the script directly
./scripts/coverage_report.sh
./scripts/coverage_report.sh --open
```

### Manual Coverage Run

```bash
# Generate all report formats
pytest tests/ \
    --cov=dataclass_config \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml
```

## Report Formats

### Terminal Report
- Shown automatically after running tests
- Displays missing lines and branches
- Color-coded output

### HTML Report
- Location: `htmlcov/index.html`
- Interactive browsing of coverage
- Line-by-line coverage visualization
- Branch coverage details

### XML Report
- Location: `coverage.xml`
- Used by CI/CD systems
- Machine-readable format

## Uncovered Code Analysis

### annotations.py (87.92%)

**Missing Lines:**
- Lines 274-278: `is_cli_included()` - Edge case for explicit CLI inclusion
- Line 311: `get_cli_short()` - Metadata access fallback
- Line 327: `get_cli_choices()` - Metadata access fallback
- Line 373: `get_cli_positional_nargs()` - Metadata access fallback
- Line 490: `is_optional_field()` - Edge case for optional detection
- Line 506: `is_allow_none()` - Edge case for None handling
- Line 522: `get_cli_metavar()` - Metadata access fallback

**Why Uncovered:**
These are defensive code paths for edge cases where field metadata might not have specific attributes. They're rarely hit in normal usage but provide robustness.

### builder.py (97.96%)

**Missing Lines:**
- Lines 21-22: Type ignore comments (not executable)
- Line 351: Error handling for invalid field types
- Line 514: Edge case in positional argument handling

**Why Uncovered:**
Mostly error handling paths that would require malformed dataclasses to trigger.

### file_loading.py (87.50%)

**Missing Lines:**
- Lines 60-63: Error handling for missing file loading libraries
- Line 66: Error message construction
- Line 102: Edge case in file type detection

**Why Uncovered:**
Error paths for when optional dependencies (PyYAML, tomli) aren't installed. These are tested in integration but may not appear in standard test runs.

### utils.py (94.68%)

**Missing Lines:**
- Lines 13-14: Import error handling
- Line 20: Fallback logic
- Lines 27-28: Type conversion edge cases

**Why Uncovered:**
Defensive code for unusual type annotations and edge cases.

## Coverage Configuration

Coverage settings are in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["dataclass_config"]
branch = true  # Track branch coverage
omit = ["*/tests/*", "*/examples/*"]

[tool.coverage.report]
precision = 2
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]

[tool.coverage.html]
directory = "htmlcov"

[tool.coverage.xml]
output = "coverage.xml"
```

## Improving Coverage

### Adding Tests for Uncovered Code

To add tests for specific uncovered lines:

```python
# Example: Testing error paths
def test_missing_metadata():
    """Test field without metadata."""
    # Create field without cli_short metadata
    field = Field(default=None, metadata={})
    result = get_cli_short(field)
    assert result is None
```

### Testing Optional Dependencies

```python
# Example: Testing missing library handling
@pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
def test_yaml_loading():
    """Test YAML file loading."""
    # Test YAML functionality
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=dataclass_config --cov-report=xml
    
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
    fail_ci_if_error: true
```

## Coverage Goals

### Current Status: ✅ Excellent

- ✅ Above 90% minimum threshold
- ✅ All critical paths covered
- ✅ Branch coverage tracked
- ✅ Edge cases documented

### Future Goals

- [ ] Reach 95% total coverage
- [ ] Add tests for error handling paths
- [ ] Test optional dependency scenarios
- [ ] Add integration tests for uncovered branches

## Best Practices

1. **Always run tests with coverage** before committing
2. **Review HTML report** to understand what's not covered
3. **Don't chase 100%** - Some defensive code doesn't need testing
4. **Focus on critical paths** - Business logic should be 100%
5. **Document intentional gaps** - If code is uncovered intentionally, mark with `# pragma: no cover`

## Resources

- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

---

**Last Updated:** 2024-11-01  
**Coverage Version:** 94.35%  
**Test Count:** 230 tests passing
