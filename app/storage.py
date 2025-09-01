"""Data storage and persistence module for SlotPlanner.

This module handles JSON-based data persistence for teachers, children,
tandems, optimization weights, and scheduling results.
"""

import json
import os
import re
from datetime import datetime
from typing import Any

from app.config.logging_config import get_logger

logger = get_logger(__name__)


class Storage:
    """Handles data persistence for SlotPlanner application data."""

    def __init__(self, data_dir: str = None, export_dir: str = None):
        """Initialize storage with data and export directories.

        Args:
            data_dir: Directory to store JSON files (default: absolute path to ./data)
            export_dir: Directory to store PDF exports (default: absolute path to ./exports)
        """
        self.data_dir = data_dir or os.path.abspath("data")
        self.export_dir = export_dir or os.path.abspath("exports")
        self._ensure_data_dir()
        self._ensure_export_dir()

    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _ensure_export_dir(self) -> None:
        """Create export directory if it doesn't exist."""
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def _validate_year_format(self, year: str) -> bool:
        """Validate that year follows the expected YYYY_YYYY format.

        Args:
            year: School year string to validate

        Returns:
            True if year format is valid, False otherwise
        """
        if not isinstance(year, str):
            return False

        # Check for basic format YYYY_YYYY where YYYY are 4-digit years
        pattern = r"^\d{4}_\d{4}$"
        if not re.match(pattern, year):
            return False

        # Additional validation: years should be consecutive
        try:
            year1, year2 = year.split("_")
            year1_int = int(year1)
            year2_int = int(year2)

            # School year should be consecutive (e.g., 2023_2024)
            if year2_int != year1_int + 1:
                return False

            # Reasonable year range (1900-2100)
            if year1_int < 1900 or year1_int > 2100:
                return False

            return True
        except (ValueError, IndexError):
            return False

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal attacks.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename safe for use
        """
        # Remove any path separators and dangerous characters
        filename = os.path.basename(filename)

        # Remove any remaining dangerous patterns
        dangerous_patterns = ["..", "~", "$", "`", "|", ";", "&"]
        for pattern in dangerous_patterns:
            filename = filename.replace(pattern, "")

        # Ensure it only contains safe characters
        filename = re.sub(r"[^a-zA-Z0-9_.-]", "", filename)

        return filename

    def _get_file_path(self, year: str) -> str:
        """Get the file path for a specific school year with security validation.

        Args:
            year: School year in format "YYYY_YYYY"

        Returns:
            Full path to the JSON file

        Raises:
            ValueError: If year format is invalid or contains unsafe characters
        """
        if not self._validate_year_format(year):
            raise ValueError(f"Invalid year format: '{year}'. Expected format: YYYY_YYYY (e.g., 2023_2024)")

        # Additional sanitization as defense in depth
        safe_year = self._sanitize_filename(year)

        # Double-check that sanitization didn't break the year format
        if not self._validate_year_format(safe_year):
            raise ValueError(f"Year format became invalid after sanitization: '{safe_year}'")

        file_path = os.path.join(self.data_dir, f"{safe_year}.json")

        # Final security check: ensure the resolved path is within data_dir
        resolved_path = os.path.abspath(file_path)
        data_dir_abs = os.path.abspath(self.data_dir)

        if not resolved_path.startswith(data_dir_abs + os.sep) and resolved_path != data_dir_abs:
            raise ValueError(f"File path escapes data directory: '{resolved_path}'")

        return file_path

    def load(self, year: str) -> dict[str, Any] | None:
        """Load data for a specific school year.

        Args:
            year: School year in format "YYYY_YYYY"

        Returns:
            Dictionary containing all data for the year, or None if file doesn't exist
        """
        try:
            file_path = self._get_file_path(year)
        except ValueError as e:
            logger.error(f"Invalid year format for loading: {e}")
            return None

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                # Basic validation of loaded data structure
                if not isinstance(data, dict):
                    logger.error(f"Invalid data format in {year}.json - expected dictionary")
                    return None
                return data
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Error loading data for {year}: {e}")
            return None

    def save(self, year: str, data: dict[str, Any]) -> bool:
        """Save data for a specific school year.

        Args:
            year: School year in format "YYYY_YYYY"
            data: Dictionary containing all data to save

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_file_path(year)
        except ValueError as e:
            logger.error(f"Invalid year format for saving: {e}")
            return False

        # Validate data structure before saving
        if not isinstance(data, dict):
            logger.error(f"Invalid data type for saving: expected dict, got {type(data)}")
            return False

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (OSError, TypeError) as e:
            logger.error(f"Error saving data for {year}: {e}")
            return False

    def get_default_data_structure(self) -> dict[str, Any]:
        """Get the default data structure for a new year.

        Returns:
            Dictionary with default empty structure
        """
        # Load custom default weights if they exist
        default_weights = {
            "preferred_teacher": 5,
            "priority_early_slot": 3,
            "tandem_fulfilled": 4,
            "teacher_pause_respected": 1,
            "preserve_existing_plan": 10,
        }

        try:
            import json

            config_file = "default_weights.json"
            if os.path.exists(config_file):
                with open(config_file, encoding="utf-8") as f:
                    custom_weights = json.load(f)
                    # Merge with defaults, prioritizing custom values
                    default_weights.update(custom_weights)
                    logger.debug("Loaded custom default weights")
        except Exception as e:
            logger.warning(f"Failed to load custom default weights: {e}")

        return {
            "teachers": {},
            "children": {},
            "tandems": {},
            "weights": default_weights,
            "schedule_results": [],  # List of saved schedule results with timestamps
            "current_schedule_id": None,  # ID of currently selected schedule result
        }

    def exists(self, year: str) -> bool:
        """Check if data file exists for a specific year.

        Args:
            year: School year in format "YYYY_YYYY"

        Returns:
            True if file exists, False otherwise
        """
        try:
            return os.path.exists(self._get_file_path(year))
        except ValueError:
            return False

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
        try:
            file_path = self._get_file_path(year)
        except ValueError as e:
            logger.error(f"Invalid year format for deletion: {e}")
            return False

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except OSError as e:
            logger.error(f"Error deleting data for {year}: {e}")
            return False

    def save_schedule_result(
        self,
        year: str,
        schedule_data: dict[str, Any],
        violations: list[str],
        weights_used: dict[str, Any],
        optimization_info: dict[str, Any] = None,
    ) -> str:
        """Save a new schedule result with timestamp.

        Args:
            year: School year in format "YYYY_YYYY"
            schedule_data: The computed schedule assignments
            violations: List of constraint violations
            weights_used: The optimization weights used for this computation
            optimization_info: Additional info (solver status, runtime, etc.)

        Returns:
            The ID of the saved schedule result
        """
        data = self.load(year) or self.get_default_data_structure()

        # Generate unique ID based on timestamp
        timestamp = datetime.now()
        schedule_id = timestamp.strftime("%Y%m%d_%H%M%S")

        # Create schedule result entry
        schedule_result = {
            "id": schedule_id,
            "timestamp": timestamp.isoformat(),
            "readable_timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "schedule": schedule_data,
            "violations": violations,
            "weights_used": weights_used.copy(),
            "optimization_info": optimization_info or {},
            "description": f"Schedule computed on {timestamp.strftime('%Y-%m-%d at %H:%M')}",
        }

        # Add to results list (most recent first)
        if "schedule_results" not in data:
            data["schedule_results"] = []
        data["schedule_results"].insert(0, schedule_result)

        # Set as current schedule
        data["current_schedule_id"] = schedule_id

        # Save to file
        success = self.save(year, data)
        if success:
            logger.info(f"Saved schedule result {schedule_id} for year {year}")
        else:
            logger.error(f"Failed to save schedule result {schedule_id} for year {year}")

        return schedule_id

    def get_schedule_results(self, year: str) -> list[dict[str, Any]]:
        """Get all saved schedule results for a year.

        Args:
            year: School year in format "YYYY_YYYY"

        Returns:
            List of schedule results, most recent first
        """
        data = self.load(year)
        if not data:
            return []
        return data.get("schedule_results", [])

    def get_schedule_result_by_id(self, year: str, schedule_id: str) -> dict[str, Any] | None:
        """Get a specific schedule result by ID.

        Args:
            year: School year in format "YYYY_YYYY"
            schedule_id: ID of the schedule result

        Returns:
            Schedule result data or None if not found
        """
        results = self.get_schedule_results(year)
        for result in results:
            if result.get("id") == schedule_id:
                return result
        return None

    def set_current_schedule(self, year: str, schedule_id: str) -> bool:
        """Set the currently active schedule result.

        Args:
            year: School year in format "YYYY_YYYY"
            schedule_id: ID of the schedule result to set as current

        Returns:
            True if successful, False otherwise
        """
        data = self.load(year)
        if not data:
            return False

        # Verify the schedule exists
        if not self.get_schedule_result_by_id(year, schedule_id):
            logger.error(f"Schedule result {schedule_id} not found for year {year}")
            return False

        data["current_schedule_id"] = schedule_id
        success = self.save(year, data)
        if success:
            logger.info(f"Set current schedule to {schedule_id} for year {year}")
        return success

    def get_current_schedule_result(self, year: str) -> dict[str, Any] | None:
        """Get the currently selected schedule result.

        Args:
            year: School year in format "YYYY_YYYY"

        Returns:
            Current schedule result data or None if none selected
        """
        data = self.load(year)
        if not data:
            return None

        current_id = data.get("current_schedule_id")
        if not current_id:
            return None

        return self.get_schedule_result_by_id(year, current_id)

    def delete_schedule_result(self, year: str, schedule_id: str) -> bool:
        """Delete a specific schedule result.

        Args:
            year: School year in format "YYYY_YYYY"
            schedule_id: ID of the schedule result to delete

        Returns:
            True if successful, False otherwise
        """
        data = self.load(year)
        if not data or "schedule_results" not in data:
            return False

        # Find and remove the result
        results = data["schedule_results"]
        original_count = len(results)
        data["schedule_results"] = [r for r in results if r.get("id") != schedule_id]

        if len(data["schedule_results"]) == original_count:
            logger.warning(f"Schedule result {schedule_id} not found for deletion")
            return False

        # If we deleted the current schedule, clear the current selection
        if data.get("current_schedule_id") == schedule_id:
            data["current_schedule_id"] = None

        success = self.save(year, data)
        if success:
            logger.info(f"Deleted schedule result {schedule_id} for year {year}")
        return success
