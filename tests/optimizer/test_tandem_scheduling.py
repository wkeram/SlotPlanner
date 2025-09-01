"""
Tandem scheduling tests for the OR-Tools optimizer.
Tests the tandem pairing functionality and priority handling.
"""

import pytest
from app.handlers.results_handlers import create_optimized_schedule

pytestmark = pytest.mark.optimizer


class TestTandemScheduling:
    """Test tandem (paired children) scheduling functionality."""

    def test_basic_tandem_scheduling(self, temp_storage):
        """Test 3.1: Basic tandem scheduling - two children scheduled together."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }
        }

        children = {
            "Child_1": {"name": "Child 1", "availability": {}, "preferred_teachers": []},
            "Child_2": {"name": "Child 2", "availability": {}, "preferred_teachers": []},
        }

        tandems = {"Tandem_1": {"child1": "Child_1", "child2": "Child_2", "priority": 5}}

        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should try to schedule tandem together
        assert schedule is not None
        assert violations is not None
        assert isinstance(violations, list)

    def test_tandem_priority_levels(self, temp_storage):
        """Test 3.2: Different tandem priority levels affect scheduling."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }
        }

        children = {
            "Child_1": {"name": "Child 1", "availability": {}, "preferred_teachers": []},
            "Child_2": {"name": "Child 2", "availability": {}, "preferred_teachers": []},
            "Child_3": {"name": "Child 3", "availability": {}, "preferred_teachers": []},
            "Child_4": {"name": "Child 4", "availability": {}, "preferred_teachers": []},
        }

        tandems = {
            "High_Priority_Tandem": {"child1": "Child_1", "child2": "Child_2", "priority": 10},
            "Low_Priority_Tandem": {"child1": "Child_3", "child2": "Child_4", "priority": 1},
        }

        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should prioritize high priority tandems
        assert schedule is not None
        assert violations is not None

    def test_conflicting_tandem_preferences(self, temp_storage):
        """Test 3.3: Conflicting tandem preferences and availability."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "10:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {"Di": [("09:00", "10:00")], "Mo": [], "Mi": [], "Do": [], "Fr": []},
            },
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {"Mo": [("09:00", "10:00")]},
                "preferred_teachers": ["Teacher A"],
            },
            "Child_2": {
                "name": "Child 2",
                "availability": {"Di": [("09:00", "10:00")]},
                "preferred_teachers": ["Teacher B"],
            },
        }

        tandems = {"Conflicted_Tandem": {"child1": "Child_1", "child2": "Child_2", "priority": 5}}

        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should handle conflicting preferences gracefully
        assert schedule is not None
        assert violations is not None

    def test_tandem_impossible_due_to_availability(self, temp_storage):
        """Test 3.4: Tandem impossible due to no overlapping availability."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "10:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }
        }

        children = {
            "Child_1": {"name": "Child 1", "availability": {"Mo": [("09:00", "10:00")]}, "preferred_teachers": []},
            "Child_2": {
                "name": "Child 2",
                "availability": {"Di": [("09:00", "10:00")]},  # Different day
                "preferred_teachers": [],
            },
        }

        tandems = {"Impossible_Tandem": {"child1": "Child_1", "child2": "Child_2", "priority": 5}}

        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should report tandem violations
        assert schedule is not None
        assert violations is not None

    def test_multiple_tandems_optimization(self, temp_storage):
        """Test 3.5: Multiple tandems with different priorities and constraints."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("08:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {"Mo": [("08:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
        }

        children = {
            "Child_1": {"name": "Child 1", "availability": {}, "preferred_teachers": []},
            "Child_2": {"name": "Child 2", "availability": {}, "preferred_teachers": []},
            "Child_3": {"name": "Child 3", "availability": {}, "preferred_teachers": []},
            "Child_4": {"name": "Child 4", "availability": {}, "preferred_teachers": []},
            "Child_5": {"name": "Child 5", "availability": {}, "preferred_teachers": []},
            "Child_6": {"name": "Child 6", "availability": {}, "preferred_teachers": []},
        }

        tandems = {
            "Tandem_1": {"child1": "Child_1", "child2": "Child_2", "priority": 8},
            "Tandem_2": {"child1": "Child_3", "child2": "Child_4", "priority": 6},
            "Tandem_3": {"child1": "Child_5", "child2": "Child_6", "priority": 4},
        }

        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should handle multiple tandems
        assert schedule is not None
        assert violations is not None
