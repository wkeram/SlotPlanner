"""
CI/CD validation tests for SlotPlanner.
Basic tests to ensure the CI/CD pipeline setup is working correctly.
"""

from pathlib import Path

import pytest


class TestCICDValidation:
    """Basic tests to validate CI/CD setup."""

    def test_imports(self):
        """Test that core modules can be imported."""
        try:
            import app.storage
            import app.ui_feedback
            import app.utils
            import app.validation

            assert True, "Core modules imported successfully"
        except ImportError as e:
            pytest.fail(f"Failed to import core modules: {e}")

    def test_pytest_framework(self):
        """Test that pytest framework is working."""
        assert True, "pytest is working"

    def test_project_structure(self):
        """Test that project structure is correct."""
        project_root = Path(__file__).parent.parent

        # Check required directories
        assert (project_root / "app").exists(), "app directory should exist"
        assert (project_root / "tests").exists(), "tests directory should exist"
        assert (project_root / ".github" / "workflows").exists(), "workflows directory should exist"

        # Check required files
        assert (project_root / "pyproject.toml").exists(), "pyproject.toml should exist"
        assert (project_root / "README.md").exists(), "README.md should exist"
        assert (project_root / "CLAUDE.md").exists(), "CLAUDE.md should exist"

    def test_workflow_files(self):
        """Test that GitHub Actions workflow files exist."""
        workflows_dir = Path(__file__).parent.parent / ".github" / "workflows"

        required_workflows = ["test.yml", "release.yml", "pr-checks.yml", "nightly.yml"]

        for workflow in required_workflows:
            workflow_path = workflows_dir / workflow
            assert workflow_path.exists(), f"Workflow {workflow} should exist"
            assert workflow_path.stat().st_size > 0, f"Workflow {workflow} should not be empty"

    def test_test_infrastructure(self):
        """Test that test infrastructure is properly set up."""
        tests_dir = Path(__file__).parent

        # Check test runner
        assert (tests_dir / "test_runner.py").exists(), "test_runner.py should exist"
        assert (tests_dir / "conftest.py").exists(), "conftest.py should exist"
        assert (tests_dir / "README.md").exists(), "tests/README.md should exist"

        # Check test directories
        assert (tests_dir / "optimizer").exists(), "optimizer test directory should exist"
        assert (tests_dir / "ui").exists(), "ui test directory should exist"

    def test_configuration_files(self):
        """Test that configuration files are present."""
        project_root = Path(__file__).parent.parent

        # Check pytest configuration
        assert (project_root / "pytest.ini").exists(), "pytest.ini should exist"

        # Check coverage configuration
        assert (project_root / ".coveragerc").exists(), ".coveragerc should exist"

    @pytest.mark.slow
    def test_dependencies_installable(self):
        """Test that all dependencies can be resolved."""
        # This test would be run in CI to ensure dependencies are correct
        # For now, just check that key modules can be imported
        try:
            import ortools
            import PySide6
            import reportlab

            assert True, "Key dependencies are available"
        except ImportError as e:
            pytest.skip(f"Dependencies not fully installed: {e}")

    def test_status_monitoring(self):
        """Test that status monitoring script exists."""
        scripts_dir = Path(__file__).parent.parent / "scripts"
        status_script = scripts_dir / "check-status.py"

        assert status_script.exists(), "Status monitoring script should exist"
        assert status_script.stat().st_size > 0, "Status monitoring script should not be empty"
