# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important

- ALL instructions within this document MUST BE FOLLOWED, these are not optional unless explicitly stated.
- DO NOT edit more code than you have to.
- DO NOT WASTE TOKENS, be succinct and concise.

## Commands

### Development Setup
```bash
# Install uv package manager first (see README.md for installation)
uv venv
uv sync
uv run main.py
```

### Running the Application
```bash
uv run main.py
```

### Testing Commands
```bash
# Run all tests
uv run python tests/test_runner.py all

# Run only optimizer tests (no UI required)
uv run python tests/test_runner.py optimizer

# Run with coverage reporting
uv run python tests/test_runner.py coverage

# Run fast tests (development cycle)
uv run python tests/test_runner.py fast

# Check CI/CD readiness
uv run python scripts/check-status.py
```

### Code Quality
```bash
# Format code
uv run black app/ tests/

# Lint code
uv run ruff check app/ tests/

# Type checking
uv run mypy app/
```

### Version Management
```bash
# Show current version status
uv run python scripts/version-manager.py status

# Set a specific version
uv run python scripts/version-manager.py set 1.0.0

# Set version and create git tag
uv run python scripts/version-manager.py set 1.0.0 --tag

# Bump version parts
uv run python scripts/version-manager.py bump major
uv run python scripts/version-manager.py bump minor
uv run python scripts/version-manager.py bump patch

# Create git tag for current version
uv run python scripts/version-manager.py tag
```

## Project Status

SlotPlanner is a **production-ready** PySide6 desktop application with comprehensive CI/CD pipeline. Core functionality is implemented including:

- ✅ Teacher management with availability scheduling
- ✅ OR-Tools constraint optimization engine
- ✅ PDF export of weekly schedules
- ✅ JSON data persistence per school year
- ✅ Real-time UI feedback and validation
- 🔄 Child and tandem management (UI in progress)

Functional requirements are documented in `README.md` and must be respected when implementing new features.

## Code Editing Rules

- Clarity and Reuse: Every component and page should be modular and reusable. Avoid duplication by factoring repeated UI patterns into components.
- Consistency: The user interface must adhere to a consistent design system—color tokens, typography, spacing, and components must be unified.
- Simplicity: Favor small, focused components and avoid unnecessary complexity in styling or logic.
- Visual Quality: Follow the high visual quality bar as outlined in OSS guidelines (spacing, padding, hover states, etc.)

## UI/UX Best Practices

- Visual Hierarchy: Limit typography to 4–5 font sizes and weights for consistent hierarchy; use `text-xs` for captions and annotations; avoid `text-xl` unless for hero or major headings.
- Color Usage: Use 1 neutral base (e.g., `zinc`) and up to 2 accent colors.
- Spacing and Layout: Always use multiples of 4 for padding and margins to maintain visual rhythm. Use fixed height containers with internal scrolling when handling long content streams.
- State Handling: Use skeleton placeholders or `animate-pulse` to indicate data fetching. Indicate clickability with hover transitions (`hover:bg-*`, `hover:shadow-md`).
- **Translation Requirement**: ALL user-facing text strings must be translatable. Store all UI text in English and German in `app/config/translations.json` and use `get_translations()` function for loading. No hardcoded strings in UI elements are allowed.
- **Dialog Translation**: All dialog boxes must implement translation setup functions that update UI elements when dialogs are opened (see `_setup_*_dialog_translations()` pattern in handler modules).
- **Translation Coverage**: Use `scripts/verify_translations.py` to verify complete translation coverage before releases.

## Architecture

SlotPlanner is a PySide6-based desktop application for optimizing weekly schedules using constraint optimization. It assigns children to teachers/therapists in 45-minute time slots while respecting constraints and preferences.

### Core Structure
- **GUI**: Qt Designer UI files (`.ui`) define the interface layout
  - `main_window.ui` - Main interface with 5 tabs (Teachers, Children, Tandems, Settings, Results)
  - `add_teacher.ui` - Dialog for adding new teachers
- **Data Layer**: JSON-based persistence in `app/storage.py`
  - One file per school year: `data/YYYY_YYYY.json`
  - Stores teachers, children, tandems, optimization weights
- **Business Logic**: Constraint optimization in `app/handlers/results_handlers.py`
  - Uses OR-Tools for constraint programming
  - Time model: 45min slots, 15min raster (8:00, 8:15, etc.)
- **Event Handling**: UI interactions managed in `app/handlers/` modules
- **PDF Export**: Schedule generation in `app/handlers/results_handlers.py`

### Key Components
```
app/
├── handlers/           # Modular UI event handlers
│   ├── main_handlers.py      # Application lifecycle
│   ├── teacher_handlers.py   # Teacher management
│   ├── child_handlers.py     # Child management (TODO)
│   ├── tandem_handlers.py    # Tandem management (TODO)
│   ├── settings_handlers.py  # Weight configuration
│   └── results_handlers.py   # OR-Tools solver & PDF export
├── storage.py         # JSON data persistence layer
├── gui.py            # Main GUI initialization
├── ui_feedback.py    # Real-time validation feedback
├── utils.py          # Translations and error dialogs
├── version.py        # Centralized version management
├── config/           # Logging and configuration
scripts/
└── version-manager.py # Version management CLI tool
version.json          # Single source of truth for version
```

### Data Flow
1. UI collects data via table widgets and forms
2. Data persisted as JSON via `storage.py`
3. Solver (`results_handlers.py`) reads JSON + weights to optimize schedule
4. Results displayed in tables with violation reports
5. PDF export generates printable schedules

### Technologies
- **PySide6**: All UI components and Qt framework integration
- **OR-Tools**: Constraint programming optimization engine
- **ReportLab**: PDF generation for schedule exports
- **PyInstaller**: Creates standalone Windows executable via GitHub Actions

### UI Architecture
The application uses Qt Designer `.ui` files for UI layout, loaded at runtime via `QUiLoader`. Modular event handlers in `app/handlers/` connect UI interactions to business logic. All UI state changes trigger immediate data persistence to maintain consistency.

### Constraint Model
- Teachers have weekly availability patterns
- Children require exactly one 45-minute slot per week
- Tandems (pairs of children) can share slots with same teacher
- Weighted optimization objectives include teacher preferences, early time preferences, tandem fulfillment, and stability between planning cycles

## Versioning and Releases

SlotPlanner uses semantic versioning (SemVer) with centralized version management.

### Version Management System
- **Single Source of Truth**: `version.json` contains the authoritative version
- **Dynamic Loading**: Application and build system read version from `version.json`
- **Validation**: Version format and git tag conflicts are validated before release
- **Automation**: GitHub Actions workflow handles building, testing, and releases

### Release Process
1. **Pre-Release**: Run `uv run python scripts/version-manager.py status` to check current state
2. **Version Check**: Use `scripts/version-manager.py` to validate new version doesn't exist
3. **Set Version**: Run `uv run python scripts/version-manager.py set X.Y.Z` to update version
4. **GitHub Release**: Trigger "Version Release" workflow with version number
5. **Automated Steps**:
   - Validates version format and checks for existing tags
   - Runs tests and builds for all platforms (Windows, macOS, Linux)
   - Creates GitHub release with artifacts and auto-generated notes
   - Creates and pushes git tag to main branch

### Version Guidelines
- **Major** (X.0.0): Breaking changes, major new features
- **Minor** (X.Y.0): New features, backwards compatible
- **Patch** (X.Y.Z): Bug fixes, small improvements
- **Pre-release**: X.Y.Z-alpha.N, X.Y.Z-beta.N for testing versions

### Important Notes
- NEVER manually edit version numbers in code files
- Always use the version management script for consistency
- The GitHub Actions workflow ensures no duplicate tags are created
- Version updates are automatically synced between feature branches and main
