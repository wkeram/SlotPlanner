"""Data storage and persistence module for SlotPlanner.

This module handles JSON-based data persistence for teachers, children,
tandems, optimization weights, and scheduling results.
"""

import json
import os
from typing import Optional, Dict, Any
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class Storage:
    """Handles data persistence for SlotPlanner application data."""

    def __init__(self, data_dir: str = "data"):
        """Initialize storage with data directory.

        Args:
            data_dir: Directory to store JSON files
        """
        self.data_dir = data_dir
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _get_file_path(self, year: str) -> str:
        """Get the file path for a specific school year.

        Args:
            year: School year in format "YYYY_YYYY"

        Returns:
            Full path to the JSON file
        """
        return os.path.join(self.data_dir, f"{year}.json")

    def load(self, year: str) -> Optional[Dict[str, Any]]:
        """Load data for a specific school year.

        Args:
            year: School year in format "YYYY_YYYY"

        Returns:
            Dictionary containing all data for the year, or None if file doesn't exist
        """
        file_path = self._get_file_path(year)

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading data for {year}: {e}")
            return None

    def save(self, year: str, data: Dict[str, Any]) -> bool:
        """Save data for a specific school year.

        Args:
            year: School year in format "YYYY_YYYY"
            data: Dictionary containing all data to save

        Returns:
            True if successful, False otherwise
        """
        file_path = self._get_file_path(year)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            logger.error(f"Error saving data for {year}: {e}")
            return False

    def get_default_data_structure(self) -> Dict[str, Any]:
        """Get the default data structure for a new year.

        Returns:
            Dictionary with default empty structure
        """
        return {
            "teachers": {},
            "children": {},
            "tandems": {},
            "weights": {
                "preferred_teacher": 5,
                "priority_early_slot": 3,
                "tandem_fulfilled": 4,
                "teacher_pause_respected": 1,
                "preserve_existing_plan": 10,
            },
            "schedule": {},
            "violations": [],
        }

    def exists(self, year: str) -> bool:
        """Check if data file exists for a specific year.

        Args:
            year: School year in format "YYYY_YYYY"

        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(self._get_file_path(year))

    def list_years(self) -> list[str]:
        """Get list of all available school years.

        Returns:
            List of school year strings
        """
        if not os.path.exists(self.data_dir):
            return []

        years = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                year = filename[:-5]  # Remove .json extension
                years.append(year)

        return sorted(years)

    def delete(self, year: str) -> bool:
        """Delete data file for a specific year.

        Args:
            year: School year in format "YYYY_YYYY"

        Returns:
            True if successful, False otherwise
        """
        file_path = self._get_file_path(year)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except IOError as e:
            logger.error(f"Error deleting data for {year}: {e}")
            return False
