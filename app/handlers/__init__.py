"""Event handlers package for SlotPlanner application.

This package contains organized event handlers for different UI components
and functionality areas.
"""

# Import handlers to maintain backward compatibility
from .main_handlers import *
from .teacher_handlers import *
from .child_handlers import *
from .tandem_handlers import *
from .settings_handlers import *
from .results_handlers import *

# Import private functions that are used by the GUI
from .main_handlers import _unsaved_changes