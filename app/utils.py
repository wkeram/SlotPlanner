"""Utility functions for the SlotPlanner application.

This module provides utility functions for translations and error message display.
"""

import json
from typing import Optional
from PySide6.QtWidgets import QMessageBox, QWidget
from app.config.logging_config import get_logger

logger = get_logger(__name__)


def get_translations(message_key: str) -> str:
    """Get translated text for a given message key.

    Args:
        message_key (str): The key to look up in the translations file

    Returns:
        str: The translated text for the given key
    """
    # Default translations for key messages
    default_translations = {
        "invalid_teacher_name": "Invalid teacher name. Please enter a valid name.",
        "invalid_time_range": "Invalid time range. Time slots must be at least 45 minutes and end time must be after start time.",
    }

    language_key = "en"  # Default language
    try:
        with open("app/config/translations.json", "r", encoding="utf-8") as f:
            translations = json.load(f)
            return translations[language_key][message_key]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        logger.warning(f"Translation not found for '{message_key}'. Using default.")
        return default_translations.get(message_key, f"Missing translation: {message_key}")


def show_error(message: str, parent: Optional["QWidget"] = None) -> None:
    """Display an error message dialog in a pop-up.

    Args:
        message (str): The error message to display
        parent (QWidget, optional): Parent widget for the error dialog
    """
    QMessageBox.critical(parent, "Error", message)
