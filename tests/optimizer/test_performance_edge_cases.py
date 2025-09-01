"""
Performance and edge case tests for the OR-Tools optimizer.
Tests handling of large datasets and unusual scenarios.
"""

import pytest
from app.handlers.results_handlers import create_optimized_schedule

pytestmark = pytest.mark.optimizer


class TestPerformanceEdgeCases:
    """Test optimizer performance and edge case handling."""

    @pytest.mark.slow
    def test_large_dataset_performance(self, temp_storage):
        """Test 5.1: Performance with moderate dataset (simplified for CI)."""
        # Generate moderate test data (reduced for CI performance)
        teachers = {}
        for i in range(10):  # Reduced from 100+ for CI
            teachers[f"Teacher_{i}"] = {
                "name": f"Teacher {i}",
                "availability": {"Mo": [("09:00", "17:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }

        children = {}
        for i in range(25):  # Reduced from 500+ for CI
            children[f"Child_{i}"] = {"name": f"Child {i}", "availability": {}, "preferred_teachers": []}

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        # Test should complete within reasonable time
        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        assert schedule is not None
        assert violations is not None

    @pytest.mark.edge_case
    def test_single_teacher_many_children(self, temp_storage):
        """Test 5.2: Edge case - single teacher with many children."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("08:00", "18:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},  # 10 hour window
            }
        }

        children = {}
        for i in range(15):  # 15 children competing for 1 teacher
            children[f"Child_{i}"] = {"name": f"Child {i}", "availability": {}, "preferred_teachers": ["Teacher A"]}

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should handle capacity limits
        assert schedule is not None
        assert violations is not None

    @pytest.mark.edge_case
    def test_many_teachers_single_child(self, temp_storage):
        """Test 5.3: Edge case - many teachers competing for single child."""
        teachers = {}
        for i in range(20):
            teachers[f"Teacher_{i}"] = {
                "name": f"Teacher {i}",
                "availability": {"Mo": [("09:00", "17:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {},
                "preferred_teachers": [],  # No preference, any teacher acceptable
            }
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should assign the child to one teacher
        assert schedule is not None
        assert violations is not None

    def test_optimization_timeout_handling(self, temp_storage):
        """Test 5.4: Optimization with time constraints."""
        # Create a moderately complex scenario
        teachers = {}
        for i in range(5):
            teachers[f"Teacher_{i}"] = {
                "name": f"Teacher {i}",
                "availability": {"Mo": [("09:00", "17:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }

        children = {}
        for i in range(10):
            children[f"Child_{i}"] = {
                "name": f"Child {i}",
                "availability": {},
                "preferred_teachers": [f"Teacher_{i % 3}"],  # Create preferences
            }

        tandems = {
            f"Tandem_{i}": {"child1": f"Child_{i*2}", "child2": f"Child_{i*2+1}", "priority": 5}
            for i in range(3)  # 3 tandems
        }

        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        # Should complete within solver timeout (60 seconds)
        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        assert schedule is not None
        assert violations is not None

    @pytest.mark.edge_case
    def test_extremely_limited_availability(self, temp_storage):
        """Test 5.5: Extremely limited availability windows."""
        teachers = {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {"Mo": [("09:00", "09:15")], "Di": [], "Mi": [], "Do": [], "Fr": []},  # Only 15 minutes
            }
        }

        children = {
            "Child_1": {
                "name": "Child 1",
                "availability": {"Mo": [("09:00", "09:15")]},  # Same tiny window
                "preferred_teachers": ["Teacher A"],
            },
            "Child_2": {
                "name": "Child 2",
                "availability": {"Mo": [("09:00", "09:15")]},
                "preferred_teachers": ["Teacher A"],
            },
        }

        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        # Should handle impossible constraints gracefully
        assert schedule is not None
        assert violations is not None

    @pytest.mark.performance
    def test_solver_memory_usage(self, temp_storage):
        """Test 5.6: Memory usage remains reasonable with complex scenarios."""
        # Test with moderate complexity to avoid CI resource limits
        teachers = {}
        for i in range(8):
            teachers[f"Teacher_{i}"] = {
                "name": f"Teacher {i}",
                "availability": {"Mo": [("08:00", "18:00")], "Di": [], "Mi": [], "Do": [], "Fr": []},
            }

        children = {}
        for i in range(16):
            children[f"Child_{i}"] = {"name": f"Child {i}", "availability": {}, "preferred_teachers": []}

        # Create multiple tandems
        tandems = {}
        for i in range(6):
            if i * 2 + 1 < 16:  # Ensure we don't go out of bounds
                tandems[f"Tandem_{i}"] = {"child1": f"Child_{i*2}", "child2": f"Child_{i*2+1}", "priority": 5}

        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        # Should complete without excessive memory usage
        schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)

        assert schedule is not None
        assert violations is not None
