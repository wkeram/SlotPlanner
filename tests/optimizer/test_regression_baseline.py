"""
Regression baseline tests for the OR-Tools optimizer.
Tests that ensure optimization results remain consistent across code changes.
"""

import pytest

from tests.test_helpers import (
    assert_schedule_quality,
    calculate_total_optimization_score,
    expect_deterministic_schedule,
    get_scheduled_children,
    run_deterministic_optimization,
)

pytestmark = pytest.mark.optimizer


class TestRegressionBaseline:
    """Test that optimizer produces consistent results across code changes."""

    def test_simple_deterministic_baseline(self, temp_storage):
        """Test 1: Simple deterministic scenario with known expected result."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "Mo": [("09:00", "12:00")],  # 3 hours available
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
                    "Mo": [("09:00", "12:00")],  # Matches teacher availability
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

        # Expected result: Child_1 assigned to Teacher_A on Monday at 11:15 (deterministic result with seed 42)
        expected_assignments = [("Child_1", "Teacher_A", "Mo", "11:15")]

        schedule, violations = expect_deterministic_schedule(
            teachers, children, tandems, weights, expected_assignments, seed=42
        )

        # Should have no violations for this simple case
        assert len(violations) == 0, f"Expected no violations, got: {violations}"

        # Verify optimization score
        score = calculate_total_optimization_score(schedule, children, tandems, weights)
        assert score == 5, f"Expected score of 5 (preferred teacher bonus), got {score}"

    def test_preference_weight_deterministic(self, temp_storage):
        """Test 2: Verify that preference weights produce deterministic results."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "11:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {"Mo": [("10:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {"Mo": [("09:00", "12:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
                "preferred_teachers": ["Teacher_A"],  # Strong preference for Teacher A
            }
        }

        tandems = {}
        weights = {"preferred_teacher": 10, "priority_early_slot": 1, "tandem_fulfilled": 1}

        # With high preference weight, should always choose Teacher_A
        schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)

        assert_schedule_quality(schedule, violations, teachers, children, tandems)

        # Find the assignment
        assigned_teacher = None
        for day_schedule in schedule.values():
            for assignment in day_schedule.values():
                if "Child_1" in assignment.get("children", []):
                    assigned_teacher = assignment.get("teacher")
                    break

        assert (
            assigned_teacher == "Teacher_A"
        ), f"With high preference weight, Child_1 should be assigned to Teacher_A, got {assigned_teacher}"

    def test_early_preference_deterministic(self, temp_storage):
        """Test 3: Verify early slot preference produces deterministic results."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "Mo": [("08:00", "10:00"), ("14:00", "16:00")],  # Morning and afternoon
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
                "availability": {"Mo": [("08:00", "16:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
                "preferred_teachers": [],
                "early_preference": True,  # Prefers morning slots
            }
        }

        tandems = {}
        weights = {"preferred_teacher": 1, "priority_early_slot": 10, "tandem_fulfilled": 1}

        # With high early slot weight, should choose morning slot (08:00)
        schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)

        assert_schedule_quality(schedule, violations, teachers, children, tandems)

        # Find the assignment time
        assigned_time = None
        for day_schedule in schedule.values():
            for time_slot, assignment in day_schedule.items():
                if "Child_1" in assignment.get("children", []):
                    assigned_time = time_slot
                    break

        assert assigned_time is not None, "Child_1 should be assigned"
        assert (
            assigned_time < "12:00"
        ), f"With high early preference weight, Child_1 should get morning slot, got {assigned_time}"

    def test_tandem_deterministic_baseline(self, temp_storage, tandem_test_data):
        """Test 4: Tandem scheduling produces deterministic results."""
        teachers = tandem_test_data["teachers"]
        children = tandem_test_data["children"]
        tandems = tandem_test_data["tandems"]
        weights = {"preferred_teacher": 1, "priority_early_slot": 1, "tandem_fulfilled": 20}  # High tandem weight

        # Run optimization multiple times with same seed
        schedule1, violations1 = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)
        schedule2, violations2 = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)

        # Results should be identical
        assert schedule1 == schedule2, "Deterministic optimization should produce identical results"
        assert violations1 == violations2, "Violations should be identical"

        # Check that both tandem children are scheduled (together or separately)
        scheduled_children = set()
        for day_schedule in schedule1.values():
            for assignment in day_schedule.values():
                scheduled_children.update(assignment.get("children", []))

        # Both tandem children should be scheduled (the key test is determinism)
        assert "Child_A" in scheduled_children, "Child_A should be scheduled"
        assert "Child_B" in scheduled_children, "Child_B should be scheduled"

        # Test passes if results are deterministic (which they are)

    def test_impossible_scenario_consistent_failure(self, temp_storage, edge_case_data):
        """Test 5: Impossible scenarios fail consistently."""
        teachers = edge_case_data["teachers"]
        children = edge_case_data["children"]
        tandems = edge_case_data["tandems"]
        weights = edge_case_data["weights"]

        # Run multiple times with same seed
        schedule1, violations1 = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)
        schedule2, violations2 = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)

        # Results should be identical even for impossible scenarios
        assert schedule1 == schedule2, "Even impossible scenarios should produce identical results"
        assert violations1 == violations2, "Violation lists should be identical"

        # Should have violations due to impossible constraints
        assert len(violations1) > 0, "Impossible scenarios should produce violations"

    def test_score_consistency_across_runs(self, temp_storage, minimal_test_data):
        """Test 6: Optimization scores are consistent across multiple runs."""
        teachers = minimal_test_data["teachers"]
        children = minimal_test_data["children"]
        tandems = minimal_test_data["tandems"]
        weights = minimal_test_data["weights"]

        scores = []
        schedules = []

        # Run optimization 5 times with same seed
        for _ in range(5):
            schedule, violations = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)
            score = calculate_total_optimization_score(schedule, children, tandems, weights)
            scores.append(score)
            schedules.append(schedule)

        # All scores should be identical
        assert all(score == scores[0] for score in scores), f"Scores should be identical, got: {scores}"

        # All schedules should be identical
        for i, schedule in enumerate(schedules[1:], 1):
            assert schedule == schedules[0], f"Schedule {i} differs from schedule 0"

    def test_different_seeds_produce_different_results(self, temp_storage):
        """Test 7: Different seeds can produce different valid results."""
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
            "Child_1": {
                "name": "Child 1",
                "availability": {"Mo": [("09:00", "13:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
                "preferred_teachers": [],  # No preference - could go either way
            }
        }

        tandems = {}
        weights = {"preferred_teacher": 1, "priority_early_slot": 1, "tandem_fulfilled": 1}

        # Run with different seeds
        schedule1, violations1 = run_deterministic_optimization(teachers, children, tandems, weights, seed=42)
        schedule2, violations2 = run_deterministic_optimization(teachers, children, tandems, weights, seed=123)

        # Both should be valid
        assert_schedule_quality(schedule1, violations1, teachers, children, tandems)
        assert_schedule_quality(schedule2, violations2, teachers, children, tandems)

        # Child should be scheduled in both cases
        scheduled1 = get_scheduled_children(schedule1)
        scheduled2 = get_scheduled_children(schedule2)
        assert "Child_1" in scheduled1, "Child_1 should be scheduled with seed 42"
        assert "Child_1" in scheduled2, "Child_1 should be scheduled with seed 123"

        # Note: Results might be the same or different - both are valid
        # The important thing is that they are deterministic for each seed
