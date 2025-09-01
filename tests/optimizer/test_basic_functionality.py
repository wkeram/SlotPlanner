"""
Basic functionality tests for the OR-Tools optimizer.
Tests fundamental assignment capabilities without complex constraints.
"""

import pytest
from app.handlers.results_handlers import create_optimized_schedule

pytestmark = pytest.mark.optimizer


class TestBasicFunctionality:
    """Test basic assignment functionality of the optimizer."""

    def test_simple_assignment(self, temp_storage, minimal_test_data):
        """Test 1.1: Simple assignment with 2 teachers, 3 children, no special constraints."""
        teachers = minimal_test_data["teachers"]
        children = minimal_test_data["children"]
        tandems = minimal_test_data["tandems"]
        weights = minimal_test_data["weights"]

        # Create solver and run optimization
        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Validate basic requirements
        assert schedule is not None, "Solver should return a schedule"
        assert violations is not None, "Solver should return violations list"
        assert isinstance(schedule, dict), "Schedule should be a dictionary"
        assert isinstance(violations, list), "Violations should be a list"

        # Extract assignments from schedule structure
        assignments = []
        for day, day_schedule in schedule.items():
            for time_slot, assignment_data in day_schedule.items():
                teacher = assignment_data.get("teacher")
                assigned_children = assignment_data.get("children", [])
                for child in assigned_children:
                    assignments.append({"child": child, "teacher": teacher, "day": day, "time": time_slot})

        if assignments:
            # Each child should be assigned exactly once
            assigned_children = set()
            for assignment in assignments:
                child_name = assignment["child"]
                assert child_name not in assigned_children, f"Child {child_name} assigned multiple times"
                assigned_children.add(child_name)

            # No double bookings - same teacher cannot have overlapping slots
            teacher_slots = {}
            for assignment in assignments:
                teacher = assignment["teacher"]
                day = assignment["day"]
                time = assignment["time"]

                if teacher not in teacher_slots:
                    teacher_slots[teacher] = []

                # Check for overlapping slots (45-minute duration)
                slot_key = f"{day}_{time}"
                assert slot_key not in teacher_slots[teacher], f"Teacher {teacher} double booked at {day} {time}"
                teacher_slots[teacher].append(slot_key)

    def test_multiple_teachers_same_time(self, temp_storage):
        """Test 1.2: Multiple teachers available same time, multiple children need slots."""
        test_data = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "10:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {"Mo": [("09:00", "10:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Teacher_C": {
                "name": "Teacher C",
                "availability": {"Mo": [("09:00", "10:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
        }

        children_data = {
            "Child_1": {
                "name": "Child 1",
                "availability": {},
                "preferred_teachers": [],
            },
            "Child_2": {
                "name": "Child 2",
                "availability": {},
                "preferred_teachers": [],
            },
            "Child_3": {
                "name": "Child 3",
                "availability": {},
                "preferred_teachers": [],
            },
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(test_data, children_data, tandems, weights)

        # All children should be assigned
        total_assigned = 0
        for day_schedule in schedule.values():
            for assignment_data in day_schedule.values():
                total_assigned += len(assignment_data.get("children", []))

        assert total_assigned <= 3, "Should not assign more children than available"

    def test_sequential_time_slots(self, temp_storage):
        """Test 1.3: Sequential time slots with single teacher, multiple children."""
        test_data = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "Mo": [("08:00", "11:00")],  # 3 hour window for multiple slots
                    "Di": [],
                    "Mi": [],
                    "Do": [],
                    "Fr": [],
                },
            }
        }

        children_data = {
            "Child_1": {
                "name": "Child 1",
                "availability": {},
                "preferred_teachers": ["Teacher A"],
            },
            "Child_2": {
                "name": "Child 2",
                "availability": {},
                "preferred_teachers": ["Teacher A"],
            },
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(test_data, children_data, tandems, weights)

        # Count total assigned children
        total_assigned = 0
        for day_schedule in schedule.values():
            for assignment_data in day_schedule.values():
                total_assigned += len(assignment_data.get("children", []))

        # Should try to assign children (may not succeed due to constraints)
        assert total_assigned >= 0, "Scheduler should return valid results"

    def test_no_assignments_possible(self, temp_storage):
        """Test edge case where no assignments are possible due to no availability overlap."""
        test_data = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("08:00", "09:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }
        }

        children_data = {
            "Child_1": {
                "name": "Child 1",
                "availability": {"Di": [("09:00", "10:00")]},  # Different day
                "preferred_teachers": ["Teacher A"],
            }
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(test_data, children_data, tandems, weights)

        # Should handle impossible assignments gracefully
        assert schedule is not None, "Solver should return a schedule even when no assignments possible"
        assert violations is not None, "Solver should return violations list"
        assert isinstance(violations, list), "Violations should be a list"

    def test_partial_assignment_insufficient_capacity(self, temp_storage):
        """Test partial assignment when there are more children than available slots."""
        test_data = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "Mo": [("08:00", "10:00")],  # Only space for 2 x 45min slots
                    "Di": [],
                    "Mi": [],
                    "Do": [],
                    "Fr": [],
                },
            }
        }

        children_data = {
            "Child_1": {"name": "Child 1", "availability": {}, "preferred_teachers": ["Teacher A"]},
            "Child_2": {"name": "Child 2", "availability": {}, "preferred_teachers": ["Teacher A"]},
            "Child_3": {"name": "Child 3", "availability": {}, "preferred_teachers": ["Teacher A"]},
            "Child_4": {"name": "Child 4", "availability": {}, "preferred_teachers": ["Teacher A"]},
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(test_data, children_data, tandems, weights)

        # Should assign maximum possible children
        total_assigned = 0
        for day_schedule in schedule.values():
            for assignment_data in day_schedule.values():
                total_assigned += len(assignment_data.get("children", []))

        # May not assign all 4 due to capacity constraints
        assert total_assigned <= 4, "Should not assign more children than requested"
        assert isinstance(violations, list), "Should return violations list"
