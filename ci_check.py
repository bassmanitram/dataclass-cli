#!/usr/bin/env python
"""
CI Environment Check Script
Diagnoses common CI failures for dataclass-cli
"""

import sys
import subprocess
from pathlib import Path

def run_check(name, command, critical=True):
    """Run a check command and report status."""
    print(f"\n{'='*60}")
    print(f"CHECK: {name}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ PASS")
            if result.stdout:
                print(result.stdout[:500])
        else:
            print(f"❌ FAIL (exit code: {result.returncode})")
            if result.stderr:
                print("STDERR:", result.stderr[:500])
            if result.stdout:
                print("STDOUT:", result.stdout[:500])
            if critical:
                return False
        return True
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

def main():
    print("="*60)
    print("DATACLASS-CLI CI ENVIRONMENT CHECK")
    print("="*60)
    print(f"Python: {sys.version}")
    print(f"Path: {Path.cwd()}")
    
    checks = [
        ("Import dataclass_cli", "python -c 'import dataclass_cli; print(dataclass_cli.__version__)'"),
        ("Import typing_extensions", "python -c 'import typing_extensions; print(\"typing_extensions OK\")'"),
        ("Check get_origin/get_args", "python -c 'from typing import get_origin, get_args; print(\"typing OK\")'"),
        ("Run pytest discovery", "python -m pytest tests/ --collect-only -q"),
        ("Run basic tests", "python -m pytest tests/test_basic.py -v"),
        ("Run file loading tests", "python -m pytest tests/test_file_loading.py -v"),
        ("Black check", "black --check dataclass_cli/ tests/ examples/", False),
        ("isort check", "isort --check-only dataclass_cli/ tests/ examples/", False),
        ("mypy check (may fail on 3.8)", "mypy dataclass_cli/", False),
    ]
    
    passed = 0
    failed = 0
    
    for name, command, *args in checks:
        critical = args[0] if args else True
        if run_check(name, command, critical):
            passed += 1
        else:
            failed += 1
            if critical:
                print(f"\n❌ CRITICAL CHECK FAILED: {name}")
                print("Stopping further checks")
                break
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
