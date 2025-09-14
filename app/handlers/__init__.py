"""Event handlers package for SlotPlanner application.

This package contains organized event handlers for different UI components
and functionality areas.
"""

# Import specific functions that are used by the GUI
from .main_handlers import *
from .child_handlers import *
from .main_handlers import _unsaved_changes

__all__ = [
    # Re-export all imported functions for backward compatibility
    "_unsaved_changes",
]
