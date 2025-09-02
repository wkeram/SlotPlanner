"""
Test helper functions for SlotPlanner optimizer tests.
Provides utilities for schedule validation, score calculation, and test assertions.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple

from app.handlers.results_handlers import create_optimized_schedule


def validate_schedule_structure(schedule: dict, violations: list) -> bool:
    """Validate that the schedule has the correct basic structure.

    Args:
        schedule: Schedule dictionary
        violations: Violations list

    Returns:
        True if structure is valid, False otherwise
    """
    if not isinstance(schedule, dict):
        return False
    if not isinstance(violations, list):
        return False

    days = ["Mo", "Di", "Mi", "Do", "Fr"]

    # Check that all days are present (can be empty)
    for day in days:
        if day not in schedule:
            schedule[day] = {}

    # Check structure of each day
    for day, day_schedule in schedule.items():
        if not isinstance(day_schedule, dict):
            return False
        for time_slot, assignment in day_schedule.items():
            if not isinstance(assignment, dict):
                return False
            if "teacher" not in assignment or "children" not in assignment:
                return False
            if not isinstance(assignment["children"], list):
                return False

    return True


def get_scheduled_children(schedule: dict) -> Set[str]:
    """Extract all children that are scheduled.

    Args:
        schedule: Schedule dictionary

    Returns:
        Set of child names that are scheduled
    """
    scheduled = set()
    for day_schedule in schedule.values():
        for assignment in day_schedule.values():
            scheduled.update(assignment.get("children", []))
    return scheduled


def get_teacher_assignments(schedule: dict, teacher_name: str) -> List[Tuple[str, str]]:
    """Get all time slots assigned to a specific teacher.

    Args:
        schedule: Schedule dictionary
        teacher_name: Name of teacher

    Returns:
        List of (day, time_slot) tuples
    """
    assignments = []
    for day, day_schedule in schedule.items():
        for time_slot, assignment in day_schedule.items():
            if assignment.get("teacher") == teacher_name:
                assignments.append((day, time_slot))
    return assignments


def check_no_double_bookings(schedule: dict) -> List[str]:
    """Check for teacher double bookings (overlapping 45-minute slots).

    Args:
        schedule: Schedule dictionary

    Returns:
        List of violation messages for double bookings
    """
    violations = []
    teacher_slots = {}

    for day, day_schedule in schedule.items():
        for time_slot, assignment in day_schedule.items():
            teacher = assignment.get("teacher")
            if teacher:
                if teacher not in teacher_slots:
                    teacher_slots[teacher] = []

                # Check for overlapping slots
                slot_start = datetime.strptime(time_slot, "%H:%M")
                slot_end = slot_start + timedelta(minutes=45)

                for existing_day, existing_time in teacher_slots[teacher]:
                    if day == existing_day:  # Same day
                        existing_start = datetime.strptime(existing_time, "%H:%M")
                        existing_end = existing_start + timedelta(minutes=45)

                        # Check for overlap
                        if not (slot_end <= existing_start or existing_end <= slot_start):
                            violations.append(
                                f"Teacher {teacher} double booked on {day}: " f"{existing_time} and {time_slot} overlap"
                            )

                teacher_slots[teacher].append((day, time_slot))

    return violations


def check_child_multiple_assignments(schedule: dict) -> List[str]:
    """Check that each child is assigned exactly once.

    Args:
        schedule: Schedule dictionary

    Returns:
        List of violation messages for multiple assignments
    """
    violations = []
    child_assignments = {}

    for day, day_schedule in schedule.items():
        for time_slot, assignment in day_schedule.items():
            for child in assignment.get("children", []):
                if child not in child_assignments:
                    child_assignments[child] = []
                child_assignments[child].append((day, time_slot))

    for child, assignments in child_assignments.items():
        if len(assignments) > 1:
            assignments_str = ", ".join([f"{day} {time}" for day, time in assignments])
            violations.append(f"Child {child} assigned multiple times: {assignments_str}")

    return violations


def calculate_preference_score(schedule: dict, children: dict, weights: dict) -> int:
    """Calculate the preference score for a schedule.

    Args:
        schedule: Schedule dictionary
        children: Children data
        weights: Optimization weights

    Returns:
        Total preference score
    """
    score = 0
    preferred_weight = weights.get("preferred_teacher", 0)

    for day, day_schedule in schedule.items():
        for time_slot, assignment in day_schedule.items():
            teacher = assignment.get("teacher")
            assigned_children = assignment.get("children", [])

            for child in assigned_children:
                child_data = children.get(child, {})
                preferred_teachers = child_data.get("preferred_teachers", [])

                if teacher in preferred_teachers:
                    score += preferred_weight

    return score


def calculate_early_slot_score(schedule: dict, children: dict, weights: dict) -> int:
    """Calculate the early slot preference score for a schedule.

    Args:
        schedule: Schedule dictionary
        children: Children data
        weights: Optimization weights

    Returns:
        Total early slot score
    """
    score = 0
    early_weight = weights.get("priority_early_slot", 0)

    for day, day_schedule in schedule.items():
        for time_slot, assignment in day_schedule.items():
            if time_slot < "12:00":  # Morning slot
                assigned_children = assignment.get("children", [])

                for child in assigned_children:
                    child_data = children.get(child, {})
                    if child_data.get("early_preference", False):
                        score += early_weight

    return score


def calculate_tandem_score(schedule: dict, tandems: dict, weights: dict) -> int:
    """Calculate the tandem fulfillment score for a schedule.

    Args:
        schedule: Schedule dictionary
        tandems: Tandem data
        weights: Optimization weights

    Returns:
        Total tandem score
    """
    score = 0
    tandem_weight = weights.get("tandem_fulfilled", 0)

    for tandem_name, tandem_data in tandems.items():
        child1 = tandem_data.get("child1")
        child2 = tandem_data.get("child2")
        priority = tandem_data.get("priority", 5)

        # Check if tandem is scheduled together
        for day, day_schedule in schedule.items():
            for time_slot, assignment in day_schedule.items():
                assigned_children = assignment.get("children", [])
                if child1 in assigned_children and child2 in assigned_children:
                    score += tandem_weight * priority
                    break

    return score


def calculate_total_optimization_score(schedule: dict, children: dict, tandems: dict, weights: dict) -> int:
    """Calculate the total optimization score for a schedule.

    Args:
        schedule: Schedule dictionary
        children: Children data
        tandems: Tandem data
        weights: Optimization weights

    Returns:
        Total optimization score
    """
    preference_score = calculate_preference_score(schedule, children, weights)
    early_score = calculate_early_slot_score(schedule, children, weights)
    tandem_score = calculate_tandem_score(schedule, tandems, weights)

    return preference_score + early_score + tandem_score


def run_deterministic_optimization(teachers: dict, children: dict, tandems: dict, weights: dict, seed: int = 42):
    """Run optimization with a fixed random seed for reproducible results.

    Args:
        teachers: Teacher data
        children: Children data
        tandems: Tandem data
        weights: Optimization weights
        seed: Random seed for reproducibility

    Returns:
        Tuple of (schedule, violations)
    """
    return create_optimized_schedule(teachers, children, tandems, weights, worker=None, random_seed=seed)


def assert_schedule_quality(schedule: dict, violations: list, teachers: dict, children: dict, tandems: dict):
    """Assert that a schedule meets basic quality requirements.

    Args:
        schedule: Schedule dictionary
        violations: Violations list
        teachers: Teacher data
        children: Children data
        tandems: Tandem data

    Raises:
        AssertionError: If schedule doesn't meet quality requirements
    """
    # Basic structure validation
    assert validate_schedule_structure(schedule, violations), "Schedule structure is invalid"

    # Check for double bookings
    double_booking_violations = check_no_double_bookings(schedule)
    assert not double_booking_violations, f"Double bookings found: {double_booking_violations}"

    # Check for multiple child assignments
    multiple_assignment_violations = check_child_multiple_assignments(schedule)
    assert not multiple_assignment_violations, f"Multiple assignments found: {multiple_assignment_violations}"

    # Check that scheduled children exist
    scheduled_children = get_scheduled_children(schedule)
    for child in scheduled_children:
        assert child in children, f"Scheduled child {child} not in children data"


def create_simple_deterministic_scenario():
    """Create a simple scenario with deterministic results for testing.

    Returns:
        Tuple of (teachers, children, tandems, weights) with expected deterministic outcome
    """
    teachers = {
        "Teacher_A": {
            "name": "Teacher A",
            "availability": {
                "Mo": [("09:00", "11:00")],  # 2 hours
                "Di": [],
                "Mi": [],
                "Do": [],
                "Fr": [],
            },
        }
    }

    children = {
        "Child_1": {
            "name": "Child 1",
            "availability": {
                "Mo": [("09:00", "11:00")],  # Matches teacher
                "Di": [],
                "Mi": [],
                "Do": [],
                "Fr": [],
            },
            "preferred_teachers": ["Teacher_A"],
        }
    }

    tandems = {}
    weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

    return teachers, children, tandems, weights


def expect_deterministic_schedule(
    teachers: dict,
    children: dict,
    tandems: dict,
    weights: dict,
    expected_assignments: List[Tuple[str, str, str, str]],
    seed: int = 42,
):
    """Test that a scenario produces expected deterministic assignments.

    Args:
        teachers: Teacher data
        children: Children data
        tandems: Tandem data
        weights: Optimization weights
        expected_assignments: List of (child, teacher, day, time) tuples
        seed: Random seed for reproducibility

    Returns:
        Tuple of (schedule, violations) for further testing
    """
    schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed)

    # Validate basic structure
    assert_schedule_quality(schedule, violations, teachers, children, tandems)

    # Check expected assignments
    actual_assignments = []
    for day, day_schedule in schedule.items():
        for time_slot, assignment in day_schedule.items():
            teacher = assignment.get("teacher")
            for child in assignment.get("children", []):
                actual_assignments.append((child, teacher, day, time_slot))

    # Sort for comparison
    expected_sorted = sorted(expected_assignments)
    actual_sorted = sorted(actual_assignments)

    assert actual_sorted == expected_sorted, f"Expected assignments {expected_sorted} but got {actual_sorted}"

    return schedule, violations
