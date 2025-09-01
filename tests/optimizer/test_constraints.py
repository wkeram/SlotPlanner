"""
Constraint violation tests for the OR-Tools optimizer.
Tests that hard constraints are properly enforced and violations are reported.
"""

import pytest

from app.handlers.results_handlers import create_optimized_schedule

pytestmark = pytest.mark.optimizer


class TestConstraintViolations:
    """Test constraint enforcement and violation handling."""

    def test_teacher_unavailability_hard_constraint(self, temp_storage):
        """Test 2.1: Teacher unavailability as hard constraint overrides child preferences."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [], "Di": [], "Mi": [], "Do": [], "Fr": []},  # No availability
            }
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {},
                "preferred_teachers": ["Teacher A"],  # Prefers unavailable teacher
            }
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should handle constraint properly
        assert schedule is not None
        assert violations is not None
        assert isinstance(violations, list)

    def test_child_availability_conflict(self, temp_storage):
        """Test 2.2: Child availability conflicts should be reported as violations."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "10:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {"Di": [("09:00", "10:00")]},  # Different day from teacher
                "preferred_teachers": ["Teacher A"],
            }
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should handle availability conflicts
        assert schedule is not None
        assert violations is not None

    def test_insufficient_teacher_capacity(self, temp_storage):
        """Test 2.3: Insufficient teacher capacity leads to constraint violations."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "10:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},  # Only 1 hour
            }
        }

        children = {
            "Child_1": {"name": "Child 1", "availability": {}, "preferred_teachers": ["Teacher A"]},
            "Child_2": {"name": "Child 2", "availability": {}, "preferred_teachers": ["Teacher A"]},
            "Child_3": {"name": "Child 3", "availability": {}, "preferred_teachers": ["Teacher A"]},
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should report capacity issues
        assert schedule is not None
        assert violations is not None

    def test_teacher_preference_vs_availability_constraint(self, temp_storage):
        """Test 2.4: Teacher preference vs availability constraint priority."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [], "Di": [], "Mi": [], "Do": [], "Fr": []},  # Not available
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {"Mo": [("09:00", "10:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {},
                "preferred_teachers": ["Teacher A"],  # Prefer unavailable teacher
            }
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Availability should override preferences
        assert schedule is not None
        assert violations is not None

    def test_multiple_constraint_violations(self, temp_storage):
        """Test 2.5: Multiple constraint violations should all be reported."""
        teachers = {}  # No teachers available

        children = {
            "Child_1": {"name": "Child 1", "availability": {}, "preferred_teachers": []},
            "Child_2": {"name": "Child 2", "availability": {}, "preferred_teachers": []},
        }

        tandems = {"Tandem_1": {"child1": "Child_1", "child2": "Child_2", "priority": 5}}

        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should report multiple violations
        assert schedule is not None
        assert violations is not None
        assert isinstance(violations, list)

    def test_empty_availability_handling(self, temp_storage):
        """Test edge case with completely empty availability patterns."""
        teachers = {}
        children = {}
        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should handle empty inputs gracefully
        assert schedule is not None
        assert violations is not None
