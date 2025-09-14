"""Tandem management event handlers.

This module contains all handlers for tandem-related functionality
including adding, editing, and deleting tandems.
"""

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QComboBox, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget, QWidget

from app.config.logging_config import get_logger
from app.storage import Storage
from app.ui_teachers import refresh_children_table, refresh_tandems_table, refresh_teacher_table
from app.utils import get_translations, show_error
from app.validation import Validator

from .base_handler import BaseHandler

logger = get_logger(__name__)


def _setup_tandem_dialog_translations(dialog: QWidget) -> None:
    """Set up translations for tandem dialog UI elements.

    Args:
        dialog: Tandem dialog widget
    """
    from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton

    from app.utils import get_current_language

    logger.debug(f"Setting up tandem dialog translations for language: {get_current_language()}")

    # Update button text
    save_btn = dialog.findChild(QPushButton, "buttonOk")
    if save_btn:
        save_btn.setText(get_translations("save_tandem"))

    cancel_btn = dialog.findChild(QPushButton, "buttonCancel")
    if cancel_btn:
        cancel_btn.setText(get_translations("cancel"))

    # Update labels
    description_label = dialog.findChild(QLabel, "descriptionLabel")
    if description_label:
        description_label.setText(get_translations("tandem_description"))
        logger.debug(f"Updated tandem description label with text: {get_translations('tandem_description')[:50]}...")
    else:
        logger.warning("descriptionLabel not found in tandem dialog")

    # Update note label
    note_label = dialog.findChild(QLabel, "noteLabel")
    if note_label:
        note_label.setText(get_translations("tandem_note"))
        logger.debug("Updated tandem note label")
    else:
        logger.warning("noteLabel not found in tandem dialog")

    name_label = dialog.findChild(QLabel, "tandemNameLabel")
    if name_label:
        name_label.setText(get_translations("tandem_name_label"))

    child1_label = dialog.findChild(QLabel, "child1Label")
    if child1_label:
        child1_label.setText(get_translations("first_child"))

    child2_label = dialog.findChild(QLabel, "child2Label")
    if child2_label:
        child2_label.setText(get_translations("second_child"))

    priority_label = dialog.findChild(QLabel, "priorityLabel")
    if priority_label:
        priority_label.setText(get_translations("priority_label"))

    # Update line edit placeholder
    name_line_edit = dialog.findChild(QLineEdit, "tandemNameLineEdit")
    if name_line_edit:
        name_line_edit.setPlaceholderText(get_translations("tandem_name_placeholder"))

    # Update combo box placeholders
    child1_combo = dialog.findChild(QComboBox, "child1ComboBox")
    if child1_combo:
        child1_combo.setPlaceholderText(get_translations("select_first_child"))

    child2_combo = dialog.findChild(QComboBox, "child2ComboBox")
    if child2_combo:
        child2_combo.setPlaceholderText(get_translations("select_second_child"))


def tandem_open_add_dialog(window: QWidget, storage: Storage) -> None:
    """Open the dialog for adding a new tandem.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _open_dialog():
        logger.info("Opening add tandem dialog")

        loader = QUiLoader()
        file = QFile("app/ui/add_tandem.ui")

        if not file.open(QFile.ReadOnly):
            error_msg = f"Cannot open add_tandem.ui: {file.errorString()}"
            logger.error(error_msg)
            show_error(error_msg, window)
            return

        add_tandem_dialog = loader.load(file, window)
        file.close()

        if not add_tandem_dialog:
            error_msg = "Failed to load add_tandem.ui - loader returned None"
            logger.error(error_msg)
            show_error(error_msg, window)
            return

        add_tandem_dialog.setWindowTitle(get_translations("add_tandem"))
        logger.debug("Tandem dialog UI loaded successfully")

        # Set up dialog UI translations
        _setup_tandem_dialog_translations(add_tandem_dialog)

        # Setup dialog functionality
        _setup_tandem_dialog(add_tandem_dialog, window, storage)

        # Show the dialog
        logger.debug("Showing tandem dialog")
        result = add_tandem_dialog.exec()
        logger.debug(f"Tandem dialog closed with result: {result}")

        # Proper cleanup to prevent memory leaks
        BaseHandler.cleanup_widget(add_tandem_dialog)

    BaseHandler.safe_execute(_open_dialog, parent=window)


def tandem_edit_selected(window: QWidget, storage: Storage) -> None:
    """Edit the selected tandem.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _edit_tandem():
        table = window.ui.findChild(QTableWidget, "tableTandems")
        if not table:
            show_error(get_translations("error_tandems_table_not_found"), window)
            return

        selected_row = table.currentRow()
        if selected_row < 0:
            show_error(get_translations("error_please_select_tandem_edit"), window)
            return

        # Get tandem name from first column
        name_item = table.item(selected_row, 0)
        if not name_item:
            show_error(get_translations("error_could_not_get_tandem_name"), window)
            return

        tandem_name = name_item.text()
        logger.info(f"Opening edit dialog for tandem: {tandem_name}")

        # Load tandem data
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        data = storage.load(year) or storage.get_default_data_structure()
        tandem_data = data.get("tandems", {}).get(tandem_name)

        if not tandem_data:
            show_error(get_translations("error_tandem_data_not_found").format(name=tandem_name), window)
            return

        # Open edit dialog with pre-populated data
        _open_tandem_edit_dialog(window, storage, tandem_name, tandem_data)

    BaseHandler.safe_execute(_edit_tandem, parent=window)


def tandem_delete_selected(window: QWidget, storage: Storage) -> None:
    """Delete the selected tandem.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _delete_tandem():
        table = window.ui.findChild(QTableWidget, "tableTandems")
        if not table:
            show_error(get_translations("error_tandems_table_not_found"), window)
            return

        selected_row = table.currentRow()
        if selected_row < 0:
            show_error(get_translations("error_please_select_tandem_delete"), window)
            return

        # Get tandem name from first column
        name_item = table.item(selected_row, 0)
        if not name_item:
            show_error(get_translations("error_could_not_get_tandem_name"), window)
            return

        tandem_name = name_item.text()

        # Confirm deletion
        reply = QMessageBox.question(
            window,
            "Delete Tandem",
            f"Are you sure you want to delete tandem '{tandem_name}'?\n\n"
            f"This will break the pairing but the individual children will remain.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # Delete tandem
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        data = storage.load(year) or storage.get_default_data_structure()

        if tandem_name in data.get("tandems", {}):
            del data["tandems"][tandem_name]
            logger.info(f"Deleted tandem: {tandem_name}")

            # Save and refresh
            success = storage.save(year, data)
            if success:
                logger.info(f"Successfully deleted tandem: {tandem_name}")

                # Refresh all tables
                refresh_teacher_table(window.ui, data)
                refresh_children_table(window.ui, data)
                refresh_tandems_table(window.ui, data)

                BaseHandler.show_info(
                    window, "Tandem Deleted", f"Tandem '{tandem_name}' has been deleted successfully."
                )
            else:
                logger.error(f"Failed to delete tandem: {tandem_name}")
                show_error(get_translations("error_failed_delete_tandem").format(name=tandem_name), window)
        else:
            show_error(get_translations("error_tandem_not_found_in_data").format(name=tandem_name), window)

    BaseHandler.safe_execute(_delete_tandem, parent=window)


def _setup_tandem_dialog(dialog: QWidget, window: QWidget, storage: Storage) -> None:
    """Setup the tandem dialog with buttons and data population.

    Args:
        dialog: Tandem dialog instance
        window: Main window instance
        storage: Storage instance
    """
    # Find buttons with error checking
    button_save = dialog.findChild(QPushButton, "buttonOk")
    button_cancel = dialog.findChild(QPushButton, "buttonCancel")

    if not button_save:
        show_error(get_translations("error_save_button_not_found"), window)
        return
    if not button_cancel:
        show_error(get_translations("error_cancel_button_not_found"), window)
        return

    # Populate child dropdowns
    _populate_children_dropdowns(dialog, window, storage)

    # Connect buttons with safe error handling
    button_cancel.clicked.connect(dialog.reject)
    button_save.clicked.connect(
        lambda: BaseHandler.safe_execute(tandem_save_from_dialog, dialog, window, storage, parent=dialog)
    )

    logger.debug("Tandem dialog buttons connected")


def _populate_children_dropdowns(dialog: QWidget, window: QWidget, storage: Storage) -> None:
    """Populate the child dropdowns with available children.

    Args:
        dialog: Tandem dialog instance
        window: Main window instance
        storage: Storage instance
    """
    child1_combo = dialog.findChild(QComboBox, "child1ComboBox")
    child2_combo = dialog.findChild(QComboBox, "child2ComboBox")

    if not child1_combo or not child2_combo:
        logger.warning("Child dropdowns not found in dialog")
        return

    # Get current children data
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    data = storage.load(year) or storage.get_default_data_structure()
    children = data.get("children", {})

    # Clear and populate dropdowns
    child1_combo.clear()
    child2_combo.clear()

    # Add placeholder
    child1_combo.addItem("Select first child", "")
    child2_combo.addItem("Select second child", "")

    # Add children
    for child_name in sorted(children.keys()):
        child1_combo.addItem(child_name, child_name)
        child2_combo.addItem(child_name, child_name)

    logger.debug(f"Populated {len(children)} children in tandem dropdowns")


def tandem_save_from_dialog(dialog: QWidget, window: QWidget, storage: Storage) -> None:
    """Save tandem data from the add tandem dialog.

    Args:
        dialog: Tandem dialog instance
        window: Main window instance
        storage: Storage instance for data persistence
    """
    # Get tandem name
    name_field = dialog.findChild(QLineEdit, "tandemNameLineEdit")
    if not name_field:
        show_error(get_translations("error_tandem_name_field_not_found"), dialog)
        return

    tandem_name = name_field.text().strip()
    if not tandem_name:
        show_error(get_translations("error_please_enter_tandem_name"), dialog)
        return

    # Get child selections
    child1_combo = dialog.findChild(QComboBox, "child1ComboBox")
    child2_combo = dialog.findChild(QComboBox, "child2ComboBox")

    if not child1_combo or not child2_combo:
        show_error(get_translations("error_child_selection_dropdowns_not_found"), dialog)
        return

    child1_name = child1_combo.currentData()
    child2_name = child2_combo.currentData()

    if not child1_name or not child2_name:
        show_error(get_translations("error_please_select_both_children"), dialog)
        return

    # Get priority
    priority_spin = dialog.findChild(QSpinBox, "prioritySpinBox")
    priority = priority_spin.value() if priority_spin else 5

    # Validate tandem pair
    tandem_validation = Validator.validate_tandem_pair(child1_name, child2_name, priority)
    if not tandem_validation.is_valid:
        show_error(tandem_validation.get_error_message(), dialog)
        return

    # Show warnings if any
    if tandem_validation.has_warnings:
        reply = QMessageBox.question(
            dialog,
            "Tandem Warnings",
            f"The following warnings were found:\n\n{tandem_validation.get_warning_message()}\n\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return

    # Check for availability overlap
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    data = storage.load(year) or storage.get_default_data_structure()
    children = data.get("children", {})

    child1_data = children.get(child1_name, {})
    child2_data = children.get(child2_name, {})

    # Analyze availability overlap
    overlap_analysis = _analyze_availability_overlap(
        child1_data.get("availability", {}), child2_data.get("availability", {}), child1_name, child2_name
    )

    if not overlap_analysis["has_overlap"]:
        reply = QMessageBox.warning(
            dialog,
            "No Availability Overlap",
            f"Warning: {child1_name} and {child2_name} have no overlapping availability.\n\n"
            f"This tandem cannot be scheduled together.\n\n"
            f"Do you want to create the tandem anyway?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
    elif overlap_analysis["limited_overlap"]:
        QMessageBox.information(
            dialog,
            "Limited Availability Overlap",
            f"Note: {child1_name} and {child2_name} have limited overlapping availability:\n\n"
            f"{overlap_analysis['overlap_summary']}\n\n"
            f"The tandem will be created but scheduling options may be limited.",
        )

    # Check for existing tandems with these children
    existing_tandems = []
    for existing_name, existing_data in data.get("tandems", {}).items():
        if existing_data.get("child1") in [child1_name, child2_name] or existing_data.get("child2") in [
            child1_name,
            child2_name,
        ]:
            existing_tandems.append(existing_name)

    if existing_tandems:
        reply = QMessageBox.question(
            dialog,
            "Existing Tandems Found",
            f"The selected children are already in the following tandems:\n\n"
            f"• {chr(10).join(existing_tandems)}\n\n"
            f"Creating this tandem will create conflicting pairings.\n\n"
            f"Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

    # Save tandem data
    data.setdefault("tandems", {})[tandem_name] = {"child1": child1_name, "child2": child2_name, "priority": priority}

    success = storage.save(year, data)
    if success:
        logger.info(f"Successfully saved tandem: {tandem_name}")
        dialog.accept()

        # Refresh all tables
        refresh_teacher_table(window.ui, data)
        refresh_children_table(window.ui, data)
        refresh_tandems_table(window.ui, data)

        if hasattr(window, "feedback_manager") and window.feedback_manager:
            window.feedback_manager.show_success(get_translations("success_tandem_saved").format(name=tandem_name))
    else:
        logger.error(f"Failed to save tandem: {tandem_name}")
        show_error(get_translations("error_failed_save_tandem_data"), dialog)


def _analyze_availability_overlap(avail1: dict, avail2: dict, child1: str, child2: str) -> dict:
    """Analyze availability overlap between two children.

    Args:
        avail1: First child's availability
        avail2: Second child's availability
        child1: First child's name
        child2: Second child's name

    Returns:
        Dictionary with overlap analysis results
    """
    from datetime import datetime

    overlaps = []
    total_overlap_minutes = 0

    # Check each day for overlaps
    for day in ["Mo", "Di", "Mi", "Do", "Fr"]:
        day_slots1 = avail1.get(day, [])
        day_slots2 = avail2.get(day, [])

        if not day_slots1 or not day_slots2:
            continue

        # Find overlapping time ranges
        for start1, end1 in day_slots1:
            for start2, end2 in day_slots2:
                try:
                    start1_dt = datetime.strptime(start1, "%H:%M")
                    end1_dt = datetime.strptime(end1, "%H:%M")
                    start2_dt = datetime.strptime(start2, "%H:%M")
                    end2_dt = datetime.strptime(end2, "%H:%M")

                    # Calculate overlap
                    overlap_start = max(start1_dt, start2_dt)
                    overlap_end = min(end1_dt, end2_dt)

                    if overlap_start < overlap_end:
                        overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
                        if overlap_minutes >= 45:  # Minimum slot duration
                            overlaps.append(
                                {
                                    "day": day,
                                    "start": overlap_start.strftime("%H:%M"),
                                    "end": overlap_end.strftime("%H:%M"),
                                    "duration_minutes": overlap_minutes,
                                }
                            )
                            total_overlap_minutes += overlap_minutes

                except ValueError:
                    continue  # Skip malformed time strings

    has_overlap = len(overlaps) > 0
    limited_overlap = has_overlap and total_overlap_minutes < 180  # Less than 3 hours total

    overlap_summary = ""
    if overlaps:
        overlap_lines = []
        for overlap in overlaps:
            overlap_lines.append(
                f"{overlap['day']}: {overlap['start']}-{overlap['end']} " f"({int(overlap['duration_minutes'])} min)"
            )
        overlap_summary = "\n".join(overlap_lines)

    return {
        "has_overlap": has_overlap,
        "limited_overlap": limited_overlap,
        "total_overlap_minutes": total_overlap_minutes,
        "overlap_count": len(overlaps),
        "overlaps": overlaps,
        "overlap_summary": overlap_summary,
    }


def _open_tandem_edit_dialog(window: QWidget, storage: Storage, tandem_name: str, tandem_data: dict) -> None:
    """Open the tandem edit dialog with pre-populated data.

    Args:
        window: Main window instance
        storage: Storage instance
        tandem_name: Name of tandem to edit
        tandem_data: Existing tandem data
    """
    logger.info(f"Opening edit dialog for tandem: {tandem_name}")

    loader = QUiLoader()
    file = QFile("app/ui/add_tandem.ui")

    if not file.open(QFile.ReadOnly):
        error_msg = f"Cannot open add_tandem.ui: {file.errorString()}"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    edit_tandem_dialog = loader.load(file, window)
    file.close()

    if not edit_tandem_dialog:
        error_msg = "Failed to load add_tandem.ui - loader returned None"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    edit_tandem_dialog.setWindowTitle(f"{get_translations('edit_tandem')}: {tandem_name}")
    logger.debug("Tandem edit dialog UI loaded successfully")

    # Set up dialog UI translations
    _setup_tandem_dialog_translations(edit_tandem_dialog)

    # Pre-populate the dialog with existing data
    _populate_tandem_edit_dialog(edit_tandem_dialog, tandem_name, tandem_data, window, storage)

    # Setup dialog functionality for editing
    _setup_tandem_edit_dialog(edit_tandem_dialog, window, storage, tandem_name, tandem_data)

    # Show the dialog
    logger.debug("Showing tandem edit dialog")
    result = edit_tandem_dialog.exec()
    logger.debug(f"Tandem edit dialog closed with result: {result}")

    # Proper cleanup to prevent memory leaks
    BaseHandler.cleanup_widget(edit_tandem_dialog)


def _populate_tandem_edit_dialog(
    dialog: QWidget, tandem_name: str, tandem_data: dict, window: QWidget, storage: Storage
) -> None:
    """Pre-populate the tandem edit dialog with existing data.

    Args:
        dialog: Tandem edit dialog instance
        tandem_name: Name of the tandem being edited
        tandem_data: Existing tandem data
        window: Main window instance
        storage: Storage instance
    """
    logger.debug(f"Pre-populating tandem edit dialog for: {tandem_name}")

    # Set tandem name (enable editing with warning)
    name_field = dialog.findChild(QLineEdit, "tandemNameLineEdit")
    if name_field:
        name_field.setText(tandem_name)
        name_field.setReadOnly(False)  # Allow name changes during edit
        name_field.setStyleSheet("background-color: #fff7e6; border: 1px solid #ff9500;")  # Orange warning background
        name_field.setToolTip("⚠️ Changing the name will update all references to this tandem.")

    # Get current children for dropdowns
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    current_data = storage.load(year) or storage.get_default_data_structure()
    available_children = list(current_data.get("children", {}).keys())

    # Initialize child names with defaults
    child1_name = tandem_data.get("child1", "")
    child2_name = tandem_data.get("child2", "")

    logger.debug(f"Available children for tandem edit: {available_children}")
    logger.debug(f"Tandem children: child1='{child1_name}', child2='{child2_name}'")

    # If no children available, show warning
    if not available_children:
        logger.warning("No children available for tandem selection")
        # Add a placeholder to make it clear
        available_children = ["<No children available>"]

    # Ensure tandem children are included in the list even if not in current data
    # This handles cases where tandem references children that might have been renamed or removed
    all_children_for_dropdown = available_children[:]
    if child1_name and child1_name not in all_children_for_dropdown and child1_name != "<No children available>":
        all_children_for_dropdown.append(f"{child1_name} (missing)")
        logger.warning(f"Child1 '{child1_name}' not found in current children, adding as missing")

    if child2_name and child2_name not in all_children_for_dropdown and child2_name != "<No children available>":
        all_children_for_dropdown.append(f"{child2_name} (missing)")
        logger.warning(f"Child2 '{child2_name}' not found in current children, adding as missing")

    # Set child 1
    child1_combo = dialog.findChild(QComboBox, "child1ComboBox")
    if child1_combo:
        child1_combo.clear()
        child1_combo.addItems(all_children_for_dropdown)
        child1_combo.setEditable(True)  # Make it editable so users can type names

        # Try to select the current child1
        if child1_name:
            if child1_name in available_children:
                child1_combo.setCurrentText(child1_name)
            else:
                child1_combo.setCurrentText(f"{child1_name} (missing)")

        logger.debug(
            f"Child1 combo populated with {len(all_children_for_dropdown)} items, current: '{child1_combo.currentText()}'"
        )
    else:
        logger.error("child1ComboBox not found in tandem edit dialog")

    # Set child 2
    child2_combo = dialog.findChild(QComboBox, "child2ComboBox")
    if child2_combo:
        child2_combo.clear()
        child2_combo.addItems(all_children_for_dropdown)
        child2_combo.setEditable(True)  # Make it editable so users can type names

        # Try to select the current child2
        if child2_name:
            if child2_name in available_children:
                child2_combo.setCurrentText(child2_name)
            else:
                child2_combo.setCurrentText(f"{child2_name} (missing)")

        logger.debug(
            f"Child2 combo populated with {len(all_children_for_dropdown)} items, current: '{child2_combo.currentText()}'"
        )
    else:
        logger.error("child2ComboBox not found in tandem edit dialog")

    # Set priority
    priority_spin = dialog.findChild(QSpinBox, "prioritySpinBox")
    if priority_spin:
        priority = tandem_data.get("priority", 5)
        priority_spin.setValue(priority)

    logger.debug(
        f"Pre-populated tandem edit dialog: {child1_name} + {child2_name}, priority {tandem_data.get('priority', 5)}"
    )


def _setup_tandem_edit_dialog(
    dialog: QWidget, window: QWidget, storage: Storage, original_tandem_name: str, original_tandem_data: dict
) -> None:
    """Setup button connections for the tandem edit dialog.

    Args:
        dialog: Tandem edit dialog instance
        window: Main window instance
        storage: Storage instance
        original_tandem_name: The original name of the tandem being edited
        original_tandem_data: The original tandem data for comparison
    """
    # Find buttons with error checking
    button_save = dialog.findChild(QPushButton, "buttonOk")
    button_cancel = dialog.findChild(QPushButton, "buttonCancel")

    missing_buttons = []
    if not button_save:
        missing_buttons.append("buttonOk")
    if not button_cancel:
        missing_buttons.append("buttonCancel")

    if missing_buttons:
        error_msg = f"Missing buttons in tandem edit dialog: {', '.join(missing_buttons)}"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    # Connect buttons with safe error handling
    button_cancel.clicked.connect(dialog.reject)
    button_save.clicked.connect(
        lambda: BaseHandler.safe_execute(
            tandem_update_from_edit_dialog, dialog, window, storage, original_tandem_name, parent=dialog
        )
    )

    logger.debug("Tandem edit dialog buttons connected")


def tandem_update_from_edit_dialog(
    dialog: QWidget, window: QWidget, storage: Storage, original_tandem_name: str
) -> None:
    """Update tandem data from the edit dialog.

    Args:
        dialog: Tandem edit dialog instance
        window: Main window instance
        storage: Storage instance for data persistence
        original_tandem_name: Original name of the tandem being edited
    """
    logger.debug(f"Updating tandem data for: {original_tandem_name}")

    # Get the (possibly changed) tandem name
    name_field = dialog.findChild(QLineEdit, "tandemNameLineEdit")
    if not name_field:
        show_error(get_translations("error_tandem_name_field_not_found"), dialog)
        return

    new_tandem_name = name_field.text().strip()

    # Validate the name
    if not new_tandem_name:
        show_error(get_translations("error_tandem_name_cannot_be_empty"), dialog)
        return

    # Get current year and data
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    data = storage.load(year) or storage.get_default_data_structure()

    # Check for name conflicts (if name changed)
    name_changed = new_tandem_name != original_tandem_name
    if name_changed:
        if new_tandem_name in data.get("tandems", {}):
            show_error(get_translations("error_tandem_already_exists").format(name=new_tandem_name), dialog)
            return

        # Confirm name change with user
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            dialog,
            "Confirm Name Change",
            f"Are you sure you want to rename '{original_tandem_name}' to '{new_tandem_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

    # Get child selections
    child1_combo = dialog.findChild(QComboBox, "child1ComboBox")
    child2_combo = dialog.findChild(QComboBox, "child2ComboBox")
    priority_spin = dialog.findChild(QSpinBox, "prioritySpinBox")

    # Debug which fields are missing
    missing_fields = []
    if not child1_combo:
        missing_fields.append("child1ComboBox")
    if not child2_combo:
        missing_fields.append("child2ComboBox")
    if not priority_spin:
        missing_fields.append("prioritySpinBox")

    if missing_fields:
        error_msg = f"Required fields not found in dialog: {', '.join(missing_fields)}"
        logger.error(error_msg)
        show_error(error_msg, dialog)
        return

    child1_name = child1_combo.currentText()
    child2_name = child2_combo.currentText()
    priority = priority_spin.value()

    # Clean up "(missing)" suffix if present
    if child1_name.endswith(" (missing)"):
        child1_name = child1_name.replace(" (missing)", "")
    if child2_name.endswith(" (missing)"):
        child2_name = child2_name.replace(" (missing)", "")

    # Validate tandem pair
    tandem_validation = Validator.validate_tandem_pair(child1_name, child2_name, priority)
    if not tandem_validation.is_valid:
        show_error(
            get_translations("tandem_validation_failed_text").format(error=tandem_validation.get_error_message()),
            dialog,
        )
        return

    # Show warnings if any
    if tandem_validation.has_warnings:
        reply = QMessageBox.question(
            dialog,
            "Tandem Warnings",
            f"The following warnings were found:\n\n{tandem_validation.get_warning_message()}\n\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return

    # Handle name change (remove old entry if renamed)
    if name_changed and original_tandem_name in data.get("tandems", {}):
        del data["tandems"][original_tandem_name]
        logger.info(f"Tandem rename: {original_tandem_name} -> {new_tandem_name}")

    # Update tandem data
    data.setdefault("tandems", {})[new_tandem_name] = {
        "child1": child1_name,
        "child2": child2_name,
        "priority": priority,
    }

    # Save updated data
    success = storage.save(year, data)
    if success:
        action = "renamed and updated" if name_changed else "updated"
        logger.info(f"Successfully {action} tandem: {original_tandem_name} -> {new_tandem_name}")
        dialog.accept()

        # Refresh all tables
        refresh_teacher_table(window.ui, data)
        refresh_children_table(window.ui, data)
        refresh_tandems_table(window.ui, data)

        if hasattr(window, "feedback_manager") and window.feedback_manager:
            if name_changed:
                window.feedback_manager.show_success(
                    f"Tandem renamed from '{original_tandem_name}' to '{new_tandem_name}' successfully"
                )
            else:
                window.feedback_manager.show_success(
                    get_translations("success_tandem_updated").format(name=new_tandem_name)
                )
    else:
        logger.error(f"Failed to update tandem: {new_tandem_name}")
        show_error(get_translations("error_failed_update_tandem_data"), dialog)
