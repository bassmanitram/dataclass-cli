#!/usr/bin/env python
"""
Test script to diagnose CI environment issues.
Run this in CI to see what's failing.
"""

import sys
import traceback

def test_section(name):
    """Print test section header."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)

def check_python_version():
    """Check Python version."""
    test_section("Python Version")
    print(f"Python {sys.version}")
    print(f"Version info: {sys.version_info}")
    assert sys.version_info >= (3, 8), "Python 3.8+ required"
    print("✅ PASS")

def check_typing_imports():
    """Check typing imports work."""
    test_section("Typing Imports")
    try:
        from typing import get_args, get_origin, get_type_hints
        print("✅ Imported from typing")
    except ImportError as e:
        print(f"⚠️ typing import failed: {e}")
        print("Trying typing_extensions...")
        from typing_extensions import get_args, get_origin, get_type_hints
        print("✅ Imported from typing_extensions")
    
    # Test they work
    from typing import Optional, List
    origin = get_origin(Optional[str])
    assert origin is not None
    print(f"✅ get_origin works: {origin}")
    
    args = get_args(List[int])
    assert len(args) == 1
    print(f"✅ get_args works: {args}")
    print("✅ PASS")

def check_package_import():
    """Check dataclass_cli can be imported."""
    test_section("Package Import")
    import dataclass_cli
    print(f"✅ Imported dataclass_cli version {dataclass_cli.__version__}")
    
    from dataclass_cli import (
        build_config,
        build_config_from_cli,
        GenericConfigBuilder,
        cli_exclude,
        cli_help,
        cli_file_loadable,
    )
    print("✅ All main imports work")
    print("✅ PASS")

def check_optional_dependencies():
    """Check optional dependencies."""
    test_section("Optional Dependencies")
    
    # Check PyYAML
    try:
        import yaml
        print(f"✅ PyYAML is installed")
    except ImportError:
        print("⚠️ PyYAML not installed (optional)")
    
    # Check TOML
    try:
        import tomllib
        print(f"✅ tomllib available (Python 3.11+)")
    except ImportError:
        try:
            import tomli
            print(f"✅ tomli is installed")
        except ImportError:
            print("⚠️ TOML support not available (optional)")
    
    # Check typing_extensions
    try:
        import typing_extensions
        print(f"✅ typing_extensions is installed")
    except ImportError:
        print("❌ typing_extensions NOT installed (required!)")
        sys.exit(1)
    
    print("✅ PASS")

def check_basic_functionality():
    """Test basic functionality."""
    test_section("Basic Functionality")
    from dataclasses import dataclass
    from dataclass_cli import build_config
    
    @dataclass
    class TestConfig:
        name: str
        count: int = 10
    
    try:
        config = build_config(TestConfig, ['--name', 'test'])
        assert config.name == 'test'
        assert config.count == 10
        print("✅ build_config works")
    except Exception as e:
        print(f"❌ build_config failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    print("✅ PASS")

def check_test_discovery():
    """Check pytest can discover tests."""
    test_section("Test Discovery")
    import subprocess
    result = subprocess.run(
        ['python', '-m', 'pytest', '--collect-only', 'tests/', '-q'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Test collection failed:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    
    # Count tests
    lines = result.stdout.strip().split('\n')
    for line in lines:
        if 'test' in line.lower():
            print(line)
    
    print("✅ PASS")

def main():
    """Run all checks."""
    print("="*60)
    print("CI ENVIRONMENT DIAGNOSTIC TESTS")
    print("="*60)
    
    tests = [
        check_python_version,
        check_typing_imports,
        check_package_import,
        check_optional_dependencies,
        check_basic_functionality,
        check_test_discovery,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ FAILED: {e}")
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print('='*60)
    
    if failed > 0:
        sys.exit(1)
    
    print("\n✅ All diagnostic tests passed!")
    print("If tests are still failing in CI, the issue is likely:")
    print("  1. Platform-specific (Windows/macOS differences)")
    print("  2. Python version-specific (try Python 3.8)")
    print("  3. Test-specific logic errors")

if __name__ == '__main__':
    main()
