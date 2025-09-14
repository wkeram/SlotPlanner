"""
Test runner and utilities for SlotPlanner test suite.
Provides test execution commands and result reporting.
"""

import sys
from pathlib import Path

import pytest


def run_optimizer_tests():
    """Run only optimizer tests."""
    test_path = Path("tests/optimizer")
    if not test_path.exists():
        print(f"Warning: Test directory {test_path} does not exist")
        return 0
    return pytest.main([str(test_path), "-v", "-m", "optimizer or not ui", "--tb=short"])


def run_ui_tests():
    """Run only UI tests (requires display)."""
    test_path = Path("tests/ui")
    if not test_path.exists():
        print(f"Warning: Test directory {test_path} does not exist")
        return 0
    return pytest.main([str(test_path), "-v", "-m", "ui", "--tb=short"])


def run_all_tests():
    """Run all tests."""
    test_path = Path("tests")
    if not test_path.exists():
        print(f"Error: Test directory {test_path} does not exist")
        return 1
    return pytest.main([str(test_path), "-v", "--tb=short"])


def run_fast_tests():
    """Run fast tests only (excluding slow performance tests)."""
    test_path = Path("tests")
    if not test_path.exists():
        print(f"Error: Test directory {test_path} does not exist")
        return 1
    return pytest.main([str(test_path), "-v", "-m", "not slow and not performance", "--tb=short"])


def run_integration_tests():
    """Run integration tests only."""
    test_path = Path("tests")
    if not test_path.exists():
        print(f"Error: Test directory {test_path} does not exist")
        return 1
    return pytest.main([str(test_path), "-v", "-m", "integration", "--tb=short"])


def run_performance_tests():
    """Run performance tests only."""
    test_path = Path("tests")
    if not test_path.exists():
        print(f"Error: Test directory {test_path} does not exist")
        return 1
    return pytest.main([str(test_path), "-v", "-m", "performance", "--tb=long"])


def run_tests_with_coverage():
    """Run tests with coverage reporting."""
    test_path = Path("tests")
    if not test_path.exists():
        print(f"Error: Test directory {test_path} does not exist")
        return 1
    return pytest.main(
        [str(test_path), "-v", "--cov=app", "--cov-report=html", "--cov-report=term-missing", "--tb=short"]
    )


def main():
    """Main test runner with command line options."""
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py <command>")
        print("Commands:")
        print("  optimizer    - Run optimizer tests only")
        print("  ui           - Run UI tests only")
        print("  fast         - Run fast tests (no performance tests)")
        print("  integration  - Run integration tests only")
        print("  performance  - Run performance tests only")
        print("  coverage     - Run tests with coverage")
        print("  all          - Run all tests")
        return 1

    command = sys.argv[1].lower()

    try:
        if command == "optimizer":
            exit_code = run_optimizer_tests()
        elif command == "ui":
            exit_code = run_ui_tests()
        elif command == "fast":
            exit_code = run_fast_tests()
        elif command == "integration":
            exit_code = run_integration_tests()
        elif command == "performance":
            exit_code = run_performance_tests()
        elif command == "coverage":
            exit_code = run_tests_with_coverage()
        elif command == "all":
            exit_code = run_all_tests()
        else:
            print(f"Unknown command: {command}")
            return 1

        # Ensure proper exit code
        return 0 if exit_code == 0 else 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
