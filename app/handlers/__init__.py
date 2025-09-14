"""Event handlers package for SlotPlanner application.

This package contains organized event handlers for different UI components
and functionality areas.
"""

# Import specific functions that are used by the GUI
from .child_handlers import *  # noqa: F403
from .main_handlers import *  # noqa: F403
from .main_handlers import _unsaved_changes
from .settings_handlers import *  # noqa: F403

__all__ = [
    # Re-export all imported functions for backward compatibility
    "_unsaved_changes",
]
