"""Version management module for SlotPlanner."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple


def get_version_file_path() -> Path:
    """Get the path to the version configuration file."""
    # Look for version.json in the project root (parent of app directory)
    app_dir = Path(__file__).parent
    project_root = app_dir.parent
    return project_root / "version.json"


def load_version_info() -> Dict[str, Any]:
    """Load version information from version.json."""
    version_file = get_version_file_path()

    if not version_file.exists():
        # Fallback to default version if file doesn't exist
        return {
            "version": "0.1.0",
            "version_info": {"major": 0, "minor": 1, "patch": 0, "pre_release": None, "build": None},
        }

    try:
        with open(version_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise RuntimeError(f"Failed to load version information: {e}")


def get_version() -> str:
    """Get the current version string."""
    version_info = load_version_info()
    return version_info["version"]


def get_version_tuple() -> Tuple[int, int, int]:
    """Get version as a tuple (major, minor, patch)."""
    version_info = load_version_info()
    info = version_info["version_info"]
    return (info["major"], info["minor"], info["patch"])


def get_full_version_info() -> Dict[str, Any]:
    """Get full version information including metadata."""
    return load_version_info()


# Make version available at module level for easy import
__version__ = get_version()
