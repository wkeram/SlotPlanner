# SlotPlanner Test Suite

Comprehensive test suite for the SlotPlanner application, covering optimizer functionality, UI components, and integration scenarios.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_runner.py           # Test execution utilities
├── README.md               # This file
├── optimizer/              # OR-Tools optimizer tests
│   ├── test_basic_functionality.py
│   ├── test_constraints.py
│   ├── test_weight_optimization.py
│   ├── test_tandem_scheduling.py
│   └── test_performance_edge_cases.py
└── ui/                     # UI and integration tests
    └── test_main_window.py
```

## Test Categories

### Optimizer Tests (`tests/optimizer/`)
- **Basic Functionality**: Core assignment logic and simple scenarios
- **Constraint Violations**: Hard constraint enforcement and violation reporting  
- **Weight Optimization**: Optimization weights and objective function behavior
- **Tandem Scheduling**: Tandem pair assignment with consecutive slots
- **Performance & Edge Cases**: Scalability, error handling, and extreme scenarios

### UI Tests (`tests/ui/`)
- **Main Window**: Core UI functionality and user interactions
- **Validation**: Input validation and error feedback
- **Integration**: End-to-end workflows and component integration

## Running Tests

### Prerequisites
Install test dependencies:
```bash
uv sync  # Installs pytest, pytest-qt, pytest-mock
```

### Quick Start
```bash
# Run all tests
uv run python tests/test_runner.py all

# Run only optimizer tests (no UI)
uv run python tests/test_runner.py optimizer

# Run only UI tests (requires display)
uv run python tests/test_runner.py ui

# Run fast tests (excludes slow performance tests)
uv run python tests/test_runner.py fast
```

### Direct pytest Usage
```bash
# All tests
uv run pytest tests/

# Optimizer tests only
uv run pytest tests/optimizer/ -m optimizer

# UI tests only  
uv run pytest tests/ui/ -m ui

# Fast tests only
uv run pytest tests/ -m "not slow and not performance"

# With coverage
uv run pytest tests/ --cov=app --cov-report=html
```

### Test Markers
Tests are organized using pytest markers:
- `@pytest.mark.optimizer`: OR-Tools optimizer tests
- `@pytest.mark.ui`: UI tests (require display)
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.performance`: Performance/scalability tests
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.edge_case`: Edge case and error handling tests

## Test Data Fixtures

The test suite includes comprehensive fixtures in `conftest.py`:

### Data Fixtures
- `minimal_test_data`: 2 teachers, 3 children for basic tests
- `tandem_test_data`: Tandem scheduling scenarios
- `complex_test_data`: 10 teachers, 25 children for performance tests
- `edge_case_data`: Extreme constraint scenarios
- `zero_weights_data`: Edge case weight configurations

### Utility Fixtures  
- `qapp`: QApplication instance for UI tests
- `temp_storage`: Temporary storage for test isolation
- `create_test_storage_with_data()`: Helper for storage setup

## Test Scenarios Coverage

### 1. Basic Functionality (9 tests)
- Simple assignment with multiple teachers/children
- Parallel assignments at same time slots
- Sequential time slot assignments
- No assignments possible scenarios
- Partial assignments with insufficient capacity

### 2. Constraint Violations (6 tests)
- Teacher unavailability hard constraints
- Child availability conflicts  
- Insufficient teacher capacity handling
- Teacher preference vs availability constraints
- Multiple simultaneous violations
- Empty availability handling

### 3. Weight Optimization (7 tests)
- Teacher preference weight influence
- Early time preference optimization
- Zero weights configuration
- Competing weight priorities
- Stability weight preservation
- Negative weights handling
- Weight score calculation

### 4. Tandem Scheduling (8 tests)
- Basic tandem consecutive slot assignment
- Limited availability overlap handling
- Tandem teacher preferences
- Impossible tandem graceful degradation  
- Multiple tandems with priorities
- Different teacher preferences in tandems
- Availability intersection enforcement

### 5. Performance & Edge Cases (12+ tests)
- Large scale assignments (50+ teachers, 200+ children)
- High constraint density scenarios
- Minimal availability windows
- No available teachers error handling
- Empty datasets
- Circular tandem dependencies
- Negative and extreme weight values
- Malformed data handling
- Memory usage monitoring

### 6. UI & Integration (15+ tests)
- Main window initialization
- Data table display and interaction
- Year selection and data loading
- Dialog functionality (add/edit)
- Optimization button integration
- Results display and PDF export
- Validation feedback
- Error recovery
- Performance with large datasets
- End-to-end workflows

## Continuous Integration

### GitHub Actions Integration
Tests can be integrated with GitHub Actions:

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
      - name: Run optimizer tests
        run: uv run python tests/test_runner.py optimizer
      - name: Run fast integration tests
        run: uv run python tests/test_runner.py fast
```

### Local Development
```bash
# Quick validation during development
uv run python tests/test_runner.py fast

# Full validation before commits  
uv run python tests/test_runner.py coverage

# Performance regression testing
uv run python tests/test_runner.py performance
```

## Test Development Guidelines

### Writing New Tests
1. Use appropriate fixtures from `conftest.py`
2. Add proper pytest markers
3. Include docstrings describing test scenarios
4. Follow naming convention: `test_<functionality>_<scenario>`
5. Use descriptive assertions with failure messages

### Test Data Design
- **Minimal datasets** for basic functionality
- **Targeted datasets** for specific constraint scenarios  
- **Large datasets** for performance validation
- **Edge case datasets** for error handling

### Performance Considerations
- Mark slow tests with `@pytest.mark.slow`
- Use `@pytest.mark.performance` for scalability tests
- Include timing assertions for performance-critical tests
- Monitor memory usage in large dataset tests

## Coverage Goals

- **Optimizer Logic**: 95%+ code coverage
- **Constraint Handling**: All constraint types tested
- **UI Components**: Core functionality covered
- **Integration Paths**: Major user workflows tested
- **Error Handling**: All error conditions covered

## Troubleshooting

### Common Issues
- **UI Tests Failing**: Ensure display available or use `pytest -m "not ui"`
- **Slow Tests**: Use `pytest -m "not slow"` for faster development cycles  
- **Import Errors**: Ensure `uv sync` has been run
- **Qt Issues**: May need `QT_QPA_PLATFORM=offscreen` on headless systems

### Debugging Tests
```bash
# Verbose output with detailed failure info
uv run pytest tests/ -v --tb=long

# Stop on first failure  
uv run pytest tests/ -x

# Run specific test
uv run pytest tests/optimizer/test_basic_functionality.py::TestBasicFunctionality::test_simple_assignment
```