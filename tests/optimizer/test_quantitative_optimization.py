"""
Quantitative optimization tests for the OR-Tools optimizer.
Tests that verify optimization scores and weight effects with numerical assertions.
"""

import pytest

from app.handlers.results_handlers import create_optimized_schedule
from tests.test_helpers import (
    assert_schedule_quality,
    calculate_early_slot_score,
    calculate_preference_score,
    calculate_tandem_score,
    calculate_total_optimization_score,
    get_scheduled_children,
    run_deterministic_optimization,
)

pytestmark = pytest.mark.optimizer


class TestQuantitativeOptimization:
    """Test numerical optimization behavior and score calculations."""

    def test_preference_weight_effect_quantified(self, temp_storage):
        """Test 1: Higher preference weights produce measurably better preference scores."""
        teachers = {
            "Preferred_Teacher": {
                "name": "Preferred Teacher",
                "availability": {"Mo": [("09:00", "11:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Other_Teacher": {
                "name": "Other Teacher",
                "availability": {"Mo": [("10:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {"Mo": [("09:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
                "preferred_teachers": ["Preferred_Teacher"],
            }
        }

        tandems = {}

        # Test with low preference weight
        low_weights = {"preferred_teacher": 1, "priority_early_slot": 0, "tandem_fulfilled": 0}
        schedule_low, violations_low = run_deterministic_optimization(teachers, children, tandems, low_weights, seed=42)
        score_low = calculate_preference_score(schedule_low, children, low_weights)

        # Test with high preference weight
        high_weights = {"preferred_teacher": 100, "priority_early_slot": 0, "tandem_fulfilled": 0}
        schedule_high, violations_high = run_deterministic_optimization(
            teachers, children, tandems, high_weights, seed=42
        )
        score_high = calculate_preference_score(schedule_high, children, high_weights)

        # Both should be valid schedules
        assert_schedule_quality(schedule_low, violations_low, teachers, children, tandems)
        assert_schedule_quality(schedule_high, violations_high, teachers, children, tandems)

        # High preference weight should result in preferred teacher being chosen
        scheduled_children = get_scheduled_children(schedule_high)
        assert "Child_1" in scheduled_children, "Child should be scheduled with high preference weight"

        # Find which teacher was chosen with high preference weight
        chosen_teacher_high = None
        for day_schedule in schedule_high.values():
            for assignment in day_schedule.values():
                if "Child_1" in assignment.get("children", []):
                    chosen_teacher_high = assignment.get("teacher")
                    break

        assert (
            chosen_teacher_high == "Preferred_Teacher"
        ), "High preference weight should result in preferred teacher being chosen"

        # Score with high weight should be higher when preferred teacher is chosen
        assert score_high >= score_low, "Higher preference weight should not decrease preference score"

    def test_early_slot_weight_effect_quantified(self, temp_storage):
        """Test 2: Early slot preferences are quantifiably respected."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "Mo": [("08:00", "10:00"), ("14:00", "16:00")],  # Morning and afternoon slots
                    "Di": [],
                    "Mi": [],
                    "Do": [],
                    "Fr": [],
                },
            }
        }

        children = {
            "Early_Child": {
                "name": "Early Child",
                "availability": {"Mo": [("08:00", "16:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
                "preferred_teachers": [],
                "early_preference": True,
            }
        }

        tandems = {}

        # Test with no early slot preference
        no_early_weights = {"preferred_teacher": 0, "priority_early_slot": 0, "tandem_fulfilled": 0}
        schedule_no_early, violations_no_early = run_deterministic_optimization(
            teachers, children, tandems, no_early_weights, seed=42
        )

        # Test with high early slot preference
        high_early_weights = {"preferred_teacher": 0, "priority_early_slot": 50, "tandem_fulfilled": 0}
        schedule_early, violations_early = run_deterministic_optimization(
            teachers, children, tandems, high_early_weights, seed=42
        )

        # Both should be valid
        assert_schedule_quality(schedule_no_early, violations_no_early, teachers, children, tandems)
        assert_schedule_quality(schedule_early, violations_early, teachers, children, tandems)

        # Calculate early slot scores
        early_score_no_preference = calculate_early_slot_score(schedule_no_early, children, high_early_weights)
        early_score_with_preference = calculate_early_slot_score(schedule_early, children, high_early_weights)

        # High early preference should achieve better or equal early slot score
        assert early_score_with_preference >= early_score_no_preference, (
            f"High early weight should achieve better early score: "
            f"{early_score_with_preference} vs {early_score_no_preference}"
        )

        # Find assignment time for high early preference
        assigned_time = None
        for day_schedule in schedule_early.values():
            for time_slot, assignment in day_schedule.items():
                if "Early_Child" in assignment.get("children", []):
                    assigned_time = time_slot
                    break

        # With high early preference, should get morning slot
        assert assigned_time is not None, "Child should be assigned"
        assert assigned_time < "12:00", f"High early preference should result in morning slot, got {assigned_time}"

    def test_tandem_weight_effect_quantified(self, temp_storage):
        """Test 3: Tandem weights measurably affect tandem scheduling success."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {"Mo": [("10:00", "13:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
        }

        children = {
            "Tandem_Child_1": {
                "name": "Tandem Child 1",
                "availability": {"Mo": [("09:00", "13:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
                "preferred_teachers": [],
            },
            "Tandem_Child_2": {
                "name": "Tandem Child 2",
                "availability": {"Mo": [("09:00", "13:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
                "preferred_teachers": [],
            },
        }

        tandems = {
            "Test_Tandem": {
                "name": "Test Tandem",
                "child1": "Tandem_Child_1",
                "child2": "Tandem_Child_2",
                "priority": 5,
            }
        }

        # Test with no tandem preference
        no_tandem_weights = {"preferred_teacher": 0, "priority_early_slot": 0, "tandem_fulfilled": 0}
        schedule_no_tandem, violations_no_tandem = run_deterministic_optimization(
            teachers, children, tandems, no_tandem_weights, seed=42
        )

        # Test with high tandem preference
        high_tandem_weights = {"preferred_teacher": 0, "priority_early_slot": 0, "tandem_fulfilled": 100}
        schedule_tandem, violations_tandem = run_deterministic_optimization(
            teachers, children, tandems, high_tandem_weights, seed=42
        )

        # Both should be valid
        assert_schedule_quality(schedule_no_tandem, violations_no_tandem, teachers, children, tandems)
        assert_schedule_quality(schedule_tandem, violations_tandem, teachers, children, tandems)

        # Calculate tandem scores
        tandem_score_no_preference = calculate_tandem_score(schedule_no_tandem, tandems, high_tandem_weights)
        tandem_score_with_preference = calculate_tandem_score(schedule_tandem, tandems, high_tandem_weights)

        # High tandem weight should achieve better or equal tandem score
        assert tandem_score_with_preference >= tandem_score_no_preference, (
            f"High tandem weight should achieve better tandem score: "
            f"{tandem_score_with_preference} vs {tandem_score_no_preference}"
        )

        # Check if tandem is scheduled together with high weight
        tandem_together = False
        for day_schedule in schedule_tandem.values():
            for assignment in day_schedule.values():
                assigned_children = assignment.get("children", [])
                if "Tandem_Child_1" in assigned_children and "Tandem_Child_2" in assigned_children:
                    tandem_together = True
                    break

        # With high tandem weight, tandem should be scheduled together
        assert tandem_together, "High tandem weight should schedule tandem children together"

    def test_total_score_maximization(self, temp_storage, minimal_test_data):
        """Test 4: Optimizer maximizes total weighted score."""
        teachers = minimal_test_data["teachers"]
        children = minimal_test_data["children"]
        tandems = minimal_test_data["tandems"]
        weights = minimal_test_data["weights"]

        # Run optimization
        schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)
        assert_schedule_quality(schedule, violations, teachers, children, tandems)

        # Calculate total score
        total_score = calculate_total_optimization_score(schedule, children, tandems, weights)

        # Score should be non-negative
        assert total_score >= 0, f"Total optimization score should be non-negative, got {total_score}"

        # Each component score should be non-negative
        pref_score = calculate_preference_score(schedule, children, weights)
        early_score = calculate_early_slot_score(schedule, children, weights)
        tandem_score = calculate_tandem_score(schedule, tandems, weights)

        assert pref_score >= 0, f"Preference score should be non-negative, got {pref_score}"
        assert early_score >= 0, f"Early slot score should be non-negative, got {early_score}"
        assert tandem_score >= 0, f"Tandem score should be non-negative, got {tandem_score}"

        # Total should equal sum of components
        assert total_score == pref_score + early_score + tandem_score, (
            f"Total score {total_score} should equal sum of components: "
            f"{pref_score} + {early_score} + {tandem_score} = {pref_score + early_score + tandem_score}"
        )

    def test_zero_weights_still_produce_valid_schedule(self, temp_storage, zero_weights_data):
        """Test 5: Zero weights still produce valid schedules."""
        teachers = zero_weights_data["teachers"]
        children = zero_weights_data["children"]
        tandems = zero_weights_data["tandems"]
        weights = zero_weights_data["weights"]

        # All weights are zero
        assert all(w == 0 for w in weights.values()), "Test data should have all zero weights"

        # Run optimization
        schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)
        assert_schedule_quality(schedule, violations, teachers, children, tandems)

        # Should still schedule children even with zero weights
        scheduled = get_scheduled_children(schedule)
        assert len(scheduled) > 0, "Should schedule at least some children even with zero weights"

        # Total score should be zero with zero weights
        total_score = calculate_total_optimization_score(schedule, children, tandems, weights)
        assert total_score == 0, f"Total score with zero weights should be 0, got {total_score}"

    def test_weight_scaling_effect(self, temp_storage):
        """Test 6: Scaling all weights by same factor doesn't change optimization outcome."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "11:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {"Mo": [("09:00", "11:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
                "preferred_teachers": ["Teacher_A"],
            }
        }

        tandems = {}

        # Test with base weights
        base_weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}
        schedule_base, violations_base = run_deterministic_optimization(
            teachers, children, tandems, base_weights, seed=42
        )

        # Test with scaled weights (all multiplied by 10)
        scaled_weights = {"preferred_teacher": 50, "priority_early_slot": 30, "tandem_fulfilled": 40}
        schedule_scaled, violations_scaled = run_deterministic_optimization(
            teachers, children, tandems, scaled_weights, seed=42
        )

        # Both should be valid
        assert_schedule_quality(schedule_base, violations_base, teachers, children, tandems)
        assert_schedule_quality(schedule_scaled, violations_scaled, teachers, children, tandems)

        # Schedules should be identical (optimization outcome unchanged)
        assert (
            schedule_base == schedule_scaled
        ), "Scaling all weights by same factor should not change optimization outcome"

        # Violation counts should be identical
        assert len(violations_base) == len(violations_scaled), "Scaling weights should not change violation count"

    def test_relative_weight_importance(self, temp_storage):
        """Test 7: Relative weight ratios determine optimization priority."""
        teachers = {
            "Preferred_Teacher": {
                "name": "Preferred Teacher",
                "availability": {"Mo": [("14:00", "16:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},  # Afternoon
            },
            "Other_Teacher": {
                "name": "Other Teacher",
                "availability": {"Mo": [("08:00", "10:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},  # Morning
            },
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {
                    "Mo": [("08:00", "16:00")],
                    "Di": [],
                    "Mi": [],
                    "Do": [],
                    "Fr": [],
                },  # Available all day
                "preferred_teachers": ["Preferred_Teacher"],
                "early_preference": True,
            }
        }

        tandems = {}

        # Test: Teacher preference dominates early preference
        teacher_dominant_weights = {"preferred_teacher": 100, "priority_early_slot": 1, "tandem_fulfilled": 0}
        schedule_teacher_dom, violations_teacher_dom = run_deterministic_optimization(
            teachers, children, tandems, teacher_dominant_weights, seed=42
        )

        # Test: Early preference dominates teacher preference
        early_dominant_weights = {"preferred_teacher": 1, "priority_early_slot": 100, "tandem_fulfilled": 0}
        schedule_early_dom, violations_early_dom = run_deterministic_optimization(
            teachers, children, tandems, early_dominant_weights, seed=42
        )

        # Both should be valid
        assert_schedule_quality(schedule_teacher_dom, violations_teacher_dom, teachers, children, tandems)
        assert_schedule_quality(schedule_early_dom, violations_early_dom, teachers, children, tandems)

        # Find assignments
        teacher_dom_assignment = None
        early_dom_assignment = None

        for day_schedule in schedule_teacher_dom.values():
            for time_slot, assignment in day_schedule.items():
                if "Child_1" in assignment.get("children", []):
                    teacher_dom_assignment = (assignment.get("teacher"), time_slot)
                    break

        for day_schedule in schedule_early_dom.values():
            for time_slot, assignment in day_schedule.items():
                if "Child_1" in assignment.get("children", []):
                    early_dom_assignment = (assignment.get("teacher"), time_slot)
                    break

        assert teacher_dom_assignment is not None, "Child should be assigned when teacher preference dominates"
        assert early_dom_assignment is not None, "Child should be assigned when early preference dominates"

        # When teacher preference dominates, should choose preferred teacher (afternoon slot)
        teacher_dom_teacher, teacher_dom_time = teacher_dom_assignment
        assert (
            teacher_dom_teacher == "Preferred_Teacher"
        ), "When teacher preference dominates, should choose preferred teacher"

        # When early preference dominates, should choose morning slot
        early_dom_teacher, early_dom_time = early_dom_assignment
        assert (
            early_dom_time < "12:00"
        ), f"When early preference dominates, should choose morning slot, got {early_dom_time}"
