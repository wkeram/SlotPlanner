"""Main GUI application class for SlotPlanner.

This module contains the main application class that initializes the UI,
connects event handlers, and manages the overall application state.
"""

import sys
import traceback
from PySide6.QtWidgets import QApplication, QMainWindow, QComboBox, QPushButton, QSlider, QLabel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice
from app.storage import Storage
from app import handlers
from app.config.logging_config import get_logger
from app.ui_feedback import create_feedback_manager
from app.utils import get_translations
from datetime import datetime

logger = get_logger(__name__)


class SlotPlannerApp(QMainWindow):
    """Main application class for SlotPlanner."""

    def __init__(self):
        """Initialize the SlotPlanner application."""
        super().__init__()

        try:
            logger.info("Initializing SlotPlanner application")

            # Initialize storage and load path settings
            self.storage = Storage()
            from app.handlers.settings_handlers import load_path_settings

            load_path_settings(self.storage)
            logger.info("Storage initialized with custom paths")

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
                button_load.clicked.connect(lambda: handlers.main_on_load_clicked(self, self.storage))
                logger.debug("Connected buttonLoad")
            else:
                logger.warning("buttonLoad not found")

            button_save = self.ui.findChild(QPushButton, "buttonSave")
            if button_save:
                button_save.clicked.connect(lambda: handlers.main_on_save_clicked(self, self.storage))
                logger.debug("Connected buttonSave")
            else:
                logger.warning("buttonSave not found")

            combo_year = self.ui.findChild(QComboBox, "comboYearSelect")
            if combo_year:
                combo_year.currentTextChanged.connect(lambda: handlers.main_on_year_changed(self, self.storage))
                logger.debug("Connected comboYearSelect")
            else:
                logger.warning("comboYearSelect not found")

            # Teachers tab callbacks
            self._connect_button(
                "buttonAddTeacher", lambda: handlers.teacher_open_add_teacher_dialog(self, self.storage)
            )
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
            self._connect_button(
                "buttonResetWeightsToDefaults", lambda: handlers.settings_reset_weights(self, self.storage)
            )
            self._connect_button("buttonSaveWeights", lambda: handlers.settings_save_weights(self, self.storage))
            self._connect_button(
                "buttonSaveWeightsAsDefault", lambda: handlers.settings_save_weights_as_default(self, self.storage)
            )

            # Connect weight sliders
            self._connect_weight_sliders()

            # Storage path callbacks
            self._connect_button("buttonSelectDataPath", lambda: handlers.settings_select_data_path(self, self.storage))
            self._connect_button(
                "buttonSelectExportPath", lambda: handlers.settings_select_export_path(self, self.storage)
            )
            self._connect_button(
                "buttonResetPathsToDefaults", lambda: handlers.settings_reset_paths(self, self.storage)
            )

            # Language selection callback
            combo_language = self.ui.findChild(QComboBox, "comboLanguage")
            if combo_language:
                combo_language.currentTextChanged.connect(lambda: handlers.settings_language_changed(self, self.storage))
                logger.debug("Connected comboLanguage")
            else:
                logger.warning("comboLanguage not found")

            # Results tab callbacks
            self._connect_button("buttonCreateSchedule", lambda: handlers.results_create_schedule(self, self.storage))
            self._connect_button("buttonExportPDF", lambda: handlers.results_export_pdf(self, self.storage))

            # Schedule history callbacks
            self._connect_button(
                "buttonDeleteSchedule", lambda: handlers.main_on_delete_schedule_clicked(self, self.storage)
            )

            combo_history = self.ui.findChild(QComboBox, "comboScheduleHistory")
            if combo_history:
                combo_history.currentIndexChanged.connect(
                    lambda: handlers.main_on_schedule_history_changed(self, self.storage)
                )
                logger.debug("Connected comboScheduleHistory")
            else:
                logger.warning("comboScheduleHistory not found")

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

    def _connect_weight_sliders(self):
        """Connect weight sliders to update their corresponding value labels."""
        slider_configs = [
            ("sliderPreferredTeacher", "labelPreferredTeacherValue", "preferred_teacher"),
            ("sliderEarlySlot", "labelEarlySlotValue", "priority_early_slot"),
            ("sliderTandemFulfilled", "labelTandemFulfilledValue", "tandem_fulfilled"),
            ("sliderTeacherBreak", "labelTeacherBreakValue", "teacher_pause_respected"),
            ("sliderPreserveExisting", "labelPreserveExistingValue", "preserve_existing_plan"),
        ]

        for slider_name, label_name, weight_key in slider_configs:
            try:
                slider = self.ui.findChild(QSlider, slider_name)
                label = self.ui.findChild(QLabel, label_name)

                if slider and label:
                    # Create a closure to capture the current values
                    def make_update_callback(lbl, w_key):
                        def update_label(value):
                            # Get current default value dynamically
                            from app.handlers.settings_handlers import _get_current_default_weights

                            current_defaults = _get_current_default_weights()
                            default_val = current_defaults.get(w_key, 5)
                            lbl.setText(get_translations("weight_value_format").format(value=value, default=default_val))

                        return update_label

                    slider.valueChanged.connect(make_update_callback(label, weight_key))
                    logger.debug(f"Connected {slider_name}")
                else:
                    if not slider:
                        logger.warning(f"{slider_name} not found")
                    if not label:
                        logger.warning(f"{label_name} not found")

            except Exception as e:
                logger.error(f"Failed to connect {slider_name}: {e}")
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
        if hasattr(self, "feedback_manager") and self.feedback_manager:
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

        # Load storage paths into UI
        handlers.settings_load_paths_into_ui(self, self.storage)
        
        # Load language setting into UI
        handlers.settings_load_language_into_ui(self, self.storage)

        # Initialize empty tables
        handlers.main_on_load_clicked(self, self.storage)

        # Update UI with current language translations
        self.update_ui_translations()

        if hasattr(self, "feedback_manager") and self.feedback_manager:
            self.feedback_manager.show_ready()

    def closeEvent(self, event):
        """Handle application close event with unsaved changes check."""
        # Check for unsaved changes before closing
        if handlers._unsaved_changes(self, self.storage):
            from PySide6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "Save Changes?",
                "You have unsaved changes. Do you want to save them before exiting?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
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

    def update_ui_translations(self):
        """Update all UI text with current translations."""
        try:
            # Window title
            self.setWindowTitle(get_translations("app_title"))
            
            # Main label
            label_main = self.ui.findChild(QLabel, "label")
            if label_main:
                label_main.setText(get_translations("app_name"))
            
            # Year selection label
            label_year = self.ui.findChild(QLabel, "comboYearSelectLabel") 
            if label_year:
                label_year.setText(get_translations("school_year"))
            
            # Tab titles - find the tab widget
            from PySide6.QtWidgets import QTabWidget
            tab_widget = self.ui.findChild(QTabWidget)
            if tab_widget:
                # Update tab titles
                tab_widget.setTabText(0, get_translations("teachers"))
                tab_widget.setTabText(1, get_translations("children")) 
                tab_widget.setTabText(2, get_translations("tandems"))
                tab_widget.setTabText(3, get_translations("settings"))
                tab_widget.setTabText(4, get_translations("results"))
            
            # Teachers tab buttons
            self._update_button_text("buttonAddTeacher", "add_teacher")
            self._update_button_text("buttonEditTeacher", "edit_teacher")
            self._update_button_text("buttonDeleteTeacher", "delete_teacher")
            
            # Children tab buttons
            self._update_button_text("buttonAddChild", "add_child")
            self._update_button_text("buttonEditChild", "edit_child")
            self._update_button_text("buttonDeleteChild", "delete_child")
            
            # Tandems tab buttons
            self._update_button_text("buttonAddTandem", "add_tandem")
            self._update_button_text("buttonEditTandem", "edit_tandem")
            self._update_button_text("buttonDeleteTandem", "delete_tandem")
            
            # Settings tab group boxes and labels
            self._update_group_box_text("groupBoxWeights", "optimization_weights")
            self._update_label_text("labelPreferredTeacher", "preferred_teacher")
            self._update_label_text("labelEarlySlot", "early_time_preference")
            self._update_label_text("labelTandemFulfilled", "tandem_fulfillment")
            self._update_label_text("labelTeacherBreak", "teacher_break_preference")
            self._update_label_text("labelPreserveExisting", "preserve_existing_plan")
            
            # Settings buttons
            self._update_button_text("buttonResetWeightsToDefaults", "reset_to_defaults")
            self._update_button_text("buttonSaveWeights", "save_for_current_year")
            self._update_button_text("buttonSaveWeightsAsDefault", "save_as_default")
            
            # Storage locations
            self._update_group_box_text("groupBoxStoragePaths", "storage_locations")
            self._update_label_text("labelDataPath", "data_storage_path")
            self._update_label_text("labelExportPath", "pdf_export_path")
            self._update_button_text("buttonSelectDataPath", "browse")
            self._update_button_text("buttonSelectExportPath", "browse")
            self._update_button_text("buttonResetPathsToDefaults", "reset_to_defaults")
            
            # Language settings
            self._update_group_box_text("groupBoxLanguage", "language_settings")
            self._update_label_text("labelLanguage", "interface_language")
            
            # Results tab
            self._update_button_text("buttonCreateSchedule", "create_schedule")
            self._update_button_text("buttonExportPDF", "export_to_pdf")
            self._update_group_box_text("groupBoxScheduleHistory", "saved_schedule_results")
            self._update_label_text("labelSelectSchedule", "select_result")
            self._update_button_text("buttonDeleteSchedule", "delete_selected")
            
            # Bottom buttons
            self._update_button_text("buttonAbout", "about")
            self._update_button_text("buttonExit", "exit")
            
            # Update weight slider value labels
            self._update_weight_slider_labels()
            
            # Update tooltips
            self._update_tooltips()
            
            logger.info("Updated UI translations")
            
        except Exception as e:
            logger.error(f"Error updating UI translations: {e}")
    
    def _update_button_text(self, button_name: str, translation_key: str):
        """Helper to update button text."""
        button = self.ui.findChild(QPushButton, button_name)
        if button:
            button.setText(get_translations(translation_key))
    
    def _update_label_text(self, label_name: str, translation_key: str):
        """Helper to update label text."""
        label = self.ui.findChild(QLabel, label_name)
        if label:
            label.setText(get_translations(translation_key))
    
    def _update_group_box_text(self, group_box_name: str, translation_key: str):
        """Helper to update group box title."""
        from PySide6.QtWidgets import QGroupBox
        group_box = self.ui.findChild(QGroupBox, group_box_name)
        if group_box:
            group_box.setTitle(get_translations(translation_key))
    
    def _update_weight_slider_labels(self):
        """Update weight slider value labels with current language."""
        from app.handlers.settings_handlers import _get_current_default_weights
        current_defaults = _get_current_default_weights()
        
        slider_configs = [
            ("sliderPreferredTeacher", "labelPreferredTeacherValue", "preferred_teacher"),
            ("sliderEarlySlot", "labelEarlySlotValue", "priority_early_slot"),
            ("sliderTandemFulfilled", "labelTandemFulfilledValue", "tandem_fulfilled"),
            ("sliderTeacherBreak", "labelTeacherBreakValue", "teacher_pause_respected"),
            ("sliderPreserveExisting", "labelPreserveExistingValue", "preserve_existing_plan"),
        ]
        
        for slider_name, label_name, weight_key in slider_configs:
            slider = self.ui.findChild(QSlider, slider_name)
            label = self.ui.findChild(QLabel, label_name)
            
            if slider and label:
                value = slider.value()
                default_val = current_defaults.get(weight_key, 5)
                label.setText(get_translations("weight_value_format").format(value=value, default=default_val))
    
    def _update_tooltips(self):
        """Update tooltips with current language."""
        # Settings tooltips
        button = self.ui.findChild(QPushButton, "buttonResetWeightsToDefaults")
        if button:
            button.setToolTip(get_translations("tooltip_reset_weights"))
        
        button = self.ui.findChild(QPushButton, "buttonSaveWeights") 
        if button:
            button.setToolTip(get_translations("tooltip_save_weights_current"))
            
        button = self.ui.findChild(QPushButton, "buttonSaveWeightsAsDefault")
        if button:
            button.setToolTip(get_translations("tooltip_save_weights_default"))
        
        # Storage path tooltips
        from PySide6.QtWidgets import QLineEdit
        line_edit = self.ui.findChild(QLineEdit, "lineEditDataPath")
        if line_edit:
            line_edit.setToolTip(get_translations("tooltip_data_storage_directory"))
            line_edit.setPlaceholderText(get_translations("default_data_path"))
            
        line_edit = self.ui.findChild(QLineEdit, "lineEditExportPath")
        if line_edit:
            line_edit.setToolTip(get_translations("tooltip_pdf_export_directory"))
            line_edit.setPlaceholderText(get_translations("default_export_path"))
        
        button = self.ui.findChild(QPushButton, "buttonSelectDataPath")
        if button:
            button.setToolTip(get_translations("tooltip_select_data_directory"))
            
        button = self.ui.findChild(QPushButton, "buttonSelectExportPath")
        if button:
            button.setToolTip(get_translations("tooltip_select_export_directory"))
            
        button = self.ui.findChild(QPushButton, "buttonResetPathsToDefaults")
        if button:
            button.setToolTip(get_translations("tooltip_reset_storage_paths"))
        
        # Language combo tooltip
        combo = self.ui.findChild(QComboBox, "comboLanguage")
        if combo:
            combo.setToolTip(get_translations("tooltip_select_interface_language"))
        
        # Schedule history tooltips
        combo = self.ui.findChild(QComboBox, "comboScheduleHistory")
        if combo:
            combo.setToolTip(get_translations("tooltip_select_schedule_result"))
            
        button = self.ui.findChild(QPushButton, "buttonDeleteSchedule")
        if button:
            button.setToolTip(get_translations("tooltip_delete_schedule_result"))


def run_application():
    """Create and run the SlotPlanner application."""
    app = QApplication(sys.argv)
    app.setApplicationName("SlotPlanner")
    app.setApplicationVersion("1.0.0")

    # Set application icon
    from PySide6.QtGui import QIcon

    app.setWindowIcon(QIcon("icons/slotplanner.ico"))

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
