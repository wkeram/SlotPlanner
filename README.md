# SlotPlanner

[![Tests](https://github.com/wkeram/SlotPlanner/workflows/Tests/badge.svg)](https://github.com/wkeram/SlotPlanner/actions/workflows/test.yml)
[![Coverage Status](https://codecov.io/gh/wkeram/SlotPlanner/branch/main/graph/badge.svg)](https://codecov.io/gh/wkeram/SlotPlanner)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/wkeram/SlotPlanner)](https://github.com/wkeram/SlotPlanner/releases)

**SlotPlanner** is a local desktop application for intelligent weekly time slot planning using constraint optimization.  
It is designed to assign children to available teachers or therapists based on preferences, availability, tandem rules, and other constraints.

---

## Functional Requirements

### 1. **Time Model**

* The planning is weekly (Monday–Friday).
* Slots are 45 minutes long, with 15-minute raster start times (e.g., 08:00, 08:15, …).
* The schedule structure is identical each week.

---

### 2. **Teachers**

* Each teacher has fixed weekly availability (per weekday and start time).
* A teacher can supervise:

  * One child per time slot, or
  * Two children **if they form a tandem**.
* **Soft constraint:** Teachers should preferably have a 15-minute break between slots.

---

### 3. **Children**

* Each child has weekly availability (same structure as teachers).
* Each child:

  * Can specify preferred teachers,
  * May be marked as **early-preferred** (should be scheduled earlier in the day),
  * Must be assigned **exactly one 45-minute slot per week**.

---

### 4. **Tandems**

* A tandem is a pair of children who should, if possible, be scheduled **together** in the same time slot with the same teacher.
* If a tandem is successfully scheduled, the teacher can supervise both at once.

---

### 5. **Optimization Goals**

All planning is optimized with the following soft objectives:

* Assign children to preferred teachers.
* Schedule early-preferred children earlier in the day.
* Schedule tandems together if possible.
* Minimize back-to-back appointments for teachers (encourage breaks).
* **Minimize changes** between previous and updated schedules when re-planning (stability preference).

All goals are weighted and configurable.

---

### 6. **Weight Configuration (User-Defined)**

Users can define how important each goal is:

```toml
preferred_teacher = 5
priority_early_slot = 3
tandem_fulfilled = 4
teacher_pause_respected = 1
preserve_existing_plan = 10
```

---

### 7. **Application Functionality**

* GUI-based desktop application (`tkinter`)
* Fully operable without command-line interaction
* Windows-compatible `.exe` (via GitHub Actions)
* No external Python installation needed for users
* Data is stored per school year as JSON (`data/YYYY_YYYY.json`)
* Supports:

  * Adding/editing teachers, children, tandems
  * Adjusting weights
  * Creating and updating schedules
  * Loading previous years’ plans for re-planning

---

### 8. **Output**

* **Per-teacher weekly plan** with time slots and assigned children/tandems
* Export as **printable PDF**
* Includes a **violation summary** (e.g. unmet preferences, late assignment, broken tandems)

---

### 9. **Result Structure**

The solution output includes:

* Teacher-to-slot assignment
* Per-child assignment + fulfilled preferences
* List of violations (e.g. "K1 not assigned to preferred teacher")
* Optimization config used
* (Optionally) reference to a previous plan for change minimization

---

### 10. **Progress Feedback**

* During solving, the app displays a progress indicator.
* After solving:

  * Shows status: **Optimal**, **Feasible**, or **No solution**
  * Displays solution runtime (e.g. “Solved in 42 seconds”)

---


## 🖥️ Features

| Feature                                         | Status    |
|------------------------------------------------|-----------|
| GUI-based app using `tkinter`                  | ⚙️ planned         |
| Create and manage teachers, children, tandems  | ⚙️ planned         |
| Weekly availability per teacher and child      | ⚙️ planned         |
| Time slot system (45 min slots, 15 min raster) | ⚙️ planned         |
| Tandem planning (2 children per slot)          | ⚙️ planned         |
| Soft teacher break rule (15 min preferred)     | ⚙️ planned         |
| Preference for early times (per child)         | ⚙️ planned         |
| Exactly one time slot per child per week       | ⚙️ planned         |
| Prioritized preferred teacher assignments      | ⚙️ planned         |
| Weight configuration for optimization goals    | ⚙️ planned         |
| Planning result per teacher                    | ⚙️ planned         |
| Export weekly plans as PDF                     | ⚙️ planned         |
| Conflict reporting (e.g., preferences unmet)   | ⚙️ planned         |
| JSON-based school year storage                 | ⚙️ planned         |
| Load/edit existing plans                       | ⚙️ planned         |
| Minimize plan changes on update (soft rule)    | ⚙️ planned         |
| Progress indication and status in GUI          | ⚙️ planned         |
| Windows `.exe` build via GitHub Actions        | ⚙️ planned |

---

## ⚙️ Configuration Weights

````
preferred_teacher = 5
priority_early_slot = 3
tandem_fulfilled = 4
teacher_pause_respected = 1
preserve_existing_plan = 10
````

All weights are adjustable in the GUI.

---

## 🗃️ Data Structure

All data is stored per school year in:

```
/data/YYYY_YYYY.json
```

Structure includes:

* Teachers (name, availability)
* Children (availability, preferences, priority)
* Tandems (pairs of children)
* Config weights
* Planning result + violations

---

## 🚀 Getting Started

1. Install Python (from [python.org](https://www.python.org))
2. Install `uv`:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. Setup and run:

   ```bash
   uv venv
   uv sync
   uv run main.py
   ```

---

## 🔧 Development & Testing

### Running Tests
```bash
# Install dependencies
uv sync --all-extras --dev

# Run all tests
uv run python tests/test_runner.py all

# Run only optimizer tests (no UI)
uv run python tests/test_runner.py optimizer

# Run with coverage
uv run python tests/test_runner.py coverage
```

### Test Coverage
The project maintains comprehensive test coverage including:
- **Optimizer Tests**: 25+ tests covering constraint optimization, weight handling, and edge cases
- **UI Tests**: Integration tests for GUI components and user workflows  
- **Performance Tests**: Scalability testing with large datasets (200+ children)
- **Cross-Platform Tests**: Windows, macOS, and Linux compatibility

See [tests/README.md](tests/README.md) for detailed testing documentation.

## 🚀 CI/CD Pipeline

### Automated Testing
- **Pull Request Checks**: Linting, formatting, quick tests, documentation checks
- **Main Branch Tests**: Full test suite across Python 3.11-3.13 on Windows, macOS, Linux
- **Nightly Tests**: Comprehensive testing, stress tests, compatibility checks
- **Coverage Reporting**: Automated coverage tracking with [Codecov](https://codecov.io)

### Release Pipeline
- **Automated Builds**: Cross-platform executables (Windows .exe, macOS .app, Linux AppImage)
- **Quality Gates**: All tests must pass before release
- **Artifact Management**: Test results, coverage reports, and binaries stored for 30-90 days

### Status Monitoring
- [![Tests](https://github.com/wkeram/SlotPlanner/workflows/Tests/badge.svg)](https://github.com/wkeram/SlotPlanner/actions/workflows/test.yml) - Main test suite status
- [![Coverage Status](https://codecov.io/gh/wkeram/SlotPlanner/branch/main/graph/badge.svg)](https://codecov.io/gh/wkeram/SlotPlanner) - Code coverage tracking
- Security scanning with automated vulnerability detection
- Performance regression monitoring

## 🧱 Build & Distribution

### Windows Executable
The app is built into a portable `.exe` using [PyInstaller](https://www.pyinstaller.org/) in GitHub Actions.
Releases can be downloaded from the [Releases](../../releases) section once available.

### Cross-Platform Support
- **Windows**: Standalone .exe executable
- **macOS**: .app bundle and .dmg installer
- **Linux**: AppImage and standalone executable

All builds are automatically tested and verified before release.

---

## 📄 License

MIT License – see [LICENSE](LICENSE)





