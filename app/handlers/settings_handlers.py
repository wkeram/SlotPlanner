"""Settings management event handlers.

This module contains handlers for application settings functionality
including optimization weights and configuration management.
"""

import os
from PySide6.QtWidgets import QWidget, QSpinBox, QSlider, QLabel, QComboBox, QMessageBox, QLineEdit, QFileDialog
from app.config.logging_config import get_logger
from app.storage import Storage
from app.validation import Validator
from .base_handler import BaseHandler

logger = get_logger(__name__)


def _get_current_default_weights() -> dict:
    """Get current default weights from file or fallback to hardcoded defaults.

    Returns:
        Dictionary with current default weights
    """
    try:
        import json

        config_file = "default_weights.json"
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load custom default weights: {e}")

    # Fallback to hardcoded defaults
    return {
        "preferred_teacher": 5,
        "priority_early_slot": 3,
        "tandem_fulfilled": 4,
        "teacher_pause_respected": 1,
        "preserve_existing_plan": 10,
    }


def settings_reset_weights(window: QWidget, storage: Storage) -> None:
    """Reset optimization weights to default values.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _reset_weights():
        # Load current default weights (may be custom defaults)
        current_defaults = _get_current_default_weights()

        defaults = {
            "sliderPreferredTeacher": current_defaults.get("preferred_teacher", 5),
            "sliderEarlySlot": current_defaults.get("priority_early_slot", 3),
            "sliderTandemFulfilled": current_defaults.get("tandem_fulfilled", 4),
            "sliderTeacherBreak": current_defaults.get("teacher_pause_respected", 1),
            "sliderPreserveExisting": current_defaults.get("preserve_existing_plan", 10),
        }

        reset_count = 0
        for widget_name, value in defaults.items():
            slider = window.ui.findChild(QSlider, widget_name)
            if slider:
                slider.setValue(value)
                reset_count += 1

                # Update the corresponding label
                label_name = widget_name.replace("slider", "label") + "Value"
                label = window.ui.findChild(QLabel, label_name)
                if label:
                    label.setText(f"Value: {value} (Default: {value}, Range: 0-20)")

        logger.info(f"Reset {reset_count} weight settings to defaults")

        if reset_count > 0:
            BaseHandler.show_info(
                window, "Settings Reset", f"Reset {reset_count} optimization weights to default values."
            )
        else:
            logger.warning("No weight sliders found to reset")

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
            "preferred_teacher": "sliderPreferredTeacher",
            "priority_early_slot": "sliderEarlySlot",
            "tandem_fulfilled": "sliderTandemFulfilled",
            "teacher_pause_respected": "sliderTeacherBreak",
            "preserve_existing_plan": "sliderPreserveExisting",
        }

        saved_count = 0
        for key, widget_name in weight_widgets.items():
            slider = window.ui.findChild(QSlider, widget_name)
            if slider:
                weights[key] = slider.value()
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


def settings_select_data_path(window: QWidget, storage: Storage) -> None:
    """Select directory for data storage.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _select_data_path():
        current_path = storage.data_dir

        selected_path = QFileDialog.getExistingDirectory(
            window,
            "Select Data Storage Directory",
            current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if selected_path:
            # Update the storage path
            old_path = storage.data_dir
            storage.data_dir = selected_path

            # Update the UI
            line_edit = window.ui.findChild(QLineEdit, "lineEditDataPath")
            if line_edit:
                line_edit.setText(selected_path)

            # Save the new path to settings
            _save_path_settings(window, storage)

            logger.info(f"Changed data storage path from {old_path} to {selected_path}")
            BaseHandler.show_info(
                window,
                "Path Updated",
                f"Data storage path changed to:\n{selected_path}\n\nExisting data will remain in the previous location.",
            )

    BaseHandler.safe_execute(_select_data_path, parent=window)


def settings_select_export_path(window: QWidget, storage: Storage) -> None:
    """Select directory for PDF exports.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _select_export_path():
        # Get current export path (stored in storage or use default)
        current_path = getattr(storage, "export_dir", "exports")

        selected_path = QFileDialog.getExistingDirectory(
            window,
            "Select PDF Export Directory",
            current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if selected_path:
            # Update the export path
            old_path = getattr(storage, "export_dir", "exports")
            storage.export_dir = selected_path

            # Update the UI
            line_edit = window.ui.findChild(QLineEdit, "lineEditExportPath")
            if line_edit:
                line_edit.setText(selected_path)

            # Save the new path to settings
            _save_path_settings(window, storage)

            logger.info(f"Changed export path from {old_path} to {selected_path}")
            BaseHandler.show_info(window, "Path Updated", f"PDF export path changed to:\n{selected_path}")

    BaseHandler.safe_execute(_select_export_path, parent=window)


def settings_reset_paths(window: QWidget, storage: Storage) -> None:
    """Reset storage paths to absolute defaults.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _reset_paths():
        # Reset to absolute default paths
        default_data = os.path.abspath("data")
        default_export = os.path.abspath("exports")

        storage.data_dir = default_data
        storage.export_dir = default_export

        # Ensure directories exist
        storage._ensure_data_dir()
        storage._ensure_export_dir()

        # Update UI
        data_line = window.ui.findChild(QLineEdit, "lineEditDataPath")
        if data_line:
            data_line.setText(default_data)

        export_line = window.ui.findChild(QLineEdit, "lineEditExportPath")
        if export_line:
            export_line.setText(default_export)

        # Save to settings
        _save_path_settings(window, storage)

        logger.info(f"Reset storage paths to absolute defaults: {default_data}, {default_export}")
        BaseHandler.show_info(
            window,
            "Paths Reset to Defaults",
            f"Storage paths reset to absolute defaults:\n\nData: {default_data}\n\nExports: {default_export}",
        )

    BaseHandler.safe_execute(_reset_paths, parent=window)


def _save_path_settings(window: QWidget, storage: Storage) -> None:
    """Save path settings to a configuration file.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    import json

    try:
        config_file = "app_config.json"
        config = {"data_path": storage.data_dir, "export_path": getattr(storage, "export_dir", "exports")}

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        logger.debug(f"Saved path settings to {config_file}")

    except Exception as e:
        logger.error(f"Failed to save path settings: {e}")


def load_path_settings(storage: Storage) -> None:
    """Load path settings from configuration file.

    Args:
        storage: Storage instance to update with loaded paths
    """
    import json

    try:
        config_file = "app_config.json"
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            if "data_path" in config:
                storage.data_dir = os.path.abspath(config["data_path"])
            if "export_path" in config:
                storage.export_dir = os.path.abspath(config["export_path"])

            logger.debug(f"Loaded path settings from {config_file}")
        else:
            # No config file exists, ensure we use absolute defaults
            storage.data_dir = os.path.abspath(storage.data_dir)
            storage.export_dir = os.path.abspath(storage.export_dir)
            logger.debug("No config file found, using absolute default paths")

    except Exception as e:
        logger.error(f"Failed to load path settings: {e}")
        # Ensure absolute paths even on error
        storage.data_dir = os.path.abspath(storage.data_dir)
        storage.export_dir = os.path.abspath(storage.export_dir)


def settings_load_paths_into_ui(window: QWidget, storage: Storage) -> None:
    """Load current storage paths into the UI.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    data_line = window.ui.findChild(QLineEdit, "lineEditDataPath")
    if data_line:
        data_line.setText(storage.data_dir)

    export_line = window.ui.findChild(QLineEdit, "lineEditExportPath")
    if export_line:
        export_path = getattr(storage, "export_dir", "exports")
        export_line.setText(export_path)

    logger.debug("Loaded storage paths into UI")


def settings_save_weights_as_default(window: QWidget, storage: Storage) -> None:
    """Save current weights as default values.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _save_as_default():
        # Collect current weight values from sliders
        weight_widgets = {
            "preferred_teacher": "sliderPreferredTeacher",
            "priority_early_slot": "sliderEarlySlot",
            "tandem_fulfilled": "sliderTandemFulfilled",
            "teacher_pause_respected": "sliderTeacherBreak",
            "preserve_existing_plan": "sliderPreserveExisting",
        }

        current_weights = {}
        collected_count = 0

        for key, widget_name in weight_widgets.items():
            slider = window.ui.findChild(QSlider, widget_name)
            if slider:
                current_weights[key] = slider.value()
                collected_count += 1

        if collected_count == 0:
            logger.warning("No weight sliders found to save as defaults")
            BaseHandler.show_info(window, "No Weights Found", "No weight sliders were found.")
            return

        # Validate weights before saving
        weight_validation = Validator.validate_optimization_weights(current_weights)
        if not weight_validation.is_valid:
            from app.utils import show_error

            show_error(f"Weight validation failed:\\n\\n{weight_validation.get_error_message()}", window)
            return

        # Show warnings if any
        if weight_validation.has_warnings:
            reply = QMessageBox.question(
                window,
                "Weight Warnings",
                f"The following warnings were found:\\n\\n{weight_validation.get_warning_message()}\\n\\nDo you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply != QMessageBox.Yes:
                return

        # Save to defaults configuration file
        try:
            import json

            config_file = "default_weights.json"

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(current_weights, f, indent=2)

            logger.info(f"Saved {collected_count} weights as defaults to {config_file}")

            # Update storage's default structure
            storage._default_weights = current_weights.copy()

            # Immediately update all slider labels to show new defaults
            _update_slider_labels_with_new_defaults(window, current_weights)

            BaseHandler.show_info(
                window,
                "Defaults Saved",
                f"Successfully saved {collected_count} optimization weights as defaults.\\n\\nThese will be used for new projects and are now active.",
            )

        except Exception as e:
            logger.error(f"Failed to save default weights: {e}")
            from app.utils import show_error

            show_error(f"Failed to save default weights:\\n\\n{str(e)}", window)

    BaseHandler.safe_execute(_save_as_default, parent=window)


def _update_slider_labels_with_new_defaults(window: QWidget, new_defaults: dict) -> None:
    """Update all slider labels to reflect new default values.

    Args:
        window: Main application window instance
        new_defaults: Dictionary with new default values
    """
    weight_to_slider = {
        "preferred_teacher": ("sliderPreferredTeacher", "labelPreferredTeacherValue"),
        "priority_early_slot": ("sliderEarlySlot", "labelEarlySlotValue"),
        "tandem_fulfilled": ("sliderTandemFulfilled", "labelTandemFulfilledValue"),
        "teacher_pause_respected": ("sliderTeacherBreak", "labelTeacherBreakValue"),
        "preserve_existing_plan": ("sliderPreserveExisting", "labelPreserveExistingValue"),
    }

    for weight_key, (slider_name, label_name) in weight_to_slider.items():
        slider = window.ui.findChild(QSlider, slider_name)
        label = window.ui.findChild(QLabel, label_name)

        if slider and label:
            current_value = slider.value()
            new_default = new_defaults.get(weight_key, current_value)
            label.setText(f"Value: {current_value} (Default: {new_default}, Range: 0-20)")


def settings_load_weights_into_ui(window: QWidget, storage: Storage) -> None:
    """Load saved weights into the UI sliders.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    data = storage.load(year)

    if not data or "weights" not in data:
        # Use defaults if no saved data
        data = storage.get_default_data_structure()

    weights = data["weights"]

    # Map weights to sliders
    weight_to_slider = {
        "preferred_teacher": ("sliderPreferredTeacher", "labelPreferredTeacherValue", 5),
        "priority_early_slot": ("sliderEarlySlot", "labelEarlySlotValue", 3),
        "tandem_fulfilled": ("sliderTandemFulfilled", "labelTandemFulfilledValue", 4),
        "teacher_pause_respected": ("sliderTeacherBreak", "labelTeacherBreakValue", 1),
        "preserve_existing_plan": ("sliderPreserveExisting", "labelPreserveExistingValue", 10),
    }

    loaded_count = 0
    for weight_key, (slider_name, label_name, default_val) in weight_to_slider.items():
        value = weights.get(weight_key, default_val)

        slider = window.ui.findChild(QSlider, slider_name)
        if slider:
            slider.setValue(value)
            loaded_count += 1

            # Update the label
            label = window.ui.findChild(QLabel, label_name)
            if label:
                label.setText(f"Value: {value} (Default: {default_val}, Range: 0-20)")

    if loaded_count > 0:
        logger.debug(f"Loaded {loaded_count} weight values into UI for year {year}")
    else:
        logger.warning("No weight sliders found to load values into")


def settings_language_changed(window: QWidget, storage: Storage) -> None:
    """Handle language selection change.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    def _change_language():
        combo_language = window.ui.findChild(QComboBox, "comboLanguage")
        if not combo_language:
            logger.warning("Language combo box not found")
            return
        
        selected_text = combo_language.currentText()
        
        # Map display names to language codes
        language_map = {
            "Deutsch": "de",
            "English": "en"
        }
        
        language_code = language_map.get(selected_text)
        if not language_code:
            logger.warning(f"Unknown language selected: {selected_text}")
            return
        
        # Update the language
        from app.utils import set_language, get_current_language
        current_lang = get_current_language()
        
        if current_lang != language_code:
            set_language(language_code)
            
            # Update UI with new language immediately
            if hasattr(window, 'update_ui_translations'):
                window.update_ui_translations()
            
            # Show success message in new language
            from app.utils import get_translations
            BaseHandler.show_info(
                window, 
                get_translations("language_changed"),
                f"Language changed to {selected_text}.\n\nInterface has been updated to the new language."
            )
            logger.info(f"Language changed from {current_lang} to {language_code}")
    
    BaseHandler.safe_execute(_change_language, parent=window)


def settings_load_language_into_ui(window: QWidget, storage: Storage) -> None:
    """Load current language setting into the UI dropdown.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    combo_language = window.ui.findChild(QComboBox, "comboLanguage")
    if not combo_language:
        logger.warning("Language combo box not found")
        return
    
    from app.utils import get_current_language
    current_lang = get_current_language()
    
    # Map language codes to display names
    display_map = {
        "de": "Deutsch", 
        "en": "English"
    }
    
    display_name = display_map.get(current_lang, "Deutsch")  # Default to German
    
    # Set the combo box to the current language
    index = combo_language.findText(display_name)
    if index >= 0:
        combo_language.setCurrentIndex(index)
        logger.debug(f"Set language dropdown to {display_name}")
    else:
        logger.warning(f"Could not find {display_name} in language dropdown")
