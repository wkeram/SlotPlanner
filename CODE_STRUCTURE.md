# SlotPlanner Code Structure

This document outlines the refactored code structure and hierarchy of the SlotPlanner application.

## Architecture Overview

The application follows a clean separation of concerns with the following layers:

```
SlotPlanner/
├── main.py                    # Root entry point
├── app/
│   ├── ui/                   # UI definition files
│   │   ├── main_window_v2.ui
│   │   ├── add_teacher.ui
│   │   ├── add_child.ui
│   │   └── add_tandem.ui
│   ├── handlers/             # Event handler modules
│   │   ├── __init__.py
│   │   ├── base_handler.py
│   │   ├── main_handlers.py
│   │   ├── teacher_handlers.py
│   │   ├── child_handlers.py
│   │   ├── tandem_handlers.py
│   │   ├── settings_handlers.py
│   │   └── results_handlers.py
│   ├── config/              # Configuration modules
│   │   ├── __init__.py
│   │   └── logging_config.py
│   ├── gui.py               # Main GUI class
│   ├── storage.py           # Data persistence
│   ├── ui_teachers.py       # UI table management
│   ├── utils.py             # Utility functions
│   └── ...
```

### 1. Application Layer (`main.py`)
- **Entry point**: Initializes logging and starts the GUI application
- **Dependencies**: `app.gui`, `app.config.logging_config`

### 2. GUI Layer (`app/gui.py`)
- **Main application class**: `SlotPlannerApp`
- **Responsibilities**: UI initialization, widget setup, callback registration
- **Dependencies**: Storage, handlers, logging configuration

### 3. Event Handling Layer (`app/handlers/`)
Organized into specialized modules:

#### `base_handler.py`
- **BaseHandler class**: Common functionality for all handlers
- **Safe execution**: Error handling wrapper for all handler functions
- **User interaction**: Confirmation dialogs and information messages

#### `main_handlers.py`
- **Application lifecycle**: Load, save, year changes
- **Data validation**: Unsaved changes detection
- **About dialog**: Application information

#### `teacher_handlers.py`
- **Teacher management**: Add, edit, delete teachers
- **Dialog management**: Teacher add/edit dialog handling
- **Availability management**: Time slot configuration

#### `child_handlers.py`
- **Child management**: Add, edit, delete children (TODO)

#### `tandem_handlers.py`
- **Tandem management**: Add, edit, delete tandems (TODO)

#### `settings_handlers.py`
- **Configuration management**: Optimization weights
- **Settings persistence**: Save/load application settings

#### `results_handlers.py`
- **Schedule creation**: OR-Tools integration (TODO)
- **PDF export**: Schedule export functionality (TODO)

### 4. Data Layer (`app/storage.py`)
- **Storage class**: JSON-based data persistence
- **School year management**: Per-year data files
- **CRUD operations**: Create, read, update, delete data
- **Error handling**: Proper logging for I/O operations

### 5. UI Management Layer (`app/ui_teachers.py`)
- **Table management**: Refresh and update UI tables
- **Data presentation**: Format data for display
- **Widget configuration**: Table headers, sizing, etc.

### 6. Utility Layer (`app/utils.py`)
- **Translations**: Multi-language support
- **Error dialogs**: User-friendly error messaging
- **Common utilities**: Shared helper functions

### 7. Configuration Layer (`app/config/`)

#### `logging_config.py`
- **AppLogger class**: Centralized logging configuration
- **Module-specific levels**: Different log levels for different components
- **File and console output**: Configurable logging destinations
- **Debug mode**: Application-wide debug toggle

## Logging Hierarchy

### Log Levels by Module:
- **app.gui**: INFO - Shows important application events
- **app.handlers**: INFO - Shows user interactions and business logic
- **app.storage**: WARNING - Only shows I/O errors and important issues
- **app.ui_teachers**: WARNING - Only shows UI-related issues
- **app.utils**: WARNING - Only shows translation and utility issues

### Log Output:
- **File**: `slotplanner.log` - All messages at configured level
- **Console**: Stdout - All messages at configured level (optional)
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## Design Principles Applied

### 1. Separation of Concerns
- Each module has a single, well-defined responsibility
- UI logic separated from business logic
- Data persistence isolated in storage layer

### 2. Error Handling
- Centralized error handling in `BaseHandler.safe_execute()`
- Proper logging of all errors with stack traces
- User-friendly error messages in dialogs

### 3. Modularity
- Handler functions organized by feature area
- Reusable components (BaseHandler, logging config)
- Clear import structure and dependencies

### 4. Maintainability
- Consistent naming conventions
- Comprehensive docstrings
- Type hints where applicable
- Clean separation between TODO items and implemented features

### 5. Scalability
- Modular handler structure allows easy addition of new features
- Configurable logging system can be extended
- Storage layer supports multiple data types and years

## Migration Notes

### Changes Made:
1. **Removed print statements**: Replaced with proper logging calls
2. **Organized handlers**: Split monolithic handlers.py into specialized modules
3. **Centralized logging**: All modules use the same logging configuration
4. **Improved error handling**: Consistent error handling across all handlers
5. **Better structure**: Clear hierarchy and separation of concerns

### Backward Compatibility:
- The `app.handlers` package maintains the same public interface
- All existing handler functions are still available
- GUI callback registration remains unchanged

### Future Improvements:
- Complete TODO implementations for child, tandem, results functionality
- Add unit tests for all handler functions
- Implement comprehensive UI validation
- Add internationalization support