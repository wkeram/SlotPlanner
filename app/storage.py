"""Data storage and persistence module for SlotPlanner.

This module handles JSON-based data persistence for teachers, children,
tandems, optimization weights, and scheduling results.
"""

import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
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
                with open(config_file, "r", encoding="utf-8") as f:
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

    def save_schedule_result(
        self,
        year: str,
        schedule_data: Dict[str, Any],
        violations: List[str],
        weights_used: Dict[str, Any],
        optimization_info: Dict[str, Any] = None,
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

    def get_schedule_results(self, year: str) -> List[Dict[str, Any]]:
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

    def get_schedule_result_by_id(self, year: str, schedule_id: str) -> Optional[Dict[str, Any]]:
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

    def get_current_schedule_result(self, year: str) -> Optional[Dict[str, Any]]:
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
