#!/usr/bin/env python3
"""
CI/CD Status Monitoring Script for SlotPlanner

Checks the status of GitHub Actions workflows and provides
a consolidated report of build and test status.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd):
    """Run shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def check_local_tests():
    """Check if local tests can run successfully."""
    print("[CHECKING] Local test environment...")

    # Check if uv is available
    success, _, _ = run_command("uv --version")
    if not success:
        print("[FAIL] uv package manager not found")
        return False

    # Check if dependencies are synced
    success, _, _ = run_command("uv sync --dry-run")
    if not success:
        print("[FAIL] Dependencies not synced. Run: uv sync --all-extras --dev")
        return False

    # Run quick test check
    print("   Running quick test validation...")
    success, stdout, stderr = run_command(
        "uv run python -c \"import app.logic; import app.storage; print('[OK] Core modules importable')\""
    )
    if not success:
        print(f"[FAIL] Core modules import failed: {stderr}")
        return False

    print("[OK] Local test environment ready")
    return True


def check_test_coverage():
    """Check current test coverage."""
    print("[CHECKING] Test coverage...")

    if not Path("coverage.xml").exists():
        print("   No coverage report found. Generate with: uv run python tests/test_runner.py coverage")
        return

    # Parse coverage report (simplified)
    try:
        with open("coverage.xml") as f:
            content = f.read()
            if 'line-rate="' in content:
                start = content.find('line-rate="') + len('line-rate="')
                end = content.find('"', start)
                coverage = float(content[start:end]) * 100
                print(f"   Current coverage: {coverage:.1f}%")

                if coverage >= 90:
                    print("[OK] Coverage above 90% target")
                else:
                    print(f"[WARN] Coverage below 90% target ({coverage:.1f}%)")
    except Exception as e:
        print(f"   Could not parse coverage report: {e}")


def check_git_status():
    """Check git repository status."""
    print("[CHECKING] Git repository status...")

    # Check if we're in a git repository
    success, _, _ = run_command("git rev-parse --git-dir")
    if not success:
        print("[FAIL] Not in a git repository")
        return False

    # Check for uncommitted changes
    success, stdout, _ = run_command("git status --porcelain")
    if stdout:
        print("[WARN] Uncommitted changes detected:")
        for line in stdout.split("\n")[:5]:  # Show first 5 files
            print(f"     {line}")
        lines = stdout.split("\n")
        if len(lines) > 5:
            print(f"     ... and {len(lines) - 5} more files")
    else:
        print("[OK] Working directory clean")

    # Check current branch
    success, branch, _ = run_command("git branch --show-current")
    if success:
        print(f"   Current branch: {branch}")

    return True


def check_workflow_files():
    """Check if workflow files are present and valid."""
    print("[CHECKING] GitHub Actions workflow files...")

    workflow_dir = Path(".github/workflows")
    if not workflow_dir.exists():
        print("[FAIL] .github/workflows directory not found")
        return False

    required_workflows = ["test.yml", "release.yml", "pr-checks.yml", "nightly.yml"]

    missing_workflows = []
    for workflow in required_workflows:
        workflow_path = workflow_dir / workflow
        if not workflow_path.exists():
            missing_workflows.append(workflow)
        else:
            # Basic YAML syntax check
            try:
                import yaml

                with open(workflow_path) as f:
                    yaml.safe_load(f)
                print(f"[OK] {workflow} - valid")
            except ImportError:
                print(f"[WARN] {workflow} - present (YAML validation unavailable)")
            except yaml.YAMLError as e:
                print(f"[FAIL] {workflow} - invalid YAML: {e}")

    if missing_workflows:
        print(f"[FAIL] Missing workflows: {', '.join(missing_workflows)}")
        return False

    return True


def generate_status_report():
    """Generate a comprehensive status report."""
    print("=" * 60)
    print("SlotPlanner CI/CD Status Report")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    checks_passed = 0
    total_checks = 4

    # Local environment check
    if check_local_tests():
        checks_passed += 1
    print()

    # Git repository check
    if check_git_status():
        checks_passed += 1
    print()

    # Workflow files check
    if check_workflow_files():
        checks_passed += 1
    print()

    # Coverage check (informational)
    check_test_coverage()
    checks_passed += 1  # Always count as passed (informational only)
    print()

    # Overall status
    print("=" * 60)
    print("Overall Status")
    print("=" * 60)

    if checks_passed == total_checks:
        print("[OK] All checks passed - Ready for CI/CD")
        print()
        print("Next steps:")
        print("  1. Commit and push your changes")
        print("  2. Create a pull request")
        print("  3. Monitor GitHub Actions for automated tests")
        return True
    else:
        print(f"[WARN] {checks_passed}/{total_checks} checks passed")
        print("Please address the issues above before proceeding.")
        return False


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("SlotPlanner CI/CD Status Checker")
        print()
        print("Usage: python scripts/check-status.py")
        print()
        print("This script checks:")
        print("  - Local test environment setup")
        print("  - Git repository status")
        print("  - GitHub Actions workflow files")
        print("  - Test coverage (if available)")
        print()
        print("Run this before committing to ensure CI/CD readiness.")
        return

    success = generate_status_report()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
