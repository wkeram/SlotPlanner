# Optimizer Test Scenarios

This document describes comprehensive test scenarios for the SlotPlanner optimization engine, covering constraint satisfaction, performance edge cases, and weighted optimization objectives.

## Test Categories

### 1. Constraint Validation Tests (`test_constraints.py`)

#### Hard Constraint Tests
- **Teacher Unavailability**: Ensures teachers cannot be assigned to slots where they are unavailable
- **Child Availability Conflicts**: Validates that children cannot be scheduled outside their availability
- **Insufficient Teacher Capacity**: Tests handling when there aren't enough teacher slots for all children
- **Teacher Preference vs Availability**: Verifies that availability constraints override preference weights
- **Multiple Constraint Violations**: Tests complex scenarios with multiple simultaneous constraint conflicts
- **Empty Availability Handling**: Edge case testing for entities with no available time slots

### 2. Basic Functionality Tests (`test_basic_functionality.py`)

#### Core Assignment Logic
- **Simple Assignment**: Basic 1-teacher, 1-child assignment validation
- **Multiple Teachers Same Time**: Concurrent teacher assignments in the same time slot
- **Sequential Time Slots**: Assignment across different time periods
- **No Assignments Possible**: Graceful handling when no valid assignment exists
- **Partial Assignment Insufficient Capacity**: Behavior when only some children can be assigned

### 3. Weight Optimization Tests (`test_weight_optimization.py`)

#### Objective Function Testing
- **Teacher Preference Weight**: Validates prioritization of preferred teacher assignments
- **Early Time Preference Weight**: Tests scheduling children earlier in the day when preferred
- **Tandem Fulfillment Weight**: Ensures tandem pairs are scheduled together when possible
- **Balanced Weight Optimization**: Multi-objective optimization with competing priorities
- **Zero Weights Handling**: Edge case testing with disabled optimization objectives
- **Extreme Weight Values**: Behavior with very high/low weight configurations

### 4. Tandem Scheduling Tests (`test_tandem_scheduling.py`)

#### Tandem-Specific Logic
- **Basic Tandem Scheduling**: Simple 2-child tandem assignment
- **Tandem Priority Levels**: Different priority tandems competing for slots
- **Conflicting Tandem Preferences**: Tandems with different teacher preferences
- **Tandem Impossible Due to Availability**: Handling when tandem members have incompatible schedules
- **Multiple Tandems Optimization**: Complex scenarios with multiple tandems competing

### 5. Performance & Edge Cases (`test_performance_edge_cases.py`)

#### Scalability & Robustness
- **Large Dataset Performance**: Testing with 200+ children and 20+ teachers
- **Single Teacher Many Children**: Resource contention scenarios
- **Many Teachers Single Child**: Over-provisioned resource scenarios
- **Optimization Timeout Handling**: Behavior when solver exceeds time limits
- **Extremely Limited Availability**: Stress testing with minimal scheduling options
- **Solver Memory Usage**: Memory consumption validation for large problems

## Test Data Patterns

### Standard Test Configurations
- **Minimal Setup**: 1 teacher, 1 child, single time slot
- **Balanced Setup**: 3 teachers, 5 children, multiple time slots
- **Overloaded Setup**: High child-to-teacher ratios
- **Underutilized Setup**: High teacher-to-child ratios

### Availability Patterns
- **Full Week**: Monday-Friday, 8:00-17:00
- **Limited Hours**: Specific time windows (e.g., mornings only)
- **Fragmented**: Non-contiguous availability blocks
- **Overlapping**: Multiple entities sharing time slots
- **Exclusive**: No overlap in availability

### Weight Configurations
- **Default Weights**: Standard production values
- **Extreme Weights**: Testing boundary conditions (0, 20)
- **Competing Priorities**: High weights on conflicting objectives
- **Single Objective**: Only one weight > 0

## Validation Criteria

### Hard Constraint Compliance
1. No teacher assigned outside their availability
2. No child assigned outside their availability  
3. No teacher supervising more than capacity allows
4. Each child assigned exactly once per week
5. Tandem pairs share the same slot/teacher when assigned together

### Optimization Quality
1. Teacher preferences honored when possible
2. Early-preferred children scheduled earlier in the day
3. Successful tandem assignments when feasible
4. Teacher breaks respected (15-minute gaps preferred)
5. Minimal changes from previous schedules when re-planning

### Performance Standards
1. Solutions found within reasonable time limits (< 60 seconds for typical datasets)
2. Memory usage remains within acceptable bounds
3. Solver status properly reported (OPTIMAL, FEASIBLE, NO_SOLUTION)
4. Violation reports accurately identify constraint failures

## Test Execution

### Quick Tests (Development)
```bash
uv run python tests/test_runner.py optimizer
```

### Full Test Suite
```bash
uv run python tests/test_runner.py all
```

### Performance Testing
```bash
uv run python tests/test_runner.py performance
```

### Coverage Analysis
```bash
uv run python tests/test_runner.py coverage
```

## Expected Outcomes

### Success Conditions
- All hard constraints satisfied in feasible scenarios
- Optimization weights properly influence assignment quality
- Performance within acceptable bounds for production use
- Comprehensive violation reporting for debugging

### Failure Handling
- Graceful degradation when no solution exists
- Clear error messages for constraint violations
- Proper timeout handling for complex problems
- Memory management under high load

This test suite ensures the SlotPlanner optimizer is robust, performant, and reliable across all supported use cases.