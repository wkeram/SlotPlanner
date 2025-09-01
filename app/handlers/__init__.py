"""Event handlers package for SlotPlanner application.

This package contains organized event handlers for different UI components
and functionality areas.
"""

# Import handlers to maintain backward compatibility
from .child_handlers import *
from .main_handlers import *

# Import specific functions that are used by the GUI
from .main_handlers import _unsaved_changes
from .results_handlers import *
from .settings_handlers import *
from .tandem_handlers import *
from .teacher_handlers import *

__all__ = [
    # Re-export all imported functions for backward compatibility
    "_unsaved_changes",
]
