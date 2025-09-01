# Contributing to SlotPlanner

Thank you for your interest in contributing to SlotPlanner! This guide will help you understand our development process and quality standards.

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/wkeram/SlotPlanner.git
cd SlotPlanner

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras --dev
```

### 2. Code Quality Standards

#### Linting & Formatting
We use several tools to maintain code quality:

```bash
# Format code with black
uv run black app/ tests/

# Sort imports with isort  
uv run isort app/ tests/

# Lint with ruff
uv run ruff check app/ tests/

# Type checking with mypy
uv run mypy app/
```

#### Pre-commit Setup (Recommended)
```bash
uv add pre-commit
uv run pre-commit install
```

This will automatically run linting and formatting before each commit.

### 3. Testing Requirements

All code contributions must include appropriate tests:

#### Test Categories
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **UI Tests**: Test GUI functionality (use pytest-qt)
- **Performance Tests**: Test scalability and performance

#### Running Tests
```bash
# Quick validation during development
uv run python tests/test_runner.py fast

# Full test suite
uv run python tests/test_runner.py all

# Coverage report
uv run python tests/test_runner.py coverage

# Specific test categories
uv run python tests/test_runner.py optimizer
uv run python tests/test_runner.py ui
```

#### Test Requirements
- **Minimum 90% code coverage** for new code
- **All edge cases covered** for optimization logic
- **UI tests for all user interactions**
- **Performance tests for scalability-critical code**

## Pull Request Process

### 1. Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### 2. Commit Messages
Follow conventional commit format:
```
type(scope): description

feat(optimizer): add tandem scheduling with priority weights
fix(ui): resolve data loss when switching years
docs(testing): add comprehensive test scenarios documentation
test(optimizer): add edge case tests for constraint violations
```

### 3. PR Requirements

Before submitting a pull request:

#### Automated Checks
- [ ] All tests pass (`uv run python tests/test_runner.py all`)
- [ ] Code coverage maintained above 90%
- [ ] Linting passes (`uv run ruff check app/ tests/`)
- [ ] Formatting passes (`uv run black --check app/ tests/`)
- [ ] Type checking passes (`uv run mypy app/`)

#### Manual Checks
- [ ] Documentation updated (README, docstrings, comments)
- [ ] CLAUDE.md updated if commands/architecture changed
- [ ] Test scenarios documented for complex features
- [ ] UI changes include screenshots/videos if applicable
- [ ] Breaking changes clearly documented

### 4. PR Template

When creating a PR, include:

```markdown
## Summary
Brief description of the changes and why they're needed.

## Changes
- List of specific changes made
- New features added
- Bugs fixed
- Refactoring performed

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated  
- [ ] UI tests added/updated (if applicable)
- [ ] Performance impact tested
- [ ] Manual testing completed

## Documentation
- [ ] README updated
- [ ] Code comments added
- [ ] API documentation updated
- [ ] Test documentation updated

## Breaking Changes
List any breaking changes and migration steps.

## Screenshots
Include screenshots for UI changes.
```

## CI/CD Pipeline

### Automated Checks
Your PR will automatically trigger:

1. **PR Checks** (`pr-checks.yml`)
   - Linting and formatting validation
   - Quick test suite
   - Documentation checks
   - Dependency validation
   - Code size impact analysis

2. **Full Test Suite** (`test.yml`)
   - Cross-platform testing (Windows, macOS, Linux)
   - Multiple Python versions (3.11, 3.12, 3.13)
   - UI tests with virtual display
   - Coverage reporting
   - Performance testing
   - Security scanning

### Quality Gates
All checks must pass before merge:
- ✅ All tests passing on all platforms
- ✅ Code coverage above 90%
- ✅ No linting or formatting issues
- ✅ Documentation updated
- ✅ No security vulnerabilities
- ✅ Performance regression tests pass

## Architecture Guidelines

### Code Organization
```
app/
├── gui.py              # Main GUI initialization
├── handlers/           # Event handlers by category
│   ├── main_handlers.py    # Main window handlers
│   ├── teacher_handlers.py # Teacher management
│   ├── child_handlers.py   # Child management
│   └── tandem_handlers.py  # Tandem management
├── logic.py            # OR-Tools optimization engine
├── storage.py          # JSON data persistence
├── model.py            # Data structures
├── export_pdf.py       # PDF generation
└── utils.py            # Utilities and translations
```

### Design Principles
1. **Separation of Concerns**: UI, business logic, and data are separate
2. **Testability**: All components are testable in isolation
3. **Performance**: Optimize for large datasets (200+ children)
4. **Maintainability**: Clear code structure and comprehensive documentation
5. **User Experience**: Intuitive UI with clear feedback and validation

### Optimization Engine Guidelines
- Always validate constraints before solving
- Provide clear violation messages
- Handle edge cases gracefully (no data, impossible assignments)
- Include timing and performance metrics
- Support weight-based optimization objectives

### UI Development Guidelines
- Use Qt Designer for UI layout (`.ui` files)
- Implement proper input validation with user feedback
- Provide loading indicators for long operations
- Ensure responsive design for different screen sizes
- Include keyboard shortcuts for power users

## Getting Help

### Resources
- [Tests Documentation](tests/README.md) - Comprehensive testing guide
- [Optimizer Test Scenarios](OPTIMIZER_TEST_SCENARIOS.md) - Test case specifications  
- [CLAUDE.md](CLAUDE.md) - Development environment setup

### Communication
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for general questions
- **Reviews**: Maintainers will review PRs within 48 hours

### Common Issues

#### Test Environment Setup
```bash
# Linux: Install Qt dependencies
sudo apt-get install libxkbcommon-x11-0 libxcb-icccm4

# Windows/macOS: No additional setup needed
```

#### UI Test Failures
```bash
# Run with virtual display (Linux)
export QT_QPA_PLATFORM=offscreen
uv run python tests/test_runner.py ui

# Skip UI tests during development
uv run python tests/test_runner.py fast
```

#### Coverage Issues
```bash
# Generate detailed coverage report
uv run python tests/test_runner.py coverage
open htmlcov/index.html
```

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributor statistics

Thank you for contributing to SlotPlanner! 🎯