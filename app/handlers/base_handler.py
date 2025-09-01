"""Base handler class for common functionality.

This module provides base functionality and utilities shared across
all handler modules.
"""

import traceback
from typing import Callable, Any
from PySide6.QtWidgets import QWidget, QMessageBox
from app.config.logging_config import get_logger
from app.utils import show_error

logger = get_logger(__name__)


class BaseHandler:
    """Base class providing common handler functionality."""
    
    @staticmethod
    def safe_execute(func: Callable, *args, parent: QWidget = None, **kwargs) -> Any:
        """Execute a function with proper error handling and logging.
        
        Args:
            func: Function to execute safely
            *args: Positional arguments for the function
            parent: Parent widget for error dialogs
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result or None if error occurred
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            
            # Show error to user if parent widget is available
            error_parent = parent or (args[0] if args and isinstance(args[0], QWidget) else None)
            if error_parent:
                show_error(f"An error occurred in {func.__name__}:\n{str(e)}", error_parent)
            
            return None
    
    @staticmethod
    def confirm_action(parent: QWidget, title: str, message: str) -> bool:
        """Show a confirmation dialog to the user.
        
        Args:
            parent: Parent widget for the dialog
            title: Dialog title
            message: Confirmation message
            
        Returns:
            True if user confirmed, False otherwise
        """
        reply = QMessageBox.question(
            parent, 
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        return reply == QMessageBox.Yes
    
    @staticmethod
    def show_info(parent: QWidget, title: str, message: str) -> None:
        """Show an information dialog to the user.
        
        Args:
            parent: Parent widget for the dialog
            title: Dialog title
            message: Information message
        """
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def show_error(parent: QWidget, title: str, message: str) -> None:
        """Show an error dialog to the user.
        
        Args:
            parent: Parent widget for the dialog
            title: Dialog title
            error: Error message
        """
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def cleanup_widget(widget: QWidget) -> None:
        """Properly cleanup a widget and its children to prevent memory leaks.
        
        Args:
            widget: Widget to cleanup
        """
        if not widget:
            return
            
        try:
            # Disconnect all signals to prevent issues during cleanup
            widget.blockSignals(True)
            
            # Clean up child widgets recursively
            for child in widget.findChildren(QWidget):
                try:
                    child.blockSignals(True)
                    child.setParent(None)
                except Exception as e:
                    logger.warning(f"Error cleaning up child widget: {e}")
            
            # Set parent to None to ensure proper destruction
            widget.setParent(None)
            
            logger.debug(f"Successfully cleaned up widget: {widget.objectName()}")
            
        except Exception as e:
            logger.error(f"Error during widget cleanup: {e}")
            logger.error(traceback.format_exc())