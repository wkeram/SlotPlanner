"""Settings management event handlers.

This module contains handlers for application settings functionality
including optimization weights and configuration management.
"""

from PySide6.QtWidgets import QWidget, QSpinBox, QComboBox, QMessageBox
from app.config.logging_config import get_logger
from app.storage import Storage
from app.validation import Validator
from .base_handler import BaseHandler

logger = get_logger(__name__)


def settings_reset_weights(window: QWidget, storage: Storage) -> None:
    """Reset optimization weights to default values.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _reset_weights():
        # Default weights from README.md
        defaults = {
            "spinPreferredTeacher": 5,
            "spinEarlySlot": 3,
            "spinTandemFulfilled": 4,
            "spinTeacherBreak": 1,
            "spinPreserveExisting": 10,
        }

        reset_count = 0
        for widget_name, value in defaults.items():
            spin_box = window.ui.findChild(QSpinBox, widget_name)
            if spin_box:
                spin_box.setValue(value)
                reset_count += 1

        logger.info(f"Reset {reset_count} weight settings to defaults")

        if reset_count > 0:
            BaseHandler.show_info(
                window, "Settings Reset", f"Reset {reset_count} optimization weights to default values."
            )
        else:
            logger.warning("No weight spinboxes found to reset")

    BaseHandler.safe_execute(_reset_weights, parent=window)


def settings_save_weights(window: QWidget, storage: Storage) -> None:
    """Save optimization weights to storage.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _save_weights():
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        data = storage.load(year) or storage.get_default_data_structure()

        # Collect current weight values
        weights = {}
        weight_widgets = {
            "preferred_teacher": "spinPreferredTeacher",
            "priority_early_slot": "spinEarlySlot",
            "tandem_fulfilled": "spinTandemFulfilled",
            "teacher_pause_respected": "spinTeacherBreak",
            "preserve_existing_plan": "spinPreserveExisting",
        }

        saved_count = 0
        for key, widget_name in weight_widgets.items():
            spin_box = window.ui.findChild(QSpinBox, widget_name)
            if spin_box:
                weights[key] = spin_box.value()
                saved_count += 1

        # Validate weights before saving
        weight_validation = Validator.validate_optimization_weights(weights)
        if not weight_validation.is_valid:
            from app.utils import show_error

            show_error(f"Weight validation failed:\n\n{weight_validation.get_error_message()}", window)
            return

        # Show warnings if any
        if weight_validation.has_warnings:
            reply = QMessageBox.question(
                window,
                "Weight Warnings",
                f"The following warnings were found:\n\n{weight_validation.get_warning_message()}\n\nDo you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply != QMessageBox.Yes:
                return

        data["weights"] = weights
        success = storage.save(year, data)

        if success and saved_count > 0:
            logger.info(f"Successfully saved {saved_count} weight settings for year {year}")
            BaseHandler.show_info(window, "Settings Saved", f"Saved {saved_count} optimization weights successfully.")
        elif success:
            logger.warning("No weights were found to save")
            BaseHandler.show_info(window, "Settings Saved", "Settings saved, but no weight values were found.")
        else:
            logger.error(f"Failed to save weight settings for year {year}")

    BaseHandler.safe_execute(_save_weights, parent=window)
