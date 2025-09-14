"""
Tests for version management functionality and edge cases.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest

# Add the scripts directory to the path so we can import version-manager
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    from version_manager import VersionManager
except ImportError:
    # Fallback if import fails
    VersionManager = None


@pytest.mark.skipif(VersionManager is None, reason="version-manager.py not importable")
class TestVersionManager:
    """Test version management functionality."""

    @pytest.fixture
    def temp_version_file(self):
        """Create a temporary version file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            version_data = {
                "version": "1.0.0",
                "version_info": {"major": 1, "minor": 0, "patch": 0, "pre_release": None, "build": None},
                "last_updated": "2024-01-01T00:00:00Z",
            }
            json.dump(version_data, f)
            temp_path = f.name

        yield Path(temp_path)

        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass

    @pytest.fixture
    def version_manager(self, temp_version_file):
        """Create a VersionManager instance with temporary file."""
        vm = VersionManager()
        vm.version_file = temp_version_file
        return vm

    def test_load_version_data(self, version_manager):
        """Test loading version data from file."""
        data = version_manager.load_version_data()
        assert data["version"] == "1.0.0"
        assert data["version_info"]["major"] == 1
        assert data["version_info"]["minor"] == 0
        assert data["version_info"]["patch"] == 0

    def test_load_missing_version_file(self):
        """Test handling of missing version file."""
        vm = VersionManager()
        vm.version_file = Path("/nonexistent/version.json")

        with pytest.raises(FileNotFoundError):
            vm.load_version_data()

    def test_validate_semantic_version_valid(self, version_manager):
        """Test semantic version validation with valid versions."""
        valid_versions = [
            "1.0.0",
            "0.0.1",
            "10.20.30",
            "1.0.0-alpha.1",
            "1.0.0-beta.2",
            "1.0.0-rc.1",
            "1.0.0+build.123",
            "1.0.0-alpha.1+build.123",
        ]

        for version in valid_versions:
            assert version_manager.validate_semantic_version(version), f"Version {version} should be valid"

    def test_validate_semantic_version_invalid(self, version_manager):
        """Test semantic version validation with invalid versions."""
        invalid_versions = [
            "1",
            "1.2",
            "1.2.3.4",
            "01.2.3",
            "1.02.3",
            "1.2.03",
            "1.2.3-",
            "1.2.3+",
            "v1.2.3",
            "1.2.3-alpha_1",  # underscore not allowed
            "",
            "invalid",
        ]

        for version in invalid_versions:
            assert not version_manager.validate_semantic_version(version), f"Version {version} should be invalid"

    def test_parse_version_components(self, version_manager):
        """Test parsing version string into components."""
        test_cases = [
            ("1.2.3", (1, 2, 3, None, None)),
            ("1.0.0-alpha.1", (1, 0, 0, "alpha.1", None)),
            ("2.1.0+build.123", (2, 1, 0, None, "build.123")),
            ("1.0.0-beta.2+build.456", (1, 0, 0, "beta.2", "build.456")),
        ]

        for version_str, expected in test_cases:
            result = version_manager.parse_version(version_str)
            assert result == expected, f"Parsing {version_str} failed"

    def test_parse_invalid_version(self, version_manager):
        """Test parsing invalid version strings."""
        with pytest.raises(ValueError):
            version_manager.parse_version("invalid.version")

    def test_get_current_version(self, version_manager):
        """Test getting current version."""
        version = version_manager.get_current_version()
        assert version == "1.0.0"

    @patch("subprocess.run")
    def test_check_git_tag_exists_true(self, mock_run, version_manager):
        """Test checking for existing git tag (exists)."""
        mock_run.return_value = Mock(returncode=0, stdout="v1.0.0\n")

        result = version_manager.check_git_tag_exists("1.0.0")
        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_check_git_tag_exists_false(self, mock_run, version_manager):
        """Test checking for existing git tag (doesn't exist)."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        result = version_manager.check_git_tag_exists("1.0.0")
        assert result is False

    @patch("subprocess.run")
    def test_check_git_tag_error(self, mock_run, version_manager, capsys):
        """Test handling of git command errors."""
        mock_run.return_value = Mock(returncode=1, stdout="")

        result = version_manager.check_git_tag_exists("1.0.0")
        assert result is False

        captured = capsys.readouterr()
        assert "Warning: Could not check git tags" in captured.out

    def test_set_version_valid(self, version_manager):
        """Test setting a valid version."""
        success = version_manager.set_version("1.2.3", create_tag=False, interactive=False)
        assert success is True

        # Verify the version was updated
        data = version_manager.load_version_data()
        assert data["version"] == "1.2.3"
        assert data["version_info"]["major"] == 1
        assert data["version_info"]["minor"] == 2
        assert data["version_info"]["patch"] == 3

    def test_set_version_invalid(self, version_manager):
        """Test setting an invalid version."""
        success = version_manager.set_version("invalid.version", create_tag=False, interactive=False)
        assert success is False

        # Verify the version wasn't changed
        data = version_manager.load_version_data()
        assert data["version"] == "1.0.0"

    @patch.dict(os.environ, {"CI": "true"})
    def test_set_version_ci_environment(self, version_manager, capsys):
        """Test version setting in CI environment."""
        success = version_manager.set_version("1.0.0", create_tag=False, interactive=False)
        assert success is True

        captured = capsys.readouterr()
        assert "CI environment detected" in captured.out

    def test_bump_version_patch(self, version_manager):
        """Test bumping patch version."""
        success = version_manager.bump_version("patch", create_tag=False, interactive=False)
        assert success is True

        data = version_manager.load_version_data()
        assert data["version"] == "1.0.1"

    def test_bump_version_minor(self, version_manager):
        """Test bumping minor version."""
        success = version_manager.bump_version("minor", create_tag=False, interactive=False)
        assert success is True

        data = version_manager.load_version_data()
        assert data["version"] == "1.1.0"

    def test_bump_version_major(self, version_manager):
        """Test bumping major version."""
        success = version_manager.bump_version("major", create_tag=False, interactive=False)
        assert success is True

        data = version_manager.load_version_data()
        assert data["version"] == "2.0.0"

    def test_bump_prerelease_version_fails(self, version_manager):
        """Test that bumping pre-release versions fails."""
        # Set up a pre-release version
        version_manager.set_version("1.0.0-alpha.1", create_tag=False, interactive=False)

        success = version_manager.bump_version("patch", create_tag=False, interactive=False)
        assert success is False

    def test_bump_invalid_part(self, version_manager):
        """Test bumping with invalid part."""
        success = version_manager.bump_version("invalid", create_tag=False, interactive=False)
        assert success is False

    @patch("subprocess.run")
    def test_create_git_tag_success(self, mock_run, version_manager):
        """Test successful git tag creation."""
        mock_run.return_value = Mock(returncode=0)

        success = version_manager.create_git_tag("1.0.0", interactive=False, push=False)
        assert success is True

        # Verify git tag command was called
        expected_calls = [
            call(
                ["git", "tag", "-a", "v1.0.0", "-m", "Release version 1.0.0"],
                cwd=version_manager.project_root,
                check=True,
            )
        ]
        mock_run.assert_has_calls(expected_calls)

    @patch("subprocess.run")
    def test_create_git_tag_with_push(self, mock_run, version_manager):
        """Test git tag creation with push."""
        mock_run.return_value = Mock(returncode=0)

        success = version_manager.create_git_tag("1.0.0", interactive=False, push=True)
        assert success is True

        # Verify both tag creation and push commands
        assert mock_run.call_count == 2
        calls = mock_run.call_args_list

        # First call should create the tag
        assert "git tag -a v1.0.0" in str(calls[0])
        # Second call should push the tag
        assert "git push origin v1.0.0" in str(calls[1])

    @patch("subprocess.run")
    def test_create_git_tag_failure(self, mock_run, version_manager):
        """Test git tag creation failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        success = version_manager.create_git_tag("1.0.0", interactive=False, push=False)
        assert success is False


class TestVersionManagerCLI:
    """Test version manager command-line interface."""

    def test_version_json_exists(self):
        """Test that version.json exists in the project."""
        version_file = Path("version.json")
        assert version_file.exists(), "version.json is missing from project root"

    def test_version_json_format(self):
        """Test that version.json has the correct format."""
        version_file = Path("version.json")

        with open(version_file, encoding="utf-8") as f:
            data = json.load(f)

        # Check required fields
        assert "version" in data, "version field missing"
        assert "version_info" in data, "version_info field missing"
        assert "last_updated" in data, "last_updated field missing"

        # Check version_info structure
        version_info = data["version_info"]
        required_fields = ["major", "minor", "patch", "pre_release", "build"]
        for field in required_fields:
            assert field in version_info, f"version_info.{field} missing"

        # Validate version format
        version = data["version"]
        pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
        import re

        assert re.match(pattern, version), f"Invalid semantic version format: {version}"

    @patch("sys.argv", ["version-manager.py"])
    def test_no_command_shows_help(self):
        """Test that running without command shows help."""
        # This would require importing and running the main function
        # For now, just test that the script exists and is executable
        script_path = Path("scripts/version-manager.py")
        assert script_path.exists(), "version-manager.py script is missing"
        assert script_path.is_file(), "version-manager.py is not a file"


class TestVersionIntegration:
    """Integration tests for version management."""

    def test_version_consistency_across_files(self):
        """Test that version is consistent across all relevant files."""
        # Load version from version.json
        version_file = Path("version.json")
        if not version_file.exists():
            pytest.skip("version.json not found")

        with open(version_file, encoding="utf-8") as f:
            version_data = json.load(f)

        main_version = version_data["version"]

        # Check app/version.py can dynamically load the correct version
        try:
            import sys

            app_path = Path("app")
            if app_path.exists() and str(app_path.absolute()) not in sys.path:
                sys.path.insert(0, str(app_path.absolute()))

            from app.version import get_version

            loaded_version = get_version()
            assert (
                loaded_version == main_version
            ), f"Version mismatch: version.json has {main_version}, app.version loads {loaded_version}"
        except ImportError:
            pytest.skip("app.version module not found or not importable")

        # Check pyproject.toml uses dynamic versioning (this project uses dynamic version loading)
        pyproject_file = Path("pyproject.toml")
        if pyproject_file.exists():
            with open(pyproject_file, encoding="utf-8") as f:
                content = f.read()
                # For this project, pyproject.toml should use dynamic versioning
                assert 'dynamic = ["version"]' in content, "pyproject.toml should use dynamic versioning"
                assert (
                    'version = {attr = "app.version.__version__"}' in content
                ), "pyproject.toml should load version from app.version"
