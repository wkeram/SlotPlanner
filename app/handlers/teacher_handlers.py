"""Teacher management event handlers.

This module contains all handlers for teacher-related functionality
including adding, editing, and deleting teachers.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTableWidget, QComboBox, QMessageBox
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer
from app.config.logging_config import get_logger
from app.storage import Storage
from app.utils import get_translations, show_error
from app.ui_teachers import refresh_teacher_table, refresh_children_table, refresh_tandems_table
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
    if not button_add_slot: missing_buttons.append("buttonAddSlot")
    if not button_remove_slot: missing_buttons.append("buttonRemoveSlot")
    if not button_save: missing_buttons.append("buttonOk")
    if not button_cancel: missing_buttons.append("buttonCancel")
    
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
    invalid_row = False
    
    for row in range(table.rowCount()):
        day_widget = table.cellWidget(row, 0)
        start_widget = table.cellWidget(row, 1)
        end_widget = table.cellWidget(row, 2)

        if any(w is None for w in [day_widget, start_widget, end_widget]):
            continue  # skip incomplete rows

        day = day_widget.currentText()
        start = start_widget.currentText()
        end = end_widget.currentText()

        # Validate time slot duration
        try:
            fmt = "%H:%M"
            start_dt = datetime.strptime(start, fmt)
            end_dt = datetime.strptime(end, fmt)
            duration = (end_dt - start_dt).total_seconds() / 60

            if start >= end or duration < 45:
                invalid_row = True
                continue

            availability.setdefault(day, []).append([start, end])
        except ValueError as e:
            logger.error(f"Error parsing time values: {e}")
            invalid_row = True
            continue

    if invalid_row:
        show_error(get_translations("invalid_time_range"), dialog)
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
    combo_start.currentTextChanged.connect(
        lambda: QTimer.singleShot(50, 
            lambda: logger.debug(f"Start time changed to: {combo_start.currentText()}")
        )
    )
    table.setCellWidget(row, 1, combo_start)

    # Setup end time dropdown
    combo_end = QComboBox()
    combo_end.setEditable(False)
    combo_end.addItems(times)
    default_end_index = times.index("17:00") if "17:00" in times else len(times)-1
    combo_end.setCurrentIndex(default_end_index)
    
    # Add delayed event handling to prevent crashes
    combo_end.currentTextChanged.connect(
        lambda: QTimer.singleShot(50, 
            lambda: logger.debug(f"End time changed to: {combo_end.currentText()}")
        )
    )
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
    # TODO: Implement teacher editing functionality
    show_error("Teacher editing functionality not yet implemented", window)


def teacher_delete_selected(window: QWidget, storage: Storage) -> None:
    """Delete the selected teacher.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    # TODO: Implement teacher deletion functionality
    show_error("Teacher deletion functionality not yet implemented", window)