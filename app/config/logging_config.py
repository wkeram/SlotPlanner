"""Centralized logging configuration for SlotPlanner application.

This module provides a centralized logging configuration that can be imported
and used throughout the application to ensure consistent logging behavior.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class AppLogger:
    """Centralized logging configuration for the SlotPlanner application."""
    
    _instance: Optional['AppLogger'] = None
    _configured = False
    
    def __new__(cls) -> 'AppLogger':
        """Singleton pattern to ensure only one logger configuration."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger if not already configured."""
        if not self._configured:
            self.configure_logging()
    
    def configure_logging(
        self, 
        level: int = logging.INFO,
        log_file: str = "slotplanner.log",
        console_output: bool = True
    ) -> None:
        """Configure logging for the application.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file
            console_output: Whether to output logs to console
        """
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Remove existing handlers to avoid duplication
        root_logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Console handler (optional)
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Set specific logger levels for different modules
        self._configure_module_loggers()
        
        self._configured = True
    
    def _configure_module_loggers(self) -> None:
        """Configure logging levels for specific modules."""
        # GUI module - INFO level (show important events)
        logging.getLogger('app.gui').setLevel(logging.INFO)
        
        # Storage module - WARNING level (only show issues)
        logging.getLogger('app.storage').setLevel(logging.WARNING)
        
        # Handlers module - INFO level (show user interactions)
        logging.getLogger('app.handlers').setLevel(logging.INFO)
        
        # UI modules - WARNING level (only show issues)
        logging.getLogger('app.ui_teachers').setLevel(logging.WARNING)
        
        # Utils module - WARNING level (only show issues)
        logging.getLogger('app.utils').setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    def set_debug_mode(self, enabled: bool = True) -> None:
        """Enable or disable debug mode for detailed logging.
        
        Args:
            enabled: Whether to enable debug mode
        """
        level = logging.DEBUG if enabled else logging.INFO
        logging.getLogger().setLevel(level)
        
        # Update all handlers
        for handler in logging.getLogger().handlers:
            handler.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    app_logger = AppLogger()
    return app_logger.get_logger(name)


def set_debug_mode(enabled: bool = True) -> None:
    """Set debug mode for the entire application.
    
    Args:
        enabled: Whether to enable debug mode
    """
    app_logger = AppLogger()
    app_logger.set_debug_mode(enabled)