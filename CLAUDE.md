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

## Requirements

Functional requirements and planned or implemented features are documented in `README.md`. Those requirements always need to be respected when implementing new features!

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

## Architecture

SlotPlanner is a PySide6-based desktop application for optimizing weekly schedules using constraint optimization. It assigns children to teachers/therapists in 45-minute time slots while respecting constraints and preferences.

### Core Structure
- **GUI**: Qt Designer UI files (`.ui`) define the interface layout
  - `main_window.ui` - Main interface with 5 tabs (Teachers, Children, Tandems, Settings, Results)  
  - `add_teacher.ui` - Dialog for adding new teachers
- **Data Layer**: JSON-based persistence in `app/storage.py`
  - One file per school year: `data/YYYY_YYYY.json`
  - Stores teachers, children, tandems, optimization weights
- **Business Logic**: Constraint optimization solver in `app/logic.py`
  - Uses OR-Tools for constraint programming
  - Time model: 45min slots, 15min raster (8:00, 8:15, etc.)
- **Event Handling**: UI interactions managed in `app/handlers.py`
- **PDF Export**: Schedule generation in `app/export_pdf.py`

### Key Components
```
app/
├── handlers.py      # UI event handlers and business logic flow
├── storage.py       # JSON data persistence layer
├── logic.py         # OR-Tools constraint solver
├── model.py         # Data structures (Teacher, Child, Tandem)
├── export_pdf.py    # PDF generation for schedules
├── utils.py         # Translations and error dialogs
├── gui.py           # Main GUI initialization
└── config/          # Translation files and settings
```

### Data Flow
1. UI collects data via table widgets and forms
2. Data persisted as JSON via `storage.py`
3. Solver (`logic.py`) reads JSON + weights to optimize schedule
4. Results displayed in tables with violation reports
5. PDF export generates printable schedules

### Technologies
- **PySide6**: All UI components and Qt framework integration
- **OR-Tools**: Constraint programming optimization engine  
- **ReportLab**: PDF generation for schedule exports
- **PyInstaller**: Creates standalone Windows executable via GitHub Actions

### UI Architecture
The application uses Qt Designer `.ui` files for UI layout, loaded at runtime via `QUiLoader`. Event handlers in `handlers.py` connect UI interactions to business logic. All UI state changes trigger immediate data persistence to maintain consistency.

### Constraint Model
- Teachers have weekly availability patterns
- Children require exactly one 45-minute slot per week
- Tandems (pairs of children) can share slots with same teacher
- Weighted optimization objectives include teacher preferences, early time preferences, tandem fulfillment, and stability between planning cycles