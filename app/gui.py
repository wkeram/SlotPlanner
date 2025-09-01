"""Main GUI application class for SlotPlanner.

This module contains the main application class that initializes the UI,
connects event handlers, and manages the overall application state.
"""

import sys
import traceback
from PySide6.QtWidgets import QApplication, QMainWindow, QComboBox, QPushButton
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice
from app.storage import Storage
from app import handlers
from app.config.logging_config import get_logger
from app.ui_feedback import create_feedback_manager
from datetime import datetime

logger = get_logger(__name__)


class SlotPlannerApp(QMainWindow):
    """Main application class for SlotPlanner."""
    
    def __init__(self):
        """Initialize the SlotPlanner application."""
        super().__init__()
        
        try:
            logger.info("Initializing SlotPlanner application")
            
            # Initialize storage
            self.storage = Storage()
            logger.info("Storage initialized")
            
            # Track previous year for unsaved changes detection
            self.previous_year = None
            self.previous_year_index = 0
            
            # Load and setup UI
            self.setup_ui()
            self.setup_callbacks()
            self.setup_feedback_system()
            self.initialize_data()
            
            logger.info("SlotPlanner application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SlotPlanner: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def setup_ui(self):
        """Load the main UI from the .ui file."""
        loader = QUiLoader()
        ui_file = QFile("app/ui/main_window_v2.ui")
        
        if not ui_file.open(QIODevice.ReadOnly):
            error_msg = f"Cannot open main_window_v2.ui: {ui_file.errorString()}"
            logger.error(error_msg)
            return
            
        # Load the UI as a separate widget
        loaded_widget = loader.load(ui_file, None)
        ui_file.close()
        
        if loaded_widget:
            # Since the UI file defines a QMainWindow, we need to extract its central widget
            central_widget = loaded_widget.centralWidget()
            if central_widget:
                self.setCentralWidget(central_widget)
                # Store reference to the central widget for finding child widgets
                self.ui = central_widget
            else:
                # Fallback: set the loaded widget directly
                self.setCentralWidget(loaded_widget)
                self.ui = loaded_widget
                
            self.setWindowTitle("SlotPlanner - Weekly Schedule Optimizer")
            self.resize(1000, 700)
            logger.info("UI loaded successfully")
        else:
            logger.error("Failed to load main_window_v2.ui")
            # Create a basic fallback UI
            from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
            fallback_widget = QWidget()
            layout = QVBoxLayout(fallback_widget)
            label = QLabel("Error: Could not load main_window_v2.ui")
            layout.addWidget(label)
            self.setCentralWidget(fallback_widget)
            self.ui = fallback_widget
    
    def setup_callbacks(self):
        """Connect all UI element callbacks to their handlers."""
        
        try:
            # Main toolbar callbacks
            button_load = self.ui.findChild(QPushButton, "buttonLoad")
            if button_load:
                button_load.clicked.connect(
                    lambda: handlers.main_on_load_clicked(self, self.storage)
                )
                logger.debug("Connected buttonLoad")
            else:
                logger.warning("buttonLoad not found")
                
            button_save = self.ui.findChild(QPushButton, "buttonSave")
            if button_save:
                button_save.clicked.connect(
                    lambda: handlers.main_on_save_clicked(self, self.storage)
                )
                logger.debug("Connected buttonSave")
            else:
                logger.warning("buttonSave not found")
                
            combo_year = self.ui.findChild(QComboBox, "comboYearSelect")
            if combo_year:
                combo_year.currentTextChanged.connect(
                    lambda: handlers.main_on_year_changed(self, self.storage)
                )
                logger.debug("Connected comboYearSelect")
            else:
                logger.warning("comboYearSelect not found")
        
            # Teachers tab callbacks
            self._connect_button("buttonAddTeacher", lambda: handlers.teacher_open_add_teacher_dialog(self, self.storage))
            self._connect_button("buttonEditTeacher", lambda: handlers.teacher_edit_selected(self, self.storage))
            self._connect_button("buttonDeleteTeacher", lambda: handlers.teacher_delete_selected(self, self.storage))
            
            # Children tab callbacks
            self._connect_button("buttonAddChild", lambda: handlers.child_open_add_dialog(self, self.storage))
            self._connect_button("buttonEditChild", lambda: handlers.child_edit_selected(self, self.storage))
            self._connect_button("buttonDeleteChild", lambda: handlers.child_delete_selected(self, self.storage))
            
            # Tandems tab callbacks
            self._connect_button("buttonAddTandem", lambda: handlers.tandem_open_add_dialog(self, self.storage))
            self._connect_button("buttonEditTandem", lambda: handlers.tandem_edit_selected(self, self.storage))
            self._connect_button("buttonDeleteTandem", lambda: handlers.tandem_delete_selected(self, self.storage))
            
            # Settings tab callbacks
            self._connect_button("buttonResetWeights", lambda: handlers.settings_reset_weights(self, self.storage))
            self._connect_button("buttonSaveSettings", lambda: handlers.settings_save_weights(self, self.storage))
            
            # Results tab callbacks
            self._connect_button("buttonCreateSchedule", lambda: handlers.results_create_schedule(self, self.storage))
            self._connect_button("buttonExportPDF", lambda: handlers.results_export_pdf(self, self.storage))
            
            # Bottom toolbar callbacks
            self._connect_button("buttonAbout", lambda: handlers.main_show_about(self))
            self._connect_button("buttonExit", self.close)
            
        except Exception as e:
            logger.error(f"Error setting up callbacks: {e}")
            logger.error(traceback.format_exc())
    
    def _connect_button(self, button_name: str, callback):
        """Helper method to connect button with error checking."""
        try:
            button = self.ui.findChild(QPushButton, button_name)
            if button:
                # Wrap callback to catch exceptions
                def safe_callback():
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"Error in {button_name} callback: {e}")
                        logger.error(traceback.format_exc())
                        from PySide6.QtWidgets import QMessageBox
                        QMessageBox.critical(self, "Error", f"An error occurred:\n{str(e)}")
                
                button.clicked.connect(safe_callback)
                logger.debug(f"Connected {button_name}")
            else:
                logger.warning(f"{button_name} not found")
        except Exception as e:
            logger.error(f"Failed to connect {button_name}: {e}")
            logger.error(traceback.format_exc())
    
    def setup_feedback_system(self):
        """Initialize the UI feedback and validation system."""
        try:
            self.feedback_manager = create_feedback_manager(self)
            self.feedback_manager.show_ready()
            logger.info("UI feedback system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize UI feedback system: {e}")
            self.feedback_manager = None
    
    def initialize_data(self):
        """Initialize the application with default data and populate year dropdown."""
        if hasattr(self, 'feedback_manager') and self.feedback_manager:
            self.feedback_manager.show_status("Initializing application data...", show_progress=True)
        
        # Populate year dropdown with current and next school years
        current_year = datetime.now().year
        combo_year = self.ui.findChild(QComboBox, "comboYearSelect")
        
        # Add current and next 5 school years
        for i in range(6):
            year_start = current_year + i
            year_end = year_start + 1
            year_text = f"{year_start}_{year_end}"
            combo_year.addItem(year_text)
        
        # Set current year as default
        current_school_year = f"{current_year}_{current_year + 1}"
        combo_year.setCurrentText(current_school_year)
        self.previous_year = current_school_year
        
        # Initialize empty tables
        handlers.main_on_load_clicked(self, self.storage)
        
        if hasattr(self, 'feedback_manager') and self.feedback_manager:
            self.feedback_manager.show_ready()
    
    def closeEvent(self, event):
        """Handle application close event with unsaved changes check."""
        # Check for unsaved changes before closing
        if handlers._unsaved_changes(self, self.storage):
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, 
                'Save Changes?',
                'You have unsaved changes. Do you want to save them before exiting?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                handlers.main_on_save_clicked(self, self.storage)
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:  # Cancel
                event.ignore()
                return
        
        event.accept()


def run_application():
    """Create and run the SlotPlanner application."""
    app = QApplication(sys.argv)
    app.setApplicationName("SlotPlanner")
    app.setApplicationVersion("1.0.0")
    
    
    logger.info("Starting SlotPlanner application")
    
    try:
        window = SlotPlannerApp()
        window.show()
        
        logger.info("Application window shown successfully")
        return app.exec()
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        logger.error(traceback.format_exc())
        return 1