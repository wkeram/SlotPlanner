"""Real-time UI feedback and status management system.

This module provides real-time feedback to users through status updates,
progress indicators, and visual feedback for all UI interactions.
"""

from collections.abc import Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QSpinBox,
    QTableWidget,
    QWidget,
)

from app.config.logging_config import get_logger
from app.utils import get_translations
from app.validation import ValidationResult

logger = get_logger(__name__)


class StatusManager:
    """Manages status messages and progress indicators across the application."""

    def __init__(self, status_label: QLabel, progress_bar: QProgressBar):
        """Initialize status manager.

        Args:
            status_label: QLabel widget for status messages
            progress_bar: QProgressBar widget for progress indication
        """
        self.status_label = status_label
        self.progress_bar = progress_bar
        self._current_operation = None
        self._status_timer = QTimer()
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._clear_temporary_status)

    def show_status(self, message: str, duration: int = 0, show_progress: bool = False):
        """Show a status message with optional timeout.

        Args:
            message: Status message to display
            duration: Duration in milliseconds (0 for permanent)
            show_progress: Whether to show progress bar
        """
        logger.debug(f"Status: {message}")
        self.status_label.setText(message)

        if show_progress:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        else:
            self.progress_bar.setVisible(False)

        if duration > 0:
            self._status_timer.start(duration)
        else:
            self._status_timer.stop()

    def show_progress(self, message: str, current: int, maximum: int):
        """Show progress with specific values.

        Args:
            message: Progress message
            current: Current progress value
            maximum: Maximum progress value
        """
        self.status_label.setText(f"{message} ({current}/{maximum})")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(current)

    def show_success(self, message: str):
        """Show a success message with temporary duration.

        Args:
            message: Success message to display
        """
        self.show_status(f"✓ {message}", duration=3000)

    def show_error(self, message: str):
        """Show an error message.

        Args:
            message: Error message to display
        """
        self.show_status(f"✗ {message}")
        logger.error(f"UI Error: {message}")

    def show_ready(self):
        """Show ready status."""
        self.show_status(get_translations("status_ready"))
        self.progress_bar.setVisible(False)

    def _clear_temporary_status(self):
        """Clear temporary status and return to ready state."""
        self.show_ready()


class ValidationFeedback:
    """Provides real-time validation feedback for form inputs."""

    def __init__(self):
        """Initialize validation feedback system."""
        self._validation_timers = {}
        self._original_styles = {}

    def setup_widget_validation(
        self, widget: QWidget, validation_func: Callable, error_callback: Callable | None = None
    ):
        """Setup real-time validation for a widget.

        Args:
            widget: Widget to validate
            validation_func: Function that returns ValidationResult
            error_callback: Optional callback for handling errors
        """
        # Store original style
        if widget not in self._original_styles:
            self._original_styles[widget] = widget.styleSheet()

        # Create validation timer for delayed validation
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._validate_widget(widget, validation_func, error_callback))
        self._validation_timers[widget] = timer

        # Connect to widget signals based on type
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(lambda: self._schedule_validation(widget))
        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(lambda: self._schedule_validation(widget))
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(lambda: self._schedule_validation(widget))

    def _schedule_validation(self, widget: QWidget):
        """Schedule validation with delay to avoid excessive validation."""
        timer = self._validation_timers.get(widget)
        if timer:
            timer.start(500)  # 500ms delay

    def _validate_widget(self, widget: QWidget, validation_func: Callable, error_callback: Callable | None):
        """Perform validation and update widget appearance."""
        try:
            result = validation_func()
            self._apply_validation_style(widget, result)

            if error_callback and not result.is_valid:
                error_callback(result)

        except Exception as e:
            logger.error(f"Error in widget validation: {e}")
            self._apply_validation_style(widget, ValidationResult(False, [str(e)]))

    def _apply_validation_style(self, widget: QWidget, result: ValidationResult):
        """Apply visual feedback based on validation result."""
        original_style = self._original_styles.get(widget, "")

        if result.is_valid:
            if result.has_warnings:
                # Warning style: orange border
                widget.setStyleSheet(f"{original_style}; border: 2px solid orange;")
                widget.setToolTip(result.get_warning_message())
            else:
                # Success style: green border
                widget.setStyleSheet(f"{original_style}; border: 2px solid green;")
                widget.setToolTip("")
        else:
            # Error style: red border
            widget.setStyleSheet(f"{original_style}; border: 2px solid red;")
            widget.setToolTip(result.get_error_message())


class TableUpdateManager:
    """Manages real-time table updates and refresh operations."""

    def __init__(self):
        """Initialize table update manager."""
        self._update_timers = {}
        self._pending_updates = {}

    def schedule_table_refresh(self, table: QTableWidget, refresh_func: Callable, delay: int = 100):
        """Schedule a table refresh with debouncing.

        Args:
            table: Table widget to refresh
            refresh_func: Function to call for refresh
            delay: Delay in milliseconds before refresh
        """
        # Cancel existing timer
        if table in self._update_timers:
            self._update_timers[table].stop()

        # Store refresh function
        self._pending_updates[table] = refresh_func

        # Create new timer
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._execute_table_refresh(table))
        self._update_timers[table] = timer
        timer.start(delay)

    def _execute_table_refresh(self, table: QTableWidget):
        """Execute the pending table refresh."""
        refresh_func = self._pending_updates.get(table)
        if refresh_func:
            try:
                logger.debug(f"Refreshing table: {table.objectName()}")
                refresh_func()
                self._show_table_updated_feedback(table)
            except Exception as e:
                logger.error(f"Error refreshing table {table.objectName()}: {e}")
            finally:
                # Clean up
                if table in self._pending_updates:
                    del self._pending_updates[table]
                if table in self._update_timers:
                    del self._update_timers[table]

    def _show_table_updated_feedback(self, table: QTableWidget):
        """Show brief visual feedback that table was updated."""
        # Flash effect: briefly change background color
        original_style = table.styleSheet()
        table.setStyleSheet(f"{original_style}; background-color: #e6ffe6;")  # Light green

        # Restore original style after brief delay
        QTimer.singleShot(200, lambda: table.setStyleSheet(original_style))


class InteractionFeedback:
    """Provides feedback for user interactions like button clicks, form submissions."""

    @staticmethod
    def show_button_clicked(button):
        """Show visual feedback for button click."""
        original_style = button.styleSheet()
        button.setStyleSheet(f"{original_style}; background-color: #d4edda; border: 2px solid #28a745;")
        QTimer.singleShot(150, lambda: button.setStyleSheet(original_style))

    @staticmethod
    def show_operation_feedback(parent: QWidget, operation_name: str, success: bool, message: str = ""):
        """Show feedback for completed operations.

        Args:
            parent: Parent widget for message box
            operation_name: Name of the operation
            success: Whether operation was successful
            message: Additional message
        """
        if success:
            title = f"{operation_name} Successful"
            icon = QMessageBox.Information
            text = f"{operation_name} completed successfully."
        else:
            title = f"{operation_name} Failed"
            icon = QMessageBox.Warning
            text = f"{operation_name} failed."

        if message:
            text += f"\n\n{message}"

        msg_box = QMessageBox(icon, title, text, QMessageBox.Ok, parent)
        msg_box.setWindowTitle(title)
        msg_box.exec()


class UIFeedbackManager:
    """Central manager for all UI feedback systems."""

    def __init__(self, main_window):
        """Initialize with main window reference.

        Args:
            main_window: Main application window
        """
        self.main_window = main_window

        # Find status widgets
        self.status_label = main_window.ui.findChild(QLabel, "labelStatus")
        self.progress_bar = main_window.ui.findChild(QProgressBar, "progressBar")

        # Initialize subsystems
        if self.status_label and self.progress_bar:
            self.status_manager = StatusManager(self.status_label, self.progress_bar)
        else:
            logger.warning("Status widgets not found - status feedback disabled")
            self.status_manager = None

        self.validation_feedback = ValidationFeedback()
        self.table_manager = TableUpdateManager()
        self.interaction_feedback = InteractionFeedback()

    def setup_validation_feedback(self):
        """Setup validation feedback for all form inputs."""
        # This will be called after UI is fully loaded
        if not self.status_manager:
            return

        # Example: Setup teacher name validation
        # (This would be expanded for all form fields)
        logger.info("UI feedback system initialized")

    def show_status(self, message: str, **kwargs):
        """Proxy to status manager."""
        if self.status_manager:
            self.status_manager.show_status(message, **kwargs)

    def show_success(self, message: str):
        """Proxy to status manager."""
        if self.status_manager:
            self.status_manager.show_success(message)

    def show_error(self, message: str):
        """Proxy to status manager."""
        if self.status_manager:
            self.status_manager.show_error(message)

    def show_ready(self):
        """Proxy to status manager."""
        if self.status_manager:
            self.status_manager.show_ready()


def create_feedback_manager(main_window) -> UIFeedbackManager:
    """Factory function to create UI feedback manager.

    Args:
        main_window: Main application window

    Returns:
        Configured UIFeedbackManager instance
    """
    manager = UIFeedbackManager(main_window)
    manager.setup_validation_feedback()
    return manager
