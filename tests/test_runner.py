"""
Test runner and utilities for SlotPlanner test suite.
Provides test execution commands and result reporting.
"""

import sys

import pytest


def run_optimizer_tests():
    """Run only optimizer tests."""
    return pytest.main(["tests/optimizer/", "-v", "-m", "optimizer or not ui", "--tb=short", "--disable-warnings"])


def run_ui_tests():
    """Run only UI tests (requires display)."""
    return pytest.main(["tests/ui/", "-v", "-m", "ui", "--tb=short"])


def run_all_tests():
    """Run all tests."""
    return pytest.main(["tests/", "-v", "--tb=short"])


def run_fast_tests():
    """Run fast tests only (excluding slow performance tests)."""
    return pytest.main(["tests/", "-v", "-m", "not slow and not performance", "--tb=short"])


def run_integration_tests():
    """Run integration tests only."""
    return pytest.main(["tests/", "-v", "-m", "integration", "--tb=short"])


def run_performance_tests():
    """Run performance tests only."""
    return pytest.main(["tests/", "-v", "-m", "performance", "--tb=long"])


def run_tests_with_coverage():
    """Run tests with coverage reporting."""
    return pytest.main(["tests/", "-v", "--cov=app", "--cov-report=html", "--cov-report=term-missing", "--tb=short"])


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

    if command == "optimizer":
        return run_optimizer_tests()
    elif command == "ui":
        return run_ui_tests()
    elif command == "fast":
        return run_fast_tests()
    elif command == "integration":
        return run_integration_tests()
    elif command == "performance":
        return run_performance_tests()
    elif command == "coverage":
        return run_tests_with_coverage()
    elif command == "all":
        return run_all_tests()
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
