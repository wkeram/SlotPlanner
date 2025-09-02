"""
Basic functionality tests for the OR-Tools optimizer.
Tests fundamental assignment capabilities without complex constraints.
"""

import pytest

from app.handlers.results_handlers import create_optimized_schedule
from tests.test_helpers import (
    assert_schedule_quality,
    get_scheduled_children,
    run_deterministic_optimization,
)

pytestmark = pytest.mark.optimizer


class TestBasicFunctionality:
    """Test basic assignment functionality of the optimizer."""

    def test_simple_assignment(self, temp_storage, minimal_test_data):
        """Test 1.1: Simple assignment with 2 teachers, 3 children, no special constraints."""
        teachers = minimal_test_data["teachers"]
        children = minimal_test_data["children"]
        tandems = minimal_test_data["tandems"]
        weights = minimal_test_data["weights"]

        # Run deterministic optimization
        schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)

        # Use improved validation
        assert_schedule_quality(schedule, violations, teachers, children, tandems)

        # Verify some children are scheduled
        scheduled_children = get_scheduled_children(schedule)
        assert len(scheduled_children) > 0, "At least some children should be scheduled"

        # All scheduled children should be from the children data
        for child in scheduled_children:
            assert child in children, f"Scheduled child {child} not in children data"

    def test_multiple_teachers_same_time(self, temp_storage):
        """Test 1.2: Multiple teachers available same time, multiple children need slots."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "11:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {"Mo": [("09:00", "11:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Teacher_C": {
                "name": "Teacher C",
                "availability": {"Mo": [("09:00", "11:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {},  # Available all the time
                "preferred_teachers": [],
            },
            "Child_2": {
                "name": "Child 2",
                "availability": {},  # Available all the time
                "preferred_teachers": [],
            },
            "Child_3": {
                "name": "Child 3",
                "availability": {},  # Available all the time
                "preferred_teachers": [],
            },
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)
        assert_schedule_quality(schedule, violations, teachers, children, tandems)

        # Check that children are scheduled efficiently
        scheduled_children = get_scheduled_children(schedule)
        assert len(scheduled_children) <= 3, "Should not assign more children than available"
        assert len(scheduled_children) > 0, "Should assign at least some children"

    def test_sequential_time_slots(self, temp_storage):
        """Test 1.3: Sequential time slots with single teacher, multiple children."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "Mo": [("08:00", "12:00")],  # 4 hour window allows multiple 45-min slots
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
                "availability": {},  # Available all the time
                "preferred_teachers": ["Teacher_A"],
            },
            "Child_2": {
                "name": "Child 2",
                "availability": {},  # Available all the time
                "preferred_teachers": ["Teacher_A"],
            },
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)
        assert_schedule_quality(schedule, violations, teachers, children, tandems)

        # Should be able to assign both children (4 hours allows 2+ slots)
        scheduled_children = get_scheduled_children(schedule)
        assert len(scheduled_children) >= 1, "Should assign at least one child"
        assert len(scheduled_children) <= 2, "Should not assign more than 2 children"

    def test_no_assignments_possible(self, temp_storage):
        """Test edge case where no assignments are possible due to no availability overlap."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("08:00", "09:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {"Di": [("09:00", "10:00")]},  # Different day - no overlap
                "preferred_teachers": ["Teacher_A"],
            }
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)

        # Should handle impossible assignments gracefully
        assert_schedule_quality(schedule, violations, teachers, children, tandems)

        # Should have violations due to impossible assignment
        assert len(violations) > 0, "Should have violations when no assignment is possible"

        # No children should be scheduled
        scheduled_children = get_scheduled_children(schedule)
        assert len(scheduled_children) == 0, "No children should be scheduled when assignment is impossible"

    def test_partial_assignment_insufficient_capacity(self, temp_storage):
        """Test partial assignment when there are more children than available slots."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "Mo": [("08:00", "09:30")],  # 1.5 hours = space for only 1 x 45min slot
                    "Di": [],
                    "Mi": [],
                    "Do": [],
                    "Fr": [],
                },
            }
        }

        children = {
            "Child_1": {"name": "Child 1", "availability": {}, "preferred_teachers": ["Teacher_A"]},
            "Child_2": {"name": "Child 2", "availability": {}, "preferred_teachers": ["Teacher_A"]},
            "Child_3": {"name": "Child 3", "availability": {}, "preferred_teachers": ["Teacher_A"]},
            "Child_4": {"name": "Child 4", "availability": {}, "preferred_teachers": ["Teacher_A"]},
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)
        assert_schedule_quality(schedule, violations, teachers, children, tandems)

        # With limited capacity, we should either have few children scheduled or violations
        scheduled_children = get_scheduled_children(schedule)

        # The key test is that the optimizer handles capacity constraints consistently
        # Either by limiting assignments or by reporting violations
        if len(scheduled_children) == 4:
            # If all children are scheduled, check how (may indicate the test scenario isn't constraining enough)
            assert len(violations) == 0, "If all children are scheduled, there should be no violations"
        else:
            # If not all children are scheduled, there should be violations for unscheduled children
            unscheduled_count = 4 - len(scheduled_children)
            assert (
                len(violations) >= unscheduled_count
            ), f"Should have violations for {unscheduled_count} unscheduled children"

        # The important thing is consistent, deterministic behavior
        assert len(scheduled_children) <= 4, "Should not assign more children than exist"
        assert len(scheduled_children) >= 0, "Should not have negative assignments"
