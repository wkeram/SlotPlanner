"""Child management event handlers.

This module contains all handlers for child-related functionality
including adding, editing, and deleting children.
"""

from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QWidget,
)

from app.config.logging_config import get_logger
from app.storage import Storage
from app.ui_teachers import refresh_children_table, refresh_tandems_table, refresh_teacher_table
from app.utils import show_error
from app.validation import Validator

from .base_handler import BaseHandler

logger = get_logger(__name__)


def child_open_add_dialog(window: QWidget, storage: Storage) -> None:
    """Open the dialog for adding a new child.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _open_dialog():
        logger.info("Opening add child dialog")

        loader = QUiLoader()
        file = QFile("app/ui/add_child.ui")

        if not file.open(QFile.ReadOnly):
            error_msg = f"Cannot open add_child.ui: {file.errorString()}"
            logger.error(error_msg)
            show_error(error_msg, window)
            return

        add_child_dialog = loader.load(file, window)
        file.close()

        if not add_child_dialog:
            error_msg = "Failed to load add_child.ui - loader returned None"
            logger.error(error_msg)
            show_error(error_msg, window)
            return

        add_child_dialog.setWindowTitle("Add Child")
        logger.debug("Child dialog UI loaded successfully")

        # Setup dialog functionality
        _setup_child_dialog(add_child_dialog, window, storage)

        # Show the dialog
        logger.debug("Showing child dialog")
        result = add_child_dialog.exec()
        logger.debug(f"Child dialog closed with result: {result}")

        # Proper cleanup to prevent memory leaks
        BaseHandler.cleanup_widget(add_child_dialog)

    BaseHandler.safe_execute(_open_dialog, parent=window)


def child_edit_selected(window: QWidget, storage: Storage) -> None:
    """Edit the selected child.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _edit_child():
        table = window.ui.findChild(QTableWidget, "tableChildren")
        if not table:
            show_error("Children table not found", window)
            return

        selected_row = table.currentRow()
        if selected_row < 0:
            show_error("Please select a child to edit", window)
            return

        # Get child name from first column
        name_item = table.item(selected_row, 0)
        if not name_item:
            show_error("Could not get child name from selection", window)
            return

        child_name = name_item.text()
        logger.info(f"Opening edit dialog for child: {child_name}")

        # Load child data
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        data = storage.load(year) or storage.get_default_data_structure()
        child_data = data.get("children", {}).get(child_name)

        if not child_data:
            show_error(f"Child data not found for: {child_name}", window)
            return

        # Open edit dialog with pre-populated data
        _open_child_edit_dialog(window, storage, child_name, child_data)

    BaseHandler.safe_execute(_edit_child, parent=window)


def child_delete_selected(window: QWidget, storage: Storage) -> None:
    """Delete the selected child.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _delete_child():
        table = window.ui.findChild(QTableWidget, "tableChildren")
        if not table:
            show_error("Children table not found", window)
            return

        selected_row = table.currentRow()
        if selected_row < 0:
            show_error("Please select a child to delete", window)
            return

        # Get child name from first column
        name_item = table.item(selected_row, 0)
        if not name_item:
            show_error("Could not get child name from selection", window)
            return

        child_name = name_item.text()

        # Check for dependencies (tandems)
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        data = storage.load(year) or storage.get_default_data_structure()

        # Find tandems containing this child
        affected_tandems = []
        for tandem_name, tandem_data in data.get("tandems", {}).items():
            if tandem_data.get("child1") == child_name or tandem_data.get("child2") == child_name:
                affected_tandems.append(tandem_name)

        # Build confirmation message
        message = f"Are you sure you want to delete child '{child_name}'?"
        if affected_tandems:
            message += f"\n\nThis will also remove the following tandems:\n• {chr(10).join(affected_tandems)}"

        # Confirm deletion
        reply = QMessageBox.question(window, "Delete Child", message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        # Delete child and affected tandems
        if child_name in data.get("children", {}):
            del data["children"][child_name]
            logger.info(f"Deleted child: {child_name}")

        for tandem_name in affected_tandems:
            if tandem_name in data.get("tandems", {}):
                del data["tandems"][tandem_name]
                logger.info(f"Deleted affected tandem: {tandem_name}")

        # Save and refresh
        success = storage.save(year, data)
        if success:
            logger.info(f"Successfully deleted child {child_name} and {len(affected_tandems)} tandems")

            # Refresh all tables
            refresh_teacher_table(window.ui, data)
            refresh_children_table(window.ui, data)
            refresh_tandems_table(window.ui, data)

            BaseHandler.show_info(
                window,
                "Child Deleted",
                f"Child '{child_name}' has been deleted successfully."
                + (f"\n{len(affected_tandems)} tandems were also removed." if affected_tandems else ""),
            )
        else:
            logger.error(f"Failed to delete child: {child_name}")
            show_error(f"Failed to delete child '{child_name}'", window)

    BaseHandler.safe_execute(_delete_child, parent=window)


def _setup_child_dialog(dialog: QWidget, window: QWidget, storage: Storage) -> None:
    """Setup the child dialog with buttons and data population.

    Args:
        dialog: Child dialog instance
        window: Main window instance
        storage: Storage instance
    """
    # Find buttons with error checking
    button_add_slot = dialog.findChild(QPushButton, "buttonAddSlot")
    button_remove_slot = dialog.findChild(QPushButton, "buttonRemoveSlot")
    button_save = dialog.findChild(QPushButton, "buttonOk")
    button_cancel = dialog.findChild(QPushButton, "buttonCancel")

    missing_buttons = []
    if not button_add_slot:
        missing_buttons.append("buttonAddSlot")
    if not button_remove_slot:
        missing_buttons.append("buttonRemoveSlot")
    if not button_save:
        missing_buttons.append("buttonOk")
    if not button_cancel:
        missing_buttons.append("buttonCancel")

    if missing_buttons:
        error_msg = f"Missing buttons in add_child.ui: {', '.join(missing_buttons)}"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    # Populate available teachers in the list
    _populate_teachers_list(dialog, window, storage)

    # Connect buttons with safe error handling
    button_add_slot.clicked.connect(
        lambda: BaseHandler.safe_execute(child_dialog_add_availability_row, dialog, parent=dialog)
    )
    button_remove_slot.clicked.connect(
        lambda: BaseHandler.safe_execute(child_dialog_remove_selected_row, dialog, parent=dialog)
    )
    button_cancel.clicked.connect(dialog.reject)
    button_save.clicked.connect(
        lambda: BaseHandler.safe_execute(child_save_from_dialog, dialog, window, storage, parent=dialog)
    )

    logger.debug("Child dialog buttons connected")


def _populate_teachers_list(dialog: QWidget, window: QWidget, storage: Storage) -> None:
    """Populate the preferred teachers list with available teachers.

    Args:
        dialog: Child dialog instance
        window: Main window instance
        storage: Storage instance
    """
    teachers_list = dialog.findChild(QListWidget, "preferredTeachersList")
    if not teachers_list:
        logger.warning("preferredTeachersList not found in dialog")
        return

    # Get current teachers data
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    data = storage.load(year) or storage.get_default_data_structure()
    teachers = data.get("teachers", {})

    # Populate list with teachers
    teachers_list.clear()
    for teacher_name in sorted(teachers.keys()):
        item = QListWidgetItem(teacher_name)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        teachers_list.addItem(item)

    logger.debug(f"Populated {len(teachers)} teachers in preferred teachers list")


def child_dialog_add_availability_row(dialog: QWidget) -> None:
    """Add a new availability row to the child dialog table.

    Args:
        dialog: Child dialog instance
    """
    logger.debug("Adding availability row to child dialog")

    table = dialog.findChild(QTableWidget, "tableAvailability")
    if not table:
        logger.error("tableAvailability not found in dialog")
        return

    row = table.rowCount()
    table.insertRow(row)
    logger.debug(f"Inserted row {row}")

    # Setup day dropdown
    combo_day = QComboBox()
    combo_day.addItems(["Mo", "Di", "Mi", "Do", "Fr"])
    combo_day.setCurrentIndex(0)
    combo_day.setEditable(False)
    table.setCellWidget(row, 0, combo_day)

    # Generate time options (7:00 - 20:45 with 15min intervals)
    times = []
    for h in range(7, 21):
        for m in (0, 15, 30, 45):
            times.append(f"{h:02}:{m:02}")

    # Setup start time dropdown
    combo_start = QComboBox()
    combo_start.setEditable(False)
    combo_start.addItems(times)
    default_start_index = times.index("08:00") if "08:00" in times else 0
    combo_start.setCurrentIndex(default_start_index)

    combo_start.currentTextChanged.connect(lambda text: logger.debug(f"Start time changed to: {text}"))
    table.setCellWidget(row, 1, combo_start)

    # Setup end time dropdown
    combo_end = QComboBox()
    combo_end.setEditable(False)
    combo_end.addItems(times)
    default_end_index = times.index("17:00") if "17:00" in times else len(times) - 1
    combo_end.setCurrentIndex(default_end_index)

    combo_end.currentTextChanged.connect(lambda text: logger.debug(f"End time changed to: {text}"))
    table.setCellWidget(row, 2, combo_end)

    logger.debug("Availability row added successfully")


def child_dialog_remove_selected_row(dialog: QWidget) -> None:
    """Remove the selected row from the availability table.

    Args:
        dialog: Child dialog instance
    """
    logger.debug("Removing selected availability row")

    table = dialog.findChild(QTableWidget, "tableAvailability")
    if not table:
        logger.error("tableAvailability not found in dialog")
        return

    selected = table.currentRow()
    if selected >= 0:
        table.removeRow(selected)
        logger.debug(f"Removed row {selected}")
    else:
        logger.debug("No row selected to remove")
        show_error("Please select a row to remove.", dialog)


def child_save_from_dialog(dialog: QWidget, window: QWidget, storage: Storage) -> None:
    """Save child data from the add child dialog.

    Args:
        dialog: Child dialog instance
        window: Main window instance
        storage: Storage instance for data persistence
    """
    name_field = dialog.findChild(QLineEdit, "childNameLineEdit")
    if not name_field:
        show_error("Child name field not found in dialog", dialog)
        return

    # Validate child name
    name_validation = Validator.validate_child_name(name_field.text())
    if not name_validation.is_valid:
        show_error(name_validation.get_error_message(), dialog)
        return

    # Show warnings if any
    if name_validation.has_warnings:
        reply = QMessageBox.question(
            dialog,
            "Validation Warnings",
            f"The following warnings were found:\n\n{name_validation.get_warning_message()}\n\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return

    name = name_field.text().replace(" ", "_").strip()

    # Get early preference
    early_checkbox = dialog.findChild(QCheckBox, "earlyPreferenceCheckBox")
    early_preference = early_checkbox.isChecked() if early_checkbox else False

    # Get preferred teachers
    teachers_list = dialog.findChild(QListWidget, "preferredTeachersList")
    preferred_teachers = []
    if teachers_list:
        for i in range(teachers_list.count()):
            item = teachers_list.item(i)
            if item.checkState() == Qt.Checked:
                preferred_teachers.append(item.text())

    # Get availability
    table = dialog.findChild(QTableWidget, "tableAvailability")
    availability = {}

    if table:
        for row in range(table.rowCount()):
            day_widget = table.cellWidget(row, 0)
            start_widget = table.cellWidget(row, 1)
            end_widget = table.cellWidget(row, 2)

            if any(w is None for w in [day_widget, start_widget, end_widget]):
                continue  # skip incomplete rows

            day = day_widget.currentText()
            start = start_widget.currentText()
            end = end_widget.currentText()

            # Validate time slot
            slot_validation = Validator.validate_time_slot(start, end)
            if not slot_validation.is_valid:
                show_error(f"Invalid time slot on day '{day}':\n\n{slot_validation.get_error_message()}", dialog)
                return

            availability.setdefault(day, []).append([start, end])

    # Validate complete child data
    if availability:
        availability_validation = Validator.validate_teacher_availability(availability)
        if not availability_validation.is_valid:
            show_error(
                f"Child availability validation failed:\n\n{availability_validation.get_error_message()}", dialog
            )
            return

        # Show warnings for availability if any
        if availability_validation.has_warnings:
            reply = QMessageBox.question(
                dialog,
                "Availability Warnings",
                f"The following warnings were found:\n\n{availability_validation.get_warning_message()}\n\nDo you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply != QMessageBox.Yes:
                return

    # Save child data
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    data = storage.load(year) or storage.get_default_data_structure()

    data.setdefault("children", {})[name] = {
        "early_preference": early_preference,
        "preferred_teachers": preferred_teachers,
        "availability": availability,
    }

    success = storage.save(year, data)
    if success:
        logger.info(f"Successfully saved child: {name}")
        dialog.accept()

        # Refresh all tables
        refresh_teacher_table(window.ui, data)
        refresh_children_table(window.ui, data)
        refresh_tandems_table(window.ui, data)

        if hasattr(window, "feedback_manager") and window.feedback_manager:
            window.feedback_manager.show_success(f"Child '{name}' saved successfully")
    else:
        logger.error(f"Failed to save child: {name}")
        show_error("Failed to save child data", dialog)


def _open_child_edit_dialog(window: QWidget, storage: Storage, child_name: str, child_data: dict) -> None:
    """Open the child edit dialog with pre-populated data.

    Args:
        window: Main window instance
        storage: Storage instance
        child_name: Name of child to edit
        child_data: Existing child data
    """
    logger.info(f"Opening edit dialog for child: {child_name}")

    loader = QUiLoader()
    file = QFile("app/ui/add_child.ui")

    if not file.open(QFile.ReadOnly):
        error_msg = f"Cannot open add_child.ui: {file.errorString()}"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    edit_child_dialog = loader.load(file, window)
    file.close()

    if not edit_child_dialog:
        error_msg = "Failed to load add_child.ui - loader returned None"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    edit_child_dialog.setWindowTitle(f"Edit Child: {child_name}")
    logger.debug("Child edit dialog UI loaded successfully")

    # Pre-populate the dialog with existing data
    _populate_child_edit_dialog(edit_child_dialog, child_name, child_data, window, storage)

    # Setup dialog functionality for editing
    _setup_child_edit_dialog(edit_child_dialog, window, storage, child_name, child_data)

    # Show the dialog
    logger.debug("Showing child edit dialog")
    result = edit_child_dialog.exec()
    logger.debug(f"Child edit dialog closed with result: {result}")

    # Proper cleanup to prevent memory leaks
    BaseHandler.cleanup_widget(edit_child_dialog)


def _populate_child_edit_dialog(
    dialog: QWidget, child_name: str, child_data: dict, window: QWidget, storage: Storage
) -> None:
    """Pre-populate the child edit dialog with existing data.

    Args:
        dialog: Child edit dialog instance
        child_name: Name of the child being edited
        child_data: Existing child data
        window: Main window instance
        storage: Storage instance
    """
    logger.debug(f"Pre-populating child edit dialog for: {child_name}")

    # Set child name (enable editing with warning)
    name_field = dialog.findChild(QLineEdit, "childNameLineEdit")
    if name_field:
        name_field.setText(child_name)
        name_field.setReadOnly(False)  # Allow name changes during edit
        name_field.setStyleSheet("background-color: #fff7e6; border: 1px solid #ff9500;")  # Orange warning background
        name_field.setToolTip(
            "⚠️ Changing the name will update all references to this child, including tandems and schedules."
        )

    # Set early preference checkbox
    early_checkbox = dialog.findChild(QCheckBox, "checkEarlyPreference")
    if early_checkbox:
        early_preference = child_data.get("early_preference", False)
        early_checkbox.setChecked(early_preference)
        logger.debug(f"Set early preference to: {early_preference}")

    # Populate preferred teachers list
    teachers_list = dialog.findChild(QListWidget, "listAvailableTeachers")
    if teachers_list:
        # Clear existing items
        teachers_list.clear()

        # Get current teachers and preferred teachers
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        current_data = storage.load(year) or storage.get_default_data_structure()
        available_teachers = list(current_data.get("teachers", {}).keys())
        preferred_teachers = child_data.get("preferred_teachers", [])

        # Add all available teachers with checkboxes
        for teacher in available_teachers:
            item = QListWidgetItem(teacher)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if teacher in preferred_teachers else Qt.Unchecked)
            teachers_list.addItem(item)

        logger.debug(f"Populated {len(available_teachers)} teachers, {len(preferred_teachers)} preferred")

    # Populate availability table
    availability_table = dialog.findChild(QTableWidget, "tableAvailability")
    if availability_table:
        # Clear existing rows
        availability_table.setRowCount(0)

        # Add rows for existing availability
        availability = child_data.get("availability", {})
        for day, slots in availability.items():
            for slot in slots:
                if len(slot) == 2:
                    _add_availability_row_with_data(dialog, day, slot[0], slot[1])

        logger.debug(f"Pre-populated {sum(len(slots) for slots in availability.values())} availability slots")


def _setup_child_edit_dialog(
    dialog: QWidget, window: QWidget, storage: Storage, original_child_name: str, original_child_data: dict
) -> None:
    """Setup button connections for the child edit dialog.

    Args:
        dialog: Child edit dialog instance
        window: Main window instance
        storage: Storage instance
        original_child_name: The original name of the child being edited
        original_child_data: The original child data for comparison
    """
    # Find buttons with error checking
    button_add_slot = dialog.findChild(QPushButton, "buttonAddSlot")
    button_remove_slot = dialog.findChild(QPushButton, "buttonRemoveSlot")
    button_save = dialog.findChild(QPushButton, "buttonOk")
    button_cancel = dialog.findChild(QPushButton, "buttonCancel")

    missing_buttons = []
    if not button_add_slot:
        missing_buttons.append("buttonAddSlot")
    if not button_remove_slot:
        missing_buttons.append("buttonRemoveSlot")
    if not button_save:
        missing_buttons.append("buttonOk")
    if not button_cancel:
        missing_buttons.append("buttonCancel")

    if missing_buttons:
        error_msg = f"Missing buttons in child edit dialog: {', '.join(missing_buttons)}"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    # Connect buttons with safe error handling
    button_add_slot.clicked.connect(
        lambda: BaseHandler.safe_execute(child_dialog_add_availability_row, dialog, parent=dialog)
    )
    button_remove_slot.clicked.connect(
        lambda: BaseHandler.safe_execute(child_dialog_remove_selected_row, dialog, parent=dialog)
    )
    button_cancel.clicked.connect(dialog.reject)
    button_save.clicked.connect(
        lambda: BaseHandler.safe_execute(
            child_update_from_edit_dialog, dialog, window, storage, original_child_name, parent=dialog
        )
    )

    logger.debug("Child edit dialog buttons connected")


def child_update_from_edit_dialog(dialog: QWidget, window: QWidget, storage: Storage, original_child_name: str) -> None:
    """Update child data from the edit dialog.

    Args:
        dialog: Child edit dialog instance
        window: Main window instance
        storage: Storage instance for data persistence
        original_child_name: Original name of the child being edited
    """
    logger.debug(f"Updating child data for: {original_child_name}")

    # Get current year
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    data = storage.load(year) or storage.get_default_data_structure()

    # Get the (possibly changed) child name
    name_field = dialog.findChild(QLineEdit, "childNameLineEdit")
    if not name_field:
        show_error("Child name field not found in dialog", dialog)
        return

    new_child_name = name_field.text().strip()

    # Validate the name
    name_validation = Validator.validate_child_name(new_child_name)
    if not name_validation.is_valid:
        show_error(name_validation.get_error_message(), dialog)
        return

    # Check for name conflicts (if name changed)
    name_changed = new_child_name != original_child_name
    if name_changed:
        if new_child_name in data.get("children", {}):
            show_error(f"A child named '{new_child_name}' already exists. Please choose a different name.", dialog)
            return

        # Confirm name change with user
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            dialog,
            "Confirm Name Change",
            f"Are you sure you want to rename '{original_child_name}' to '{new_child_name}'?\n\n"
            f"This will update all references including tandems and schedules.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

    child_name = new_child_name

    # Get early preference
    early_checkbox = dialog.findChild(QCheckBox, "checkEarlyPreference")
    early_preference = early_checkbox.isChecked() if early_checkbox else False

    # Get preferred teachers from list
    preferred_teachers = []
    teachers_list = dialog.findChild(QListWidget, "listAvailableTeachers")
    if teachers_list:
        for i in range(teachers_list.count()):
            item = teachers_list.item(i)
            if item.checkState() == Qt.Checked:
                preferred_teachers.append(item.text())

    # Get availability from table
    availability = {}
    table = dialog.findChild(QTableWidget, "tableAvailability")
    if table:
        for row in range(table.rowCount()):
            day_widget = table.cellWidget(row, 0)
            start_widget = table.cellWidget(row, 1)
            end_widget = table.cellWidget(row, 2)

            if any(w is None for w in [day_widget, start_widget, end_widget]):
                continue

            day = day_widget.currentText()
            start = start_widget.currentText()
            end = end_widget.currentText()

            # Validate time slot
            slot_validation = Validator.validate_time_slot(start, end)
            if not slot_validation.is_valid:
                show_error(f"Invalid time slot on day '{day}':\n\n{slot_validation.get_error_message()}", dialog)
                return

            availability.setdefault(day, []).append([start, end])

    # Validate complete child data
    if availability:
        availability_validation = Validator.validate_teacher_availability(availability)
        if not availability_validation.is_valid:
            show_error(
                f"Child availability validation failed:\n\n{availability_validation.get_error_message()}", dialog
            )
            return

        # Show warnings for availability if any
        if availability_validation.has_warnings:
            reply = QMessageBox.question(
                dialog,
                "Availability Warnings",
                f"The following warnings were found:\n\n{availability_validation.get_warning_message()}\n\nDo you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply != QMessageBox.Yes:
                return

    # Handle name change and update all references
    if name_changed:
        changes_made = []

        # Remove old child entry
        if original_child_name in data.get("children", {}):
            del data["children"][original_child_name]
            changes_made.append(f"Removed old child entry: {original_child_name}")

        # Update tandem references
        tandems_updated = 0
        for tandem_name, tandem_data in data.get("tandems", {}).items():
            if tandem_data.get("child1") == original_child_name:
                tandem_data["child1"] = child_name
                tandems_updated += 1
                changes_made.append(f"Updated tandem '{tandem_name}' child1 reference")
            if tandem_data.get("child2") == original_child_name:
                tandem_data["child2"] = child_name
                tandems_updated += 1
                changes_made.append(f"Updated tandem '{tandem_name}' child2 reference")

        # Update schedule references (if any exist)
        schedules_updated = 0
        for day, day_schedule in data.get("schedule", {}).items():
            for time_slot, assignment in day_schedule.items():
                children = assignment.get("children", [])
                if original_child_name in children:
                    children[children.index(original_child_name)] = child_name
                    schedules_updated += 1
                    changes_made.append(f"Updated schedule reference for {day} {time_slot}")

        logger.info(
            f"Child rename: {original_child_name} -> {child_name}, {tandems_updated} tandems updated, {schedules_updated} schedule entries updated"
        )

    # Update child data
    data.setdefault("children", {})[child_name] = {
        "early_preference": early_preference,
        "preferred_teachers": preferred_teachers,
        "availability": availability,
    }

    # Save updated data
    success = storage.save(year, data)
    if success:
        action = "renamed and updated" if name_changed else "updated"
        logger.info(f"Successfully {action} child: {original_child_name} -> {child_name}")
        dialog.accept()

        # Refresh all tables
        refresh_teacher_table(window.ui, data)
        refresh_children_table(window.ui, data)
        refresh_tandems_table(window.ui, data)

        if hasattr(window, "feedback_manager") and window.feedback_manager:
            if name_changed:
                window.feedback_manager.show_success(
                    f"Child renamed from '{original_child_name}' to '{child_name}' successfully"
                )
            else:
                window.feedback_manager.show_success(f"Child '{child_name}' updated successfully")
    else:
        logger.error(f"Failed to update child: {child_name}")
        show_error("Failed to update child data", dialog)


def _add_availability_row_with_data(dialog: QWidget, day: str, start_time: str, end_time: str) -> None:
    """Add a pre-populated availability row to the dialog table.

    Args:
        dialog: Child dialog instance
        day: Day of week
        start_time: Start time
        end_time: End time
    """
    table = dialog.findChild(QTableWidget, "tableAvailability")
    if not table:
        logger.error("tableAvailability not found in dialog")
        return

    row = table.rowCount()
    table.insertRow(row)

    # Setup day dropdown
    combo_day = QComboBox()
    combo_day.addItems(["Mo", "Di", "Mi", "Do", "Fr"])
    combo_day.setCurrentText(day)
    combo_day.setEditable(False)
    table.setCellWidget(row, 0, combo_day)

    # Generate time options
    times = []
    for h in range(7, 21):
        for m in (0, 15, 30, 45):
            times.append(f"{h:02}:{m:02}")

    # Setup start time dropdown
    combo_start = QComboBox()
    combo_start.setEditable(False)
    combo_start.addItems(times)
    combo_start.setCurrentText(start_time)
    combo_start.currentTextChanged.connect(lambda text: logger.debug(f"Start time changed to: {text}"))
    table.setCellWidget(row, 1, combo_start)

    # Setup end time dropdown
    combo_end = QComboBox()
    combo_end.setEditable(False)
    combo_end.addItems(times)
    combo_end.setCurrentText(end_time)
    combo_end.currentTextChanged.connect(lambda text: logger.debug(f"End time changed to: {text}"))
    table.setCellWidget(row, 2, combo_end)

    logger.debug(f"Added pre-populated availability row: {day} {start_time}-{end_time}")
