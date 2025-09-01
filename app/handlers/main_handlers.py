"""Main application event handlers.

This module contains handlers for main application functionality like
loading, saving, year changes, and application lifecycle events.
"""

from PySide6.QtWidgets import QComboBox, QTableWidget, QMessageBox, QWidget
from app.config.logging_config import get_logger
from app.storage import Storage
from app.ui_teachers import refresh_teacher_table, refresh_children_table, refresh_tandems_table
from .base_handler import BaseHandler

logger = get_logger(__name__)


def main_on_load_clicked(window: QWidget, storage: Storage) -> None:
    """Handle click event for the load button.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    def _load_data():
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        data = storage.load(year)
        
        if data is not None:
            window.previous_year_index = window.ui.findChild(QComboBox, "comboYearSelect").currentIndex()
            logger.info(f"Successfully loaded data for year {year}")
        else:
            logger.info(f"No data found for year {year}, using default structure")
            data = storage.get_default_data_structure()
        
        # Refresh all tables with loaded data
        refresh_teacher_table(window.ui, data)
        refresh_children_table(window.ui, data)
        refresh_tandems_table(window.ui, data)
        
        return data
    
    BaseHandler.safe_execute(_load_data, parent=window)


def main_on_save_clicked(window: QWidget, storage: Storage) -> None:
    """Handle click event for the save button.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    def _save_data():
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        
        # TODO: Collect actual data from UI tables instead of empty structure
        data = {"teachers": {}, "children": {}, "tandems": {}, "weights": {}}
        
        success = storage.save(year, data)
        if success:
            logger.info(f"Successfully saved data for year {year}")
            BaseHandler.show_info(window, "Save Successful", f"Data for {year} has been saved successfully.")
        else:
            logger.error(f"Failed to save data for year {year}")
            
        # Refresh tables to reflect saved state
        refresh_teacher_table(window.ui, data)
        refresh_children_table(window.ui, data)
        refresh_tandems_table(window.ui, data)
        
        return success
    
    BaseHandler.safe_execute(_save_data, parent=window)


def _unsaved_changes(window: QWidget, storage: Storage) -> bool:
    """Check if there are unsaved changes in the current year.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence

    Returns:
        True if there are unsaved changes, False otherwise
    """
    try:
        previous_year = window.previous_year
        if not previous_year:
            return False
            
        stored_data = storage.load(previous_year)
        if stored_data is None:
            return False

        # Build current_data from UI state
        current_data = {"teachers": {}, "children": {}, "tandems": {}, "weights": {}}
        teachers_table = window.ui.findChild(QTableWidget, "tableTeachers")

        if teachers_table:
            for row in range(teachers_table.rowCount()):
                name_item = teachers_table.item(row, 0)
                avail_item = teachers_table.item(row, 1)

                if not name_item or not avail_item:
                    continue

                name = name_item.text()
                availability = {}

                for line in avail_item.text().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        day, rest = line.split(" ", 1)
                        slots = [slot.strip() for slot in rest.split(",")]
                        availability[day] = [slot.split("–") for slot in slots if "–" in slot]
                    except ValueError:
                        continue  # skip malformed lines

                current_data["teachers"][name] = {"availability": availability}

        unsaved_data = stored_data != current_data
        
        if unsaved_data:
            logger.debug("Unsaved changes detected")
        else:
            logger.debug("No unsaved changes detected")
        
        return unsaved_data
        
    except Exception as e:
        logger.error(f"Error checking for unsaved changes: {e}")
        return False


def main_on_year_changed(window: QWidget, storage: Storage) -> None:
    """Handle change event for the year selection dropdown.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    def _handle_year_change():
        if _unsaved_changes(window, storage):
            msg = QMessageBox(window)
            msg.setWindowTitle("Save changes?")
            msg.setText("Do you want to save changes to the current year before switching?")
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Save)

            result = msg.exec()

            if result == QMessageBox.Save:
                main_on_save_clicked(window, storage)
                main_on_load_clicked(window, storage)
            elif result == QMessageBox.Discard:
                main_on_load_clicked(window, storage)
            elif result == QMessageBox.Cancel:
                # Revert the combo box to previous selection
                combo = window.ui.findChild(QComboBox, "comboYearSelect")
                combo.blockSignals(True)
                combo.setCurrentIndex(window.previous_year_index)
                combo.blockSignals(False)
                return
        else:
            logger.debug("No unsaved changes, proceeding to load new year data")
            main_on_load_clicked(window, storage)
            
        # Update the tracked previous year
        window.previous_year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        logger.debug(f"Updated previous_year to: {window.previous_year}")
    
    BaseHandler.safe_execute(_handle_year_change, parent=window)


def main_show_about(window: QWidget) -> None:
    """Show the about dialog.

    Args:
        window: Main application window instance
    """
    about_text = """<h2>SlotPlanner</h2>
    <p><b>Version:</b> 1.0.0</p>
    <p><b>Description:</b> Weekly Schedule Optimizer</p>
    <br>
    <p>A desktop application for intelligent weekly time slot planning using constraint optimization.</p>
    <p>Designed to assign children to available teachers or therapists based on preferences, availability, tandem rules, and other constraints.</p>
    <br>
    <p><b>Features:</b></p>
    <ul>
    <li>45-minute time slots with 15-minute raster</li>
    <li>Teacher and child availability management</li>
    <li>Tandem scheduling (pairs of children)</li>
    <li>Configurable optimization weights</li>
    <li>PDF export for weekly schedules</li>
    </ul>
    <br>
    <p><b>License:</b> MIT</p>
    """
    
    QMessageBox.about(window, "About SlotPlanner", about_text)