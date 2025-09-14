#!/usr/bin/env python3
"""Version management script for SlotPlanner.

This script provides comprehensive version management including:
- Setting new versions with validation
- Checking if versions already exist (git tags)
- Creating git tags after releases
- Semantic version validation
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


class VersionManager:
    """Manages version operations for SlotPlanner."""

    def __init__(self):
        """Initialize version manager."""
        self.project_root = Path(__file__).parent.parent
        self.version_file = self.project_root / "version.json"

    def load_version_data(self) -> dict:
        """Load current version data from version.json."""
        if not self.version_file.exists():
            raise FileNotFoundError(f"Version file not found: {self.version_file}")

        try:
            with open(self.version_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load version file: {e}") from e

    def save_version_data(self, data: dict) -> None:
        """Save version data to version.json."""
        try:
            with open(self.version_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise RuntimeError(f"Failed to save version file: {e}") from e

    def validate_semantic_version(self, version: str) -> bool:
        """Validate that version follows semantic versioning."""
        # Semantic version pattern: MAJOR.MINOR.PATCH[-prerelease][+build]
        pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
        return bool(re.match(pattern, version))

    def parse_version(self, version: str) -> tuple[int, int, int, str | None, str | None]:
        """Parse version string into components."""
        if not self.validate_semantic_version(version):
            raise ValueError(f"Invalid semantic version: {version}")

        # Split on + for build metadata
        version_part, _, build = version.partition("+")

        # Split on - for pre-release
        core_part, _, pre_release = version_part.partition("-")

        # Split core version
        major, minor, patch = map(int, core_part.split("."))

        return major, minor, patch, pre_release or None, build or None

    def get_current_version(self) -> str:
        """Get current version string."""
        data = self.load_version_data()
        return data["version"]

    def check_git_tag_exists(self, version: str) -> bool:
        """Check if git tag for version already exists."""
        try:
            result = subprocess.run(
                ["git", "tag", "-l", f"v{version}"], cwd=self.project_root, capture_output=True, text=True, check=False
            )
            if result.returncode != 0:
                print(f"Warning: Could not check git tags (exit code {result.returncode})")
                return False
            return bool(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            print(f"Warning: Could not check git tags ({type(e).__name__}: {e})")
            return False

    def create_git_tag(
        self, version: str, message: str | None = None, push: bool = False, interactive: bool = True
    ) -> bool:
        """Create a git tag for the version."""
        tag_name = f"v{version}"
        tag_message = message or f"Release version {version}"

        try:
            # Create annotated tag
            subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_message], cwd=self.project_root, check=True)
            print(f"SUCCESS: Created git tag: {tag_name}")

            # Push tag if requested or in non-interactive mode
            should_push = push
            if interactive and not push:
                response = input("Push tag to remote? (y/N): ").lower().strip()
                should_push = response in ("y", "yes")

            if should_push:
                subprocess.run(["git", "push", "origin", tag_name], cwd=self.project_root, check=True)
                print(f"SUCCESS: Pushed tag {tag_name} to remote")

            return True
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to create git tag: {e}")
            return False

    def set_version(self, new_version: str, create_tag: bool = False, interactive: bool = True) -> bool:
        """Set a new version with validation."""
        print(f"Setting version to: {new_version}")

        # Validate semantic version
        if not self.validate_semantic_version(new_version):
            print(f"ERROR: Invalid semantic version: {new_version}")
            print("Version must follow semantic versioning (e.g., 1.0.0, 1.0.0-alpha.1, 1.0.0+build.123)")
            return False

        # Check if version already exists as git tag (skip in CI to avoid blocking)
        import os

        if not os.environ.get("CI") and self.check_git_tag_exists(new_version):
            print(f"ERROR: Version v{new_version} already exists as a git tag!")
            print("Choose a different version or delete the existing tag first.")
            return False
        elif os.environ.get("CI"):
            print(f"CI environment detected - skipping git tag check for v{new_version}")

        # Parse version components
        try:
            major, minor, patch, pre_release, build = self.parse_version(new_version)
        except ValueError as e:
            print(f"ERROR: Error parsing version: {e}")
            return False

        # Load current data and update
        data = self.load_version_data()
        old_version = data["version"]

        data["version"] = new_version
        data["version_info"] = {
            "major": major,
            "minor": minor,
            "patch": patch,
            "pre_release": pre_release,
            "build": build,
        }
        data["last_updated"] = datetime.now(UTC).isoformat()

        # Save updated version
        try:
            self.save_version_data(data)
            print(f"SUCCESS: Version updated: {old_version} -> {new_version}")
        except RuntimeError as e:
            print(f"ERROR: Failed to save version: {e}")
            return False

        # Create git tag if requested
        if create_tag:
            if not self.create_git_tag(new_version, interactive=interactive):
                print("WARNING: Version was updated but git tag creation failed")
                return False

        return True

    def bump_version(self, part: str, create_tag: bool = False, interactive: bool = True) -> bool:
        """Bump version part (major, minor, patch)."""
        if part not in ["major", "minor", "patch"]:
            print("ERROR: Part must be 'major', 'minor', or 'patch'")
            return False

        current = self.get_current_version()
        try:
            major, minor, patch, pre_release, build = self.parse_version(current)
        except ValueError as e:
            print(f"ERROR: Error parsing current version: {e}")
            return False

        # Only bump non-pre-release versions
        if pre_release or build:
            print(f"ERROR: Cannot bump pre-release or build versions. Current: {current}")
            print("Set a stable version first (e.g., 1.0.0)")
            return False

        # Bump the appropriate part
        if part == "major":
            major += 1
            minor = 0
            patch = 0
        elif part == "minor":
            minor += 1
            patch = 0
        elif part == "patch":
            patch += 1

        new_version = f"{major}.{minor}.{patch}"
        return self.set_version(new_version, create_tag, interactive)

    def show_status(self) -> None:
        """Show current version status."""
        try:
            data = self.load_version_data()
            version = data["version"]
            version_info = data["version_info"]

            print(f"Current version: {version}")
            print(f"Components: {version_info['major']}.{version_info['minor']}.{version_info['patch']}")

            if version_info.get("pre_release"):
                print(f"Pre-release: {version_info['pre_release']}")
            if version_info.get("build"):
                print(f"Build: {version_info['build']}")

            print(f"Last updated: {data.get('last_updated', 'Unknown')}")

            # Check if git tag exists
            if self.check_git_tag_exists(version):
                print(f"SUCCESS: Git tag v{version} exists")
            else:
                print(f"WARNING: Git tag v{version} does not exist")

        except Exception as e:
            print(f"ERROR: Error getting version status: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SlotPlanner Version Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/version-manager.py status                    # Show current version
  python scripts/version-manager.py set 1.0.0                # Set version to 1.0.0
  python scripts/version-manager.py set 1.0.0 --tag          # Set version and create git tag
  python scripts/version-manager.py bump major               # Bump major version
  python scripts/version-manager.py bump minor --tag         # Bump minor and create tag
  python scripts/version-manager.py tag                      # Create git tag for current version
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show current version status")

    # Set command
    set_parser = subparsers.add_parser("set", help="Set a specific version")
    set_parser.add_argument("version", help="Version to set (e.g., 1.0.0)")
    set_parser.add_argument("--tag", action="store_true", help="Create git tag")
    set_parser.add_argument("--no-interactive", action="store_true", help="Run in non-interactive mode for CI")

    # Bump command
    bump_parser = subparsers.add_parser("bump", help="Bump version part")
    bump_parser.add_argument("part", choices=["major", "minor", "patch"], help="Version part to bump")
    bump_parser.add_argument("--tag", action="store_true", help="Create git tag")
    bump_parser.add_argument("--no-interactive", action="store_true", help="Run in non-interactive mode for CI")

    # Tag command
    tag_parser = subparsers.add_parser("tag", help="Create git tag for current version")
    tag_parser.add_argument("--no-interactive", action="store_true", help="Run in non-interactive mode for CI")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    vm = VersionManager()

    try:
        if args.command == "status":
            vm.show_status()
        elif args.command == "set":
            interactive = not getattr(args, "no_interactive", False)
            success = vm.set_version(args.version, args.tag, interactive)
            return 0 if success else 1
        elif args.command == "bump":
            interactive = not getattr(args, "no_interactive", False)
            success = vm.bump_version(args.part, args.tag, interactive)
            return 0 if success else 1
        elif args.command == "tag":
            version = vm.get_current_version()
            interactive = not getattr(args, "no_interactive", False)
            success = vm.create_git_tag(version, interactive=interactive)
            return 0 if success else 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
