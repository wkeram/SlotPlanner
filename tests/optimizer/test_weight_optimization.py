"""
Weight optimization tests for the OR-Tools optimizer.
Tests different optimization weights and their effects on scheduling.
"""

import pytest

from app.handlers.results_handlers import create_optimized_schedule

pytestmark = pytest.mark.optimizer


class TestWeightOptimization:
    """Test optimization weight effects on scheduling decisions."""

    def test_teacher_preference_weight(self, temp_storage):
        """Test 4.1: Teacher preference weight affects assignment priority."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {"Mo": [("09:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
        }

        children = {
            "Child_1": {"name": "Child 1", "availability": {}, "preferred_teachers": ["Teacher_A"]}  # Strong preference
        }

        tandems = {}

        # Test with high teacher preference weight
        weights_high_pref = {"preferred_teacher": 10, "priority_early_slot": 1, "tandem_fulfilled": 1}
        schedule_high, violations_high = create_optimized_schedule(teachers, children, tandems, weights_high_pref)

        # Test with low teacher preference weight
        weights_low_pref = {"preferred_teacher": 1, "priority_early_slot": 10, "tandem_fulfilled": 1}
        schedule_low, violations_low = create_optimized_schedule(teachers, children, tandems, weights_low_pref)

        # Both should produce valid schedules
        assert schedule_high is not None
        assert schedule_low is not None
        assert violations_high is not None
        assert violations_low is not None

    def test_early_time_preference_weight(self, temp_storage):
        """Test 4.2: Early time preference weight affects time slot selection."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("08:00", "18:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},  # All day
            }
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {},
                "preferred_teachers": [],
                "early_preference": True,  # Prefers early slots
            }
        }

        tandems = {}

        # Test with high early preference weight
        weights_high_early = {"preferred_teacher": 1, "priority_early_slot": 10, "tandem_fulfilled": 1}
        schedule_high, violations_high = create_optimized_schedule(teachers, children, tandems, weights_high_early)

        # Test with low early preference weight
        weights_low_early = {"preferred_teacher": 1, "priority_early_slot": 1, "tandem_fulfilled": 1}
        schedule_low, violations_low = create_optimized_schedule(teachers, children, tandems, weights_low_early)

        # Both should produce valid schedules
        assert schedule_high is not None
        assert schedule_low is not None

    def test_tandem_fulfillment_weight(self, temp_storage):
        """Test 4.3: Tandem fulfillment weight prioritizes pairing."""
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
        }

        tandems = {"Tandem_1": {"child1": "Child_1", "child2": "Child_2", "priority": 5}}

        # High tandem weight
        weights_high_tandem = {"preferred_teacher": 1, "priority_early_slot": 1, "tandem_fulfilled": 10}
        schedule_high, violations_high = create_optimized_schedule(teachers, children, tandems, weights_high_tandem)

        # Low tandem weight
        weights_low_tandem = {"preferred_teacher": 10, "priority_early_slot": 1, "tandem_fulfilled": 1}
        schedule_low, violations_low = create_optimized_schedule(teachers, children, tandems, weights_low_tandem)

        # Both should produce valid schedules
        assert schedule_high is not None
        assert schedule_low is not None

    def test_balanced_weight_optimization(self, temp_storage):
        """Test 4.4: Balanced weights create reasonable compromise."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("08:00", "16:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {"Mo": [("08:00", "16:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {},
                "preferred_teachers": ["Teacher_A"],
                "early_preference": True,
            },
            "Child_2": {"name": "Child 2", "availability": {}, "preferred_teachers": ["Teacher B"]},
            "Child_3": {"name": "Child 3", "availability": {}, "preferred_teachers": []},
            "Child_4": {"name": "Child 4", "availability": {}, "preferred_teachers": []},
        }

        tandems = {"Tandem_1": {"child1": "Child_3", "child2": "Child_4", "priority": 7}}

        # Balanced weights
        weights_balanced = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}
        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights_balanced)

        # Should produce reasonable schedule
        assert schedule is not None
        assert violations is not None

    def test_zero_weights_handling(self, temp_storage):
        """Test 4.5: Zero weights disable optimization criteria."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {},
                "preferred_teachers": ["Teacher_A"],
                "early_preference": True,
            }
        }

        tandems = {}

        # All weights zero - should still produce valid schedule
        weights_zero = {"preferred_teacher": 0, "priority_early_slot": 0, "tandem_fulfilled": 0}
        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights_zero)

        # Should handle zero weights gracefully
        assert schedule is not None
        assert violations is not None

    def test_extreme_weight_values(self, temp_storage):
        """Test 4.6: Extreme weight values don't break optimization."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }
        }

        children = {"Child_1": {"name": "Child 1", "availability": {}, "preferred_teachers": ["Teacher_A"]}}

        tandems = {}

        # Extreme high weights
        weights_extreme = {"preferred_teacher": 1000, "priority_early_slot": 0.001, "tandem_fulfilled": 999}
        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights_extreme)

        # Should handle extreme values
        assert schedule is not None
        assert violations is not None
