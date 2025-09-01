"""Main application event handlers.

This module contains handlers for main application functionality like
loading, saving, year changes, and application lifecycle events.
"""

from PySide6.QtWidgets import QComboBox, QTableWidget, QMessageBox, QWidget, QSpinBox
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
        
        # Refresh all tables with loaded data and show feedback
        if hasattr(window, 'feedback_manager') and window.feedback_manager:
            window.feedback_manager.show_status("Refreshing tables...", show_progress=True)
        
        refresh_teacher_table(window.ui, data)
        refresh_children_table(window.ui, data)
        refresh_tandems_table(window.ui, data)
        
        if hasattr(window, 'feedback_manager') and window.feedback_manager:
            window.feedback_manager.show_success("Data loaded successfully")
        
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
        return _save_data_for_year(window, storage, year, show_feedback=True)
    
    BaseHandler.safe_execute(_save_data, parent=window)


def _save_data_for_year(window: QWidget, storage: Storage, year: str, show_feedback: bool = False) -> bool:
    """Save UI data for a specific year.
    
    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
        year: Specific year to save data for
        show_feedback: Whether to show user feedback messages
        
    Returns:
        True if save was successful, False otherwise
    """
    # Collect actual data from UI tables
    data = collect_data_from_ui(window, storage)
    
    success = storage.save(year, data)
    if success:
        logger.info(f"Successfully saved data for year {year}")
        if show_feedback:
            BaseHandler.show_info(window, "Save Successful", f"Data for {year} has been saved successfully.")
    else:
        logger.error(f"Failed to save data for year {year}")
        if show_feedback:
            BaseHandler.show_error(window, "Save Failed", f"Failed to save data for {year}")
        
    # Refresh tables to reflect saved state with feedback
    if show_feedback and hasattr(window, 'feedback_manager') and window.feedback_manager:
        window.feedback_manager.show_status("Updating tables...", show_progress=True)
        
        refresh_teacher_table(window.ui, data)
        refresh_children_table(window.ui, data)
        refresh_tandems_table(window.ui, data)
        
        if success:
            window.feedback_manager.show_success("Data saved and tables updated")
    
    return success


def collect_data_from_ui(window: QWidget, storage: Storage) -> dict:
    """Collect all current data from UI tables and form elements.
    
    Args:
        window: Main application window
        storage: Storage instance
        
    Returns:
        Complete data dictionary with all current UI state
    """
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    
    # Start with existing data to preserve non-UI data
    data = storage.load(year) or storage.get_default_data_structure()
    
    # Collect teachers data from table
    teachers_table = window.ui.findChild(QTableWidget, "tableTeachers")
    if teachers_table:
        teachers_data = {}
        
        for row in range(teachers_table.rowCount()):
            name_item = teachers_table.item(row, 0)
            avail_item = teachers_table.item(row, 1)
            
            if not name_item or not avail_item:
                continue
                
            teacher_name = name_item.text()
            availability = {}
            
            # Parse availability text
            for line in avail_item.text().split("\n"):
                if not line.strip():
                    continue
                    
                try:
                    # Expected format: "Mo: 08:00–17:00, 18:00–20:00"
                    day, rest = line.split(": ", 1)
                    slots = []
                    
                    for slot_text in rest.split(", "):
                        if "–" in slot_text:
                            start, end = slot_text.split("–")
                            slots.append([start.strip(), end.strip()])
                    
                    if slots:
                        availability[day] = slots
                        
                except ValueError:
                    logger.warning(f"Could not parse availability line: {line}")
                    continue
            
            teachers_data[teacher_name] = {"availability": availability}
        
        data["teachers"] = teachers_data
        logger.debug(f"Collected {len(teachers_data)} teachers from UI")
    
    # Collect children data from table
    children_table = window.ui.findChild(QTableWidget, "tableChildren")
    if children_table:
        children_data = {}
        
        for row in range(children_table.rowCount()):
            name_item = children_table.item(row, 0)
            early_item = children_table.item(row, 1)
            preferred_item = children_table.item(row, 2)
            avail_item = children_table.item(row, 3)
            
            if not name_item:
                continue
                
            child_name = name_item.text()
            
            # Parse early preference
            early_preference = False
            if early_item:
                early_preference = early_item.text().lower() in ["yes", "true", "1"]
            
            # Parse preferred teachers
            preferred_teachers = []
            if preferred_item:
                preferred_text = preferred_item.text()
                if preferred_text:
                    preferred_teachers = [t.strip() for t in preferred_text.split(",") if t.strip()]
            
            # Parse availability
            availability = {}
            if avail_item:
                for line in avail_item.text().split("\n"):
                    if not line.strip():
                        continue
                        
                    try:
                        day, rest = line.split(": ", 1)
                        slots = []
                        
                        for slot_text in rest.split(", "):
                            if "–" in slot_text:
                                start, end = slot_text.split("–")
                                slots.append([start.strip(), end.strip()])
                        
                        if slots:
                            availability[day] = slots
                            
                    except ValueError:
                        continue
            
            children_data[child_name] = {
                "early_preference": early_preference,
                "preferred_teachers": preferred_teachers,
                "availability": availability
            }
        
        data["children"] = children_data
        logger.debug(f"Collected {len(children_data)} children from UI")
    
    # Collect tandems data from table
    tandems_table = window.ui.findChild(QTableWidget, "tableTandems")
    if tandems_table:
        tandems_data = {}
        
        for row in range(tandems_table.rowCount()):
            name_item = tandems_table.item(row, 0)
            child1_item = tandems_table.item(row, 1)
            child2_item = tandems_table.item(row, 2)
            priority_item = tandems_table.item(row, 3)
            
            if not all([name_item, child1_item, child2_item]):
                continue
                
            tandem_name = name_item.text()
            child1 = child1_item.text()
            child2 = child2_item.text()
            
            # Parse priority
            priority = 5  # Default
            if priority_item:
                try:
                    priority = int(priority_item.text())
                except ValueError:
                    priority = 5
            
            tandems_data[tandem_name] = {
                "child1": child1,
                "child2": child2,
                "priority": priority
            }
        
        data["tandems"] = tandems_data
        logger.debug(f"Collected {len(tandems_data)} tandems from UI")
    
    # Collect optimization weights from settings tab
    weights = {}
    weight_widgets = {
        "preferred_teacher": "spinPreferredTeacher",
        "priority_early_slot": "spinEarlySlot",
        "tandem_fulfilled": "spinTandemFulfilled",
        "teacher_pause_respected": "spinTeacherBreak",
        "preserve_existing_plan": "spinPreserveExisting"
    }
    
    for key, widget_name in weight_widgets.items():
        spin_box = window.ui.findChild(QSpinBox, widget_name)
        if spin_box:
            weights[key] = spin_box.value()
        else:
            # Use default if widget not found
            defaults = {
                "preferred_teacher": 5,
                "priority_early_slot": 3,
                "tandem_fulfilled": 4,
                "teacher_pause_respected": 1,
                "preserve_existing_plan": 10
            }
            weights[key] = defaults.get(key, 5)
    
    data["weights"] = weights
    logger.debug(f"Collected optimization weights: {weights}")
    
    return data


def _force_reload_year_data(window: QWidget, storage: Storage) -> None:
    """Force reload data for the currently selected year.
    
    Args:
        window: Main application window
        storage: Storage instance
    """
    year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
    data = storage.load(year) or storage.get_default_data_structure()
    
    logger.info(f"Force reloading data for year {year}")
    
    # Show loading feedback
    if hasattr(window, 'feedback_manager') and window.feedback_manager:
        window.feedback_manager.show_status(f"Loading data for {year}...", show_progress=True)
    
    # Clear and refresh all tables with new year data
    refresh_teacher_table(window.ui, data)
    refresh_children_table(window.ui, data)
    refresh_tandems_table(window.ui, data)
    
    # Load optimization weights from data into UI
    _load_weights_into_ui(window, data)
    
    if hasattr(window, 'feedback_manager') and window.feedback_manager:
        window.feedback_manager.show_success(f"Data for {year} loaded successfully")


def _load_weights_into_ui(window: QWidget, data: dict) -> None:
    """Load optimization weights from data into the settings UI.
    
    Args:
        window: Main application window
        data: Data dictionary containing weights
    """
    weights = data.get("weights", {})
    
    weight_widgets = {
        "preferred_teacher": "spinPreferredTeacher",
        "priority_early_slot": "spinEarlySlot",
        "tandem_fulfilled": "spinTandemFulfilled",
        "teacher_pause_respected": "spinTeacherBreak",
        "preserve_existing_plan": "spinPreserveExisting"
    }
    
    defaults = {
        "preferred_teacher": 5,
        "priority_early_slot": 3,
        "tandem_fulfilled": 4,
        "teacher_pause_respected": 1,
        "preserve_existing_plan": 10
    }
    
    for key, widget_name in weight_widgets.items():
        spin_box = window.ui.findChild(QSpinBox, widget_name)
        if spin_box:
            value = weights.get(key, defaults.get(key, 5))
            spin_box.setValue(value)
    
    logger.debug(f"Loaded weights into UI: {weights}")


def _unsaved_changes(window: QWidget, storage: Storage) -> bool:
    """Check if there are unsaved changes in the current year.
    
    DEPRECATED: Use _has_unsaved_changes_for_year instead.
    This function is kept for backward compatibility.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence

    Returns:
        True if there are unsaved changes, False otherwise
    """
    try:
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        return _has_unsaved_changes_for_year(window, storage, year)
    except Exception as e:
        logger.error(f"Error checking for unsaved changes: {e}")
        return False


def _has_unsaved_changes_for_year(window: QWidget, storage: Storage, year: str) -> bool:
    """Check if there are unsaved changes for a specific year by comparing stored data with UI state.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
        year: The year to check for unsaved changes

    Returns:
        True if there are unsaved changes, False otherwise
    """
    try:
        if not year:
            return False
            
        logger.debug(f"Checking for unsaved changes in year: {year}")
        
        # Load stored data for the specified year
        stored_data = storage.load(year)
        if stored_data is None:
            logger.debug(f"No stored data found for {year}, treating as new data")
            stored_data = storage.get_default_data_structure()

        # Build current_data from UI state - this represents what's currently shown
        current_ui_data = collect_data_from_ui(window, storage)
        
        # Compare only the relevant sections (ignore internal fields like schedule, violations)
        def normalize_data_for_comparison(data):
            """Extract only user-editable data for comparison."""
            return {
                "teachers": data.get("teachers", {}),
                "children": data.get("children", {}),
                "tandems": data.get("tandems", {}),
                "weights": data.get("weights", {})
            }
        
        stored_normalized = normalize_data_for_comparison(stored_data)
        current_normalized = normalize_data_for_comparison(current_ui_data)
        
        # Deep comparison
        has_changes = stored_normalized != current_normalized
        
        if has_changes:
            logger.debug(f"Unsaved changes detected for year {year}")
            # Log specific differences for debugging
            for section in ["teachers", "children", "tandems", "weights"]:
                if stored_normalized.get(section) != current_normalized.get(section):
                    logger.debug(f"Changes detected in section: {section}")
        else:
            logger.debug(f"No unsaved changes for year {year}")
        
        return has_changes
        
    except Exception as e:
        logger.error(f"Error checking for unsaved changes in year {year}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main_on_year_changed(window: QWidget, storage: Storage) -> None:
    """Handle change event for the year selection dropdown.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """
    def _handle_year_change():
        combo = window.ui.findChild(QComboBox, "comboYearSelect")
        current_selection = combo.currentText()
        
        # Get the previous year that was displayed in UI before this change
        previous_year = getattr(window, 'previous_year', None)
        
        logger.debug(f"Year change detected: {previous_year} -> {current_selection}")
        
        # If we have a previous year and it's different from current selection
        if previous_year and previous_year != current_selection:
            # Check for unsaved changes by comparing stored data with current UI state
            # The UI still contains data from the previous year at this point
            if _has_unsaved_changes_for_year(window, storage, previous_year):
                msg = QMessageBox(window)
                msg.setWindowTitle("Save changes?")
                msg.setText(f"Do you want to save changes to {previous_year} before switching to {current_selection}?")
                msg.setIcon(QMessageBox.Question)
                msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                msg.setDefaultButton(QMessageBox.Save)

                result = msg.exec()

                if result == QMessageBox.Save:
                    # Save the UI data (which belongs to previous_year) to the previous year
                    success = _save_data_for_year(window, storage, previous_year, show_feedback=False)
                    if success:
                        logger.info(f"Successfully saved changes for {previous_year} before switching")
                    # Force reload for new year
                    _force_reload_year_data(window, storage)
                elif result == QMessageBox.Discard:
                    logger.info(f"Discarded changes for {previous_year}")
                    # Force reload for new year
                    _force_reload_year_data(window, storage)
                elif result == QMessageBox.Cancel:
                    logger.info("Year change cancelled by user")
                    # Revert the combo box to previous selection
                    combo.blockSignals(True)
                    combo.setCurrentIndex(getattr(window, 'previous_year_index', 0))
                    combo.blockSignals(False)
                    return  # Don't update previous_year tracking
            else:
                logger.debug("No unsaved changes detected, proceeding to load new year data")
                # Force reload for new year
                _force_reload_year_data(window, storage)
        else:
            logger.debug("First year selection or same year selected, loading data")
            # Force reload for selected year
            _force_reload_year_data(window, storage)
            
        # Update tracking variables for next change
        window.previous_year = current_selection
        window.previous_year_index = combo.currentIndex()
        logger.debug(f"Updated previous_year tracking to: {window.previous_year}")
    
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