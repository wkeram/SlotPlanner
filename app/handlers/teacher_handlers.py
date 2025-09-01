"""Teacher management event handlers.

This module contains all handlers for teacher-related functionality
including adding, editing, and deleting teachers.
"""

from datetime import datetime
from PySide6.QtWidgets import QWidget, QPushButton, QLineEdit, QTableWidget, QComboBox, QMessageBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer
from app.config.logging_config import get_logger
from app.storage import Storage
from app.utils import get_translations, show_error
from app.ui_teachers import refresh_teacher_table, refresh_children_table, refresh_tandems_table
from app.validation import Validator
from .base_handler import BaseHandler

logger = get_logger(__name__)


def teacher_open_add_teacher_dialog(window: QWidget, storage: Storage) -> None:
    """Open the dialog for adding a new teacher.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _open_dialog():
        logger.info("Opening add teacher dialog")

        loader = QUiLoader()
        file = QFile("app/ui/add_teacher.ui")

        if not file.open(QFile.ReadOnly):
            error_msg = f"Cannot open add_teacher.ui: {file.errorString()}"
            logger.error(error_msg)
            show_error(error_msg, window)
            return

        add_teacher_dialog = loader.load(file, window)
        file.close()

        if not add_teacher_dialog:
            error_msg = "Failed to load add_teacher.ui - loader returned None"
            logger.error(error_msg)
            show_error(error_msg, window)
            return

        add_teacher_dialog.setWindowTitle("Add Teacher")
        logger.debug("Teacher dialog UI loaded successfully")

        # Setup dialog buttons with error checking
        _setup_teacher_dialog_buttons(add_teacher_dialog, window, storage)

        # Show the dialog
        logger.debug("Showing teacher dialog")
        result = add_teacher_dialog.exec()
        logger.debug(f"Teacher dialog closed with result: {result}")

        # Proper cleanup to prevent memory leaks
        BaseHandler.cleanup_widget(add_teacher_dialog)

    BaseHandler.safe_execute(_open_dialog, parent=window)


def _setup_teacher_dialog_buttons(dialog: QWidget, window: QWidget, storage: Storage) -> None:
    """Setup button connections for the teacher dialog.

    Args:
        dialog: Add teacher dialog instance
        window: Main application window instance
        storage: Storage instance for data persistence
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
        error_msg = f"Missing buttons in add_teacher.ui: {', '.join(missing_buttons)}"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    # Connect buttons with safe error handling
    button_add_slot.clicked.connect(
        lambda: BaseHandler.safe_execute(teacher_dialog_add_availability_row, dialog, parent=dialog)
    )
    button_remove_slot.clicked.connect(
        lambda: BaseHandler.safe_execute(teacher_dialog_remove_selected_row, dialog, parent=dialog)
    )
    button_cancel.clicked.connect(dialog.reject)
    button_save.clicked.connect(
        lambda: BaseHandler.safe_execute(teacher_save_from_dialog, dialog, window, storage, parent=dialog)
    )

    logger.debug("Teacher dialog buttons connected")


def teacher_save_from_dialog(dialog: QWidget, window: QWidget, storage: Storage) -> None:
    """Save teacher data from the add teacher dialog.

    Args:
        dialog: Add teacher dialog instance
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    name_field = dialog.findChild(QLineEdit, "teacherNameLineEdit")
    if not name_field:
        show_error("Teacher name field not found in dialog", dialog)
        return

    name = name_field.text().replace(" ", "_").strip()
    if not name:
        show_error(get_translations("invalid_teacher_name"), dialog)
        return

    table = dialog.findChild(QTableWidget, "tableAvailability")
    if not table:
        show_error("Availability table not found in dialog", dialog)
        return

    availability = {}

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

    # Validate complete availability
    availability_validation = Validator.validate_teacher_availability(availability)
    if not availability_validation.is_valid:
        show_error(f"Teacher availability validation failed:\n\n{availability_validation.get_error_message()}", dialog)
        return

    # Show warnings for availability if any
    if availability_validation.has_warnings:
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            dialog,
            "Availability Warnings",
            f"The following warnings were found:\n\n{availability_validation.get_warning_message()}\n\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return

    # Save teacher data
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    data = storage.load(year) or storage.get_default_data_structure()
    data.setdefault("teachers", {})[name] = {"availability": availability}

    success = storage.save(year, data)
    if success:
        logger.info(f"Successfully saved teacher: {name}")
        dialog.accept()

        # Refresh all tables
        refresh_teacher_table(window.ui, data)
        refresh_children_table(window.ui, data)
        refresh_tandems_table(window.ui, data)
    else:
        logger.error(f"Failed to save teacher: {name}")
        show_error("Failed to save teacher data", dialog)


def teacher_dialog_add_availability_row(dialog: QWidget) -> None:
    """Add a new availability row to the teacher dialog table.

    Args:
        dialog: Add teacher dialog instance
    """
    logger.debug("Adding availability row to teacher dialog")

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

    logger.debug(f"Generated {len(times)} time options")

    # Setup start time dropdown
    combo_start = QComboBox()
    combo_start.setEditable(False)
    combo_start.addItems(times)
    default_start_index = times.index("08:00") if "08:00" in times else 0
    combo_start.setCurrentIndex(default_start_index)

    # Add delayed event handling to prevent crashes
    combo_start.currentTextChanged.connect(lambda text: logger.debug(f"Start time changed to: {text}"))
    table.setCellWidget(row, 1, combo_start)

    # Setup end time dropdown
    combo_end = QComboBox()
    combo_end.setEditable(False)
    combo_end.addItems(times)
    default_end_index = times.index("17:00") if "17:00" in times else len(times) - 1
    combo_end.setCurrentIndex(default_end_index)

    # Add delayed event handling to prevent crashes
    combo_end.currentTextChanged.connect(lambda text: logger.debug(f"End time changed to: {text}"))
    table.setCellWidget(row, 2, combo_end)

    logger.debug("Availability row added successfully")


def teacher_dialog_remove_selected_row(dialog: QWidget) -> None:
    """Remove the selected row from the availability table.

    Args:
        dialog: Add teacher dialog instance
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


def teacher_edit_selected(window: QWidget, storage: Storage) -> None:
    """Edit the selected teacher.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _edit_teacher():
        table = window.ui.findChild(QTableWidget, "tableTeachers")
        if not table:
            show_error("Teachers table not found", window)
            return

        selected_row = table.currentRow()
        if selected_row < 0:
            show_error("Please select a teacher to edit", window)
            return

        # Get teacher name from first column
        name_item = table.item(selected_row, 0)
        if not name_item:
            show_error("Could not get teacher name from selection", window)
            return

        teacher_name = name_item.text()
        logger.info(f"Opening edit dialog for teacher: {teacher_name}")

        # Load teacher data
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        data = storage.load(year) or storage.get_default_data_structure()
        teacher_data = data.get("teachers", {}).get(teacher_name)

        if not teacher_data:
            show_error(f"Teacher data not found for: {teacher_name}", window)
            return

        # Open edit dialog with pre-populated data
        _open_teacher_edit_dialog(window, storage, teacher_name, teacher_data)

    BaseHandler.safe_execute(_edit_teacher, parent=window)


def teacher_delete_selected(window: QWidget, storage: Storage) -> None:
    """Delete the selected teacher.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _delete_teacher():
        table = window.ui.findChild(QTableWidget, "tableTeachers")
        if not table:
            show_error("Teachers table not found", window)
            return

        selected_row = table.currentRow()
        if selected_row < 0:
            show_error("Please select a teacher to delete", window)
            return

        # Get teacher name from first column
        name_item = table.item(selected_row, 0)
        if not name_item:
            show_error("Could not get teacher name from selection", window)
            return

        teacher_name = name_item.text()

        # Analyze dependencies
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        data = storage.load(year) or storage.get_default_data_structure()

        # Find children who prefer this teacher
        affected_children = []
        for child_name, child_data in data.get("children", {}).items():
            preferred_teachers = child_data.get("preferred_teachers", [])
            if teacher_name in preferred_teachers:
                affected_children.append(child_name)

        # Build confirmation message
        message_parts = [f"Are you sure you want to delete teacher '{teacher_name}'?"]

        if affected_children:
            message_parts.append(
                f"\n\nThis teacher is preferred by {len(affected_children)} children:"
                f"\n• {chr(10).join(affected_children)}"
                f"\n\nThese preferences will be removed."
            )

        if not affected_children:
            message_parts.append("\n\nThis teacher has no current preferences.")

        # Show detailed confirmation
        reply = QMessageBox.question(
            window, "Delete Teacher", "\n".join(message_parts), QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Delete teacher and clean up dependencies
        changes_made = []

        # Remove teacher
        if teacher_name in data.get("teachers", {}):
            del data["teachers"][teacher_name]
            changes_made.append(f"Deleted teacher '{teacher_name}'")
            logger.info(f"Deleted teacher: {teacher_name}")

        # Remove from children's preferences
        for child_name in affected_children:
            child_data = data["children"][child_name]
            preferred_teachers = child_data.get("preferred_teachers", [])
            if teacher_name in preferred_teachers:
                preferred_teachers.remove(teacher_name)
                child_data["preferred_teachers"] = preferred_teachers
                changes_made.append(f"Removed preference from child '{child_name}'")

        # Save and refresh
        success = storage.save(year, data)
        if success:
            logger.info(f"Successfully deleted teacher {teacher_name} with {len(changes_made)} changes")

            # Refresh all tables
            refresh_teacher_table(window.ui, data)
            refresh_children_table(window.ui, data)
            refresh_tandems_table(window.ui, data)

            # Show detailed success message
            success_message = f"Teacher '{teacher_name}' has been deleted successfully."
            if len(changes_made) > 1:
                success_message += f"\n\nChanges made:\n• {chr(10).join(changes_made)}"

            BaseHandler.show_info(window, "Teacher Deleted", success_message)

            if hasattr(window, "feedback_manager") and window.feedback_manager:
                window.feedback_manager.show_success(f"Teacher '{teacher_name}' deleted successfully")
        else:
            logger.error(f"Failed to delete teacher: {teacher_name}")
            show_error(f"Failed to delete teacher '{teacher_name}'", window)

    BaseHandler.safe_execute(_delete_teacher, parent=window)


def _open_teacher_edit_dialog(window: QWidget, storage: Storage, teacher_name: str, teacher_data: dict) -> None:
    """Open the teacher edit dialog with pre-populated data.

    Args:
        window: Main window instance
        storage: Storage instance
        teacher_name: Name of teacher to edit
        teacher_data: Existing teacher data
    """
    logger.info(f"Opening edit dialog for teacher: {teacher_name}")

    loader = QUiLoader()
    file = QFile("app/ui/add_teacher.ui")

    if not file.open(QFile.ReadOnly):
        error_msg = f"Cannot open add_teacher.ui: {file.errorString()}"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    edit_teacher_dialog = loader.load(file, window)
    file.close()

    if not edit_teacher_dialog:
        error_msg = "Failed to load add_teacher.ui - loader returned None"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    edit_teacher_dialog.setWindowTitle(f"Edit Teacher: {teacher_name}")
    logger.debug("Teacher edit dialog UI loaded successfully")

    # Pre-populate the dialog with existing data
    _populate_teacher_edit_dialog(edit_teacher_dialog, teacher_name, teacher_data)

    # Setup dialog functionality for editing
    _setup_teacher_edit_dialog_buttons(edit_teacher_dialog, window, storage, teacher_name)

    # Show the dialog
    logger.debug("Showing teacher edit dialog")
    result = edit_teacher_dialog.exec()
    logger.debug(f"Teacher edit dialog closed with result: {result}")

    # Proper cleanup to prevent memory leaks
    BaseHandler.cleanup_widget(edit_teacher_dialog)


def _populate_teacher_edit_dialog(dialog: QWidget, teacher_name: str, teacher_data: dict) -> None:
    """Pre-populate the teacher edit dialog with existing data.

    Args:
        dialog: Teacher edit dialog instance
        teacher_name: Name of the teacher being edited
        teacher_data: Existing teacher data
    """
    logger.debug(f"Pre-populating teacher edit dialog for: {teacher_name}")

    # Set teacher name (enable editing with warning)
    name_field = dialog.findChild(QLineEdit, "teacherNameLineEdit")
    if name_field:
        name_field.setText(teacher_name)
        name_field.setReadOnly(False)  # Allow name changes during edit
        name_field.setStyleSheet("background-color: #fff7e6; border: 1px solid #ff9500;")  # Orange warning background
        name_field.setToolTip(
            "⚠️ Changing the name will update all references to this teacher, including children's preferences and schedules."
        )

    # Populate availability table
    availability_table = dialog.findChild(QTableWidget, "tableAvailability")
    if availability_table:
        # Clear existing rows
        availability_table.setRowCount(0)

        # Add rows for existing availability
        availability = teacher_data.get("availability", {})
        for day, slots in availability.items():
            for slot in slots:
                if len(slot) == 2:
                    _add_teacher_availability_row_with_data(dialog, day, slot[0], slot[1])

        logger.debug(f"Pre-populated {sum(len(slots) for slots in availability.values())} availability slots")


def _setup_teacher_edit_dialog_buttons(
    dialog: QWidget, window: QWidget, storage: Storage, original_teacher_name: str
) -> None:
    """Setup button connections for the teacher edit dialog.

    Args:
        dialog: Teacher edit dialog instance
        window: Main application window instance
        storage: Storage instance for data persistence
        original_teacher_name: The original name of the teacher being edited
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
        error_msg = f"Missing buttons in teacher edit dialog: {', '.join(missing_buttons)}"
        logger.error(error_msg)
        show_error(error_msg, window)
        return

    # Connect buttons with safe error handling
    button_add_slot.clicked.connect(
        lambda: BaseHandler.safe_execute(teacher_dialog_add_availability_row, dialog, parent=dialog)
    )
    button_remove_slot.clicked.connect(
        lambda: BaseHandler.safe_execute(teacher_dialog_remove_selected_row, dialog, parent=dialog)
    )
    button_cancel.clicked.connect(dialog.reject)
    button_save.clicked.connect(
        lambda: BaseHandler.safe_execute(
            teacher_update_from_edit_dialog, dialog, window, storage, original_teacher_name, parent=dialog
        )
    )

    logger.debug("Teacher edit dialog buttons connected")


def teacher_update_from_edit_dialog(
    dialog: QWidget, window: QWidget, storage: Storage, original_teacher_name: str
) -> None:
    """Update teacher data from the edit dialog.

    Args:
        dialog: Teacher edit dialog instance
        window: Main window instance
        storage: Storage instance for data persistence
        original_teacher_name: Original name of the teacher being edited
    """
    logger.debug(f"Updating teacher data for: {original_teacher_name}")

    # Get the (possibly changed) teacher name
    name_field = dialog.findChild(QLineEdit, "teacherNameLineEdit")
    if not name_field:
        show_error("Teacher name field not found in dialog", dialog)
        return

    new_teacher_name = name_field.text().replace(" ", "_").strip()

    # Validate the name
    name_validation = Validator.validate_teacher_name(new_teacher_name)
    if not name_validation.is_valid:
        show_error(name_validation.get_error_message(), dialog)
        return

    # Get current year and data
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    data = storage.load(year) or storage.get_default_data_structure()

    # Check for name conflicts (if name changed)
    name_changed = new_teacher_name != original_teacher_name
    if name_changed:
        if new_teacher_name in data.get("teachers", {}):
            show_error(f"A teacher named '{new_teacher_name}' already exists. Please choose a different name.", dialog)
            return

        # Confirm name change with user
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            dialog,
            "Confirm Name Change",
            f"Are you sure you want to rename '{original_teacher_name}' to '{new_teacher_name}'?\n\n"
            f"This will update all references including children's preferences and schedules.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

    teacher_name = new_teacher_name

    # Get availability from table
    table = dialog.findChild(QTableWidget, "tableAvailability")
    if not table:
        show_error("Availability table not found in dialog", dialog)
        return

    availability = {}

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

    # Validate complete availability
    availability_validation = Validator.validate_teacher_availability(availability)
    if not availability_validation.is_valid:
        show_error(f"Teacher availability validation failed:\n\n{availability_validation.get_error_message()}", dialog)
        return

    # Show warnings for availability if any
    if availability_validation.has_warnings:
        from PySide6.QtWidgets import QMessageBox

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

        # Remove old teacher entry
        if original_teacher_name in data.get("teachers", {}):
            del data["teachers"][original_teacher_name]
            changes_made.append(f"Removed old teacher entry: {original_teacher_name}")

        # Update children's preferred teacher references
        children_updated = 0
        for child_name, child_data in data.get("children", {}).items():
            preferred_teachers = child_data.get("preferred_teachers", [])
            if original_teacher_name in preferred_teachers:
                preferred_teachers[preferred_teachers.index(original_teacher_name)] = teacher_name
                children_updated += 1
                changes_made.append(f"Updated child '{child_name}' preferred teacher reference")

        # Update schedule references (if any exist)
        schedules_updated = 0
        for day, day_schedule in data.get("schedule", {}).items():
            for time_slot, assignment in day_schedule.items():
                if assignment.get("teacher") == original_teacher_name:
                    assignment["teacher"] = teacher_name
                    schedules_updated += 1
                    changes_made.append(f"Updated schedule reference for {day} {time_slot}")

        logger.info(
            f"Teacher rename: {original_teacher_name} -> {teacher_name}, {children_updated} children updated, {schedules_updated} schedule entries updated"
        )

    # Update teacher data
    data.setdefault("teachers", {})[teacher_name] = {"availability": availability}

    success = storage.save(year, data)
    if success:
        action = "renamed and updated" if name_changed else "updated"
        logger.info(f"Successfully {action} teacher: {original_teacher_name} -> {teacher_name}")
        dialog.accept()

        # Refresh all tables
        refresh_teacher_table(window.ui, data)
        refresh_children_table(window.ui, data)
        refresh_tandems_table(window.ui, data)

        if hasattr(window, "feedback_manager") and window.feedback_manager:
            if name_changed:
                window.feedback_manager.show_success(
                    f"Teacher renamed from '{original_teacher_name}' to '{teacher_name}' successfully"
                )
            else:
                window.feedback_manager.show_success(f"Teacher '{teacher_name}' updated successfully")
    else:
        logger.error(f"Failed to update teacher: {teacher_name}")
        show_error("Failed to update teacher data", dialog)


def _add_teacher_availability_row_with_data(dialog: QWidget, day: str, start_time: str, end_time: str) -> None:
    """Add a pre-populated availability row to the teacher dialog table.

    Args:
        dialog: Teacher dialog instance
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

    # Generate time options (7:00 - 20:45 with 15min intervals)
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

    logger.debug(f"Added pre-populated teacher availability row: {day} {start_time}-{end_time}")
