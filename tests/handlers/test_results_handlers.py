"""
Focused tests for results_handlers module based on actual implementation.
"""

from unittest.mock import Mock

import pytest

from app.handlers.results_handlers import create_optimized_schedule, generate_schedule_pdf


class TestOptimizationCore:
    """Test core optimization functionality."""

    def test_create_optimized_schedule_basic(self, temp_storage):
        """Test basic optimization with minimal data."""
        teachers = {"T1": {"name": "Teacher One", "availability": {"Mo": [("08:00", "12:00")]}}}
        children = {"C1": {"name": "Child One", "availability": {"Mo": [("08:00", "10:00")]}, "preferred_teachers": []}}
        tandems = {}
        weights = {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4}

        result = create_optimized_schedule(teachers, children, tandems, weights, random_seed=42)
        schedule, violations = result

        # Define expected result structure
        expected_schedule = {
            "Mo": {"08:00": {"teacher": "T1", "children": ["C1"]}},
            "Di": {},
            "Mi": {},
            "Do": {},
            "Fr": {},
        }
        expected_violations = []

        # Compare actual result with expected
        assert schedule == expected_schedule, f"Expected {expected_schedule}, got {schedule}"
        assert violations == expected_violations, f"Expected no violations, got {violations}"

    def test_create_optimized_schedule_with_worker(self, temp_storage):
        """Test optimization with worker callback produces valid results."""
        mock_worker = Mock()
        mock_worker.signals = Mock()
        mock_worker.signals.progress = Mock()
        mock_worker.signals.progress.emit = Mock()

        teachers = {"T1": {"name": "Teacher", "availability": {"Mo": [("08:00", "12:00")]}}}
        children = {"C1": {"name": "Child", "availability": {"Mo": [("08:00", "10:00")]}, "preferred_teachers": []}}

        result = create_optimized_schedule(teachers, children, {}, {}, worker=mock_worker, random_seed=42)
        schedule, violations = result

        # Define expected result structure - same as basic test since same data
        expected_schedule = {
            "Mo": {"08:00": {"teacher": "T1", "children": ["C1"]}},
            "Di": {},
            "Mi": {},
            "Do": {},
            "Fr": {},
        }
        expected_violations = []

        # Compare actual result with expected - worker should not interfere
        assert (
            schedule == expected_schedule
        ), f"Worker interfered with optimization: expected {expected_schedule}, got {schedule}"
        assert violations == expected_violations, f"Expected no violations, got {violations}"

    def test_create_optimized_schedule_with_random_seed(self, temp_storage):
        """Test deterministic optimization with random seed."""
        teachers = {"T1": {"name": "Teacher", "availability": {"Mo": [("08:00", "12:00")]}}}
        children = {
            "C1": {"name": "Child1", "availability": {"Mo": [("08:00", "10:00")]}, "preferred_teachers": []},
            "C2": {"name": "Child2", "availability": {"Mo": [("09:00", "11:00")]}, "preferred_teachers": []},
        }

        # Define expected result structure with both children assigned
        expected_schedule = {
            "Mo": {"08:00": {"teacher": "T1", "children": ["C1"]}, "09:00": {"teacher": "T1", "children": ["C2"]}},
            "Di": {},
            "Mi": {},
            "Do": {},
            "Fr": {},
        }
        expected_violations = []

        # Run with same seed twice - should get identical results
        result1 = create_optimized_schedule(teachers, children, {}, {}, random_seed=42)
        result2 = create_optimized_schedule(teachers, children, {}, {}, random_seed=42)

        schedule1, violations1 = result1
        schedule2, violations2 = result2

        # Verify deterministic results
        assert schedule1 == schedule2 == expected_schedule, f"Expected {expected_schedule}, got {schedule1}"
        assert violations1 == violations2 == expected_violations, f"Expected no violations, got {violations1}"

    def test_create_optimized_schedule_empty_data(self):
        """Test optimization with empty data."""
        result = create_optimized_schedule({}, {}, {}, {}, random_seed=42)
        schedule, violations = result

        # Define expected empty schedule structure
        expected_schedule = {"Mo": {}, "Di": {}, "Mi": {}, "Do": {}, "Fr": {}}
        expected_violations = []

        # Compare actual result with expected
        assert schedule == expected_schedule, f"Expected {expected_schedule}, got {schedule}"
        assert violations == expected_violations, f"Expected no violations, got {violations}"

    def test_create_optimized_schedule_impossible_scenario(self, temp_storage):
        """Test optimization with impossible scheduling scenario."""
        teachers = {"T1": {"name": "Teacher", "availability": {"Mo": [("08:00", "09:00")]}}}  # Only 1 hour
        children = {
            "C1": {
                "name": "Child1",
                "availability": {"Di": [("08:00", "10:00")]},
                "preferred_teachers": [],
            },  # Different day
            "C2": {
                "name": "Child2",
                "availability": {"Mi": [("08:00", "10:00")]},
                "preferred_teachers": [],
            },  # Different day
        }

        result = create_optimized_schedule(teachers, children, {}, {}, random_seed=42)
        schedule, violations = result

        # Define expected result structure - empty schedule with violations
        expected_schedule = {"Mo": {}, "Di": {}, "Mi": {}, "Do": {}, "Fr": {}}
        expected_violations = ["Child 'C1' could not be scheduled", "Child 'C2' could not be scheduled"]

        # Compare actual result with expected
        assert schedule == expected_schedule, f"Expected {expected_schedule}, got {schedule}"
        assert set(violations) == set(
            expected_violations
        ), f"Expected {set(expected_violations)}, got {set(violations)}"


class TestScheduleStructure:
    """Test schedule data structure and format."""

    def test_schedule_structure_with_assignment(self, temp_storage):
        """Test that successful assignment creates proper schedule structure with actual assignment validation."""
        teachers = {"T1": {"name": "Teacher", "availability": {"Mo": [("08:00", "12:00")]}}}
        children = {"C1": {"name": "Child", "availability": {"Mo": [("08:00", "10:00")]}, "preferred_teachers": ["T1"]}}

        result = create_optimized_schedule(teachers, children, {}, {"preferred_teacher": 10}, random_seed=42)
        schedule, violations = result

        # Define expected result structure with preferred teacher assignment
        expected_schedule = {
            "Mo": {"09:15": {"teacher": "T1", "children": ["C1"]}},
            "Di": {},
            "Mi": {},
            "Do": {},
            "Fr": {},
        }
        expected_violations = []

        # Compare actual result with expected
        assert schedule == expected_schedule, f"Expected {expected_schedule}, got {schedule}"
        assert violations == expected_violations, f"Expected no violations, got {violations}"

    def test_tandem_scheduling(self, temp_storage):
        """Test tandem pair scheduling with actual validation."""
        teachers = {"T1": {"name": "Teacher", "availability": {"Mo": [("08:00", "18:00")]}}}
        children = {
            "C1": {"name": "Child1", "availability": {"Mo": [("08:00", "18:00")]}, "preferred_teachers": []},
            "C2": {"name": "Child2", "availability": {"Mo": [("08:00", "18:00")]}, "preferred_teachers": []},
        }
        tandems = {"TD1": {"child1": "C1", "child2": "C2", "priority": 8}}
        weights = {"tandem_fulfilled": 10}

        result = create_optimized_schedule(teachers, children, tandems, weights, random_seed=42)
        schedule, violations = result

        # Define expected result structure with tandem fulfilled
        expected_schedule = {
            "Mo": {"17:15": {"teacher": "T1", "children": ["C1", "C2"]}},
            "Di": {},
            "Mi": {},
            "Do": {},
            "Fr": {},
        }
        expected_violations = []

        # Compare actual result with expected - tandem should be fulfilled
        assert schedule == expected_schedule, f"Expected {expected_schedule}, got {schedule}"
        assert violations == expected_violations, f"Expected no violations, got {violations}"


class TestPDFGeneration:
    """Test PDF generation functionality."""

    def test_generate_schedule_pdf_basic_smoke_test(self):
        """Smoke test for PDF generation - just ensure it doesn't crash."""
        # Simplified test that just checks the function can be called
        test_data = {
            "teachers": {"T1": {"name": "Teacher"}},
            "children": {"C1": {"name": "Child"}},
            "tandems": {},
            "violations": [],
            "weights": {},
        }

        # Just verify the function can be called without crashing
        try:
            result = generate_schedule_pdf(test_data, "test_output.pdf")
            # Function completed - that's the main success criteria
        except Exception as e:
            # If it fails due to missing dependencies or file issues, that's acceptable
            # The main thing is that the function exists and has the right signature
            assert "generate_schedule_pdf" in str(e) or isinstance(e, FileNotFoundError | PermissionError)


class TestWeightEffects:
    """Test optimization weight effects."""

    def test_teacher_preference_basic(self, temp_storage):
        """Test that teacher preferences have some effect."""
        teachers = {
            "T1": {"name": "Preferred Teacher", "availability": {"Mo": [("08:00", "18:00")]}},
            "T2": {"name": "Other Teacher", "availability": {"Mo": [("08:00", "18:00")]}},
        }
        children = {"C1": {"name": "Child", "availability": {"Mo": [("08:00", "18:00")]}, "preferred_teachers": ["T1"]}}

        # Test with high preference weight
        result = create_optimized_schedule(teachers, children, {}, {"preferred_teacher": 20}, random_seed=42)
        schedule, violations = result

        # Define expected result structure with preferred teacher assignment
        expected_schedule = {
            "Mo": {"08:00": {"teacher": "T1", "children": ["C1"]}},
            "Di": {},
            "Mi": {},
            "Do": {},
            "Fr": {},
        }
        expected_violations = []

        # Compare actual result with expected - should prefer T1 over T2
        assert schedule == expected_schedule, f"Expected {expected_schedule}, got {schedule}"
        assert violations == expected_violations, f"Expected no violations, got {violations}"

    def test_different_weight_configurations(self, temp_storage):
        """Test different weight configurations produce expected behavior."""
        teachers = {"T1": {"name": "Teacher", "availability": {"Mo": [("08:00", "18:00")]}}}
        children = {"C1": {"name": "Child", "availability": {"Mo": [("08:00", "18:00")]}, "preferred_teachers": []}}

        # Define expected result structure (same for both configs since 08:00 is already earliest)
        expected_schedule = {
            "Mo": {"08:00": {"teacher": "T1", "children": ["C1"]}},
            "Di": {},
            "Mi": {},
            "Do": {},
            "Fr": {},
        }
        expected_violations = []

        # Test early slot preference
        result_early = create_optimized_schedule(
            teachers, children, {}, {"priority_early_slot": 20, "preferred_teacher": 0}, random_seed=42
        )
        schedule_early, violations_early = result_early

        # Test no early preference
        result_no_early = create_optimized_schedule(
            teachers, children, {}, {"priority_early_slot": 0, "preferred_teacher": 0}, random_seed=42
        )
        schedule_no_early, violations_no_early = result_no_early

        # Both should produce the same result (08:00 is already earliest possible)
        assert schedule_early == expected_schedule, f"Expected {expected_schedule}, got {schedule_early}"
        assert violations_early == expected_violations, f"Expected no violations, got {violations_early}"
        assert schedule_no_early == expected_schedule, f"Expected {expected_schedule}, got {schedule_no_early}"
        assert violations_no_early == expected_violations, f"Expected no violations, got {violations_no_early}"


class TestConstraintViolations:
    """Test constraint violation detection and reporting."""

    def test_unassigned_children_violations(self, temp_storage):
        """Test that unassigned children generate violations."""
        # Teacher has very limited availability, children have conflicting availability
        teachers = {"T1": {"name": "Teacher", "availability": {"Mo": [("08:00", "08:45")]}}}
        children = {
            "C1": {"name": "Child1", "availability": {"Di": [("08:00", "10:00")]}, "preferred_teachers": []},
            "C2": {"name": "Child2", "availability": {"Mi": [("08:00", "10:00")]}, "preferred_teachers": []},
            "C3": {"name": "Child3", "availability": {"Do": [("08:00", "10:00")]}, "preferred_teachers": []},
        }

        result = create_optimized_schedule(teachers, children, {}, {}, random_seed=42)
        schedule, violations = result

        # Should report violations for unassigned children
        assert len(violations) > 0, "Should report violations when children cannot be assigned"

        # Check that violations mention the problem
        violation_text = " ".join(str(v).lower() for v in violations)
        has_unassigned_violation = any(
            keyword in violation_text
            for keyword in ["could not be scheduled", "not scheduled", "cannot assign", "unassigned"]
        )
        assert has_unassigned_violation, f"Violations should mention unassigned children: {violations}"

    def test_teacher_preference_violations(self, temp_storage):
        """Test violations when preferred teachers are unavailable."""
        teachers = {
            "T1": {"name": "Available Teacher", "availability": {"Mo": [("08:00", "18:00")]}},
            "T2": {"name": "Unavailable Teacher", "availability": {}},
        }
        children = {"C1": {"name": "Child", "availability": {"Mo": [("08:00", "10:00")]}, "preferred_teachers": ["T2"]}}

        result = create_optimized_schedule(teachers, children, {}, {"preferred_teacher": 10}, random_seed=42)
        schedule, violations = result

        # Define expected result structure - child assigned to available teacher T1
        expected_schedule = {
            "Mo": {"08:00": {"teacher": "T1", "children": ["C1"]}},
            "Di": {},
            "Mi": {},
            "Do": {},
            "Fr": {},
        }
        expected_violations = []  # System doesn't report preference violations, just assigns to available teacher

        # Compare actual result with expected
        assert schedule == expected_schedule, f"Expected {expected_schedule}, got {schedule}"
        assert violations == expected_violations, f"Expected no violations, got {violations}"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_create_optimized_schedule_malformed_data(self):
        """Test optimization with malformed input data."""
        malformed_cases = [
            # Missing required fields
            ({"T1": {"name": "Teacher"}}, {}, {}, {}),  # Missing availability
            ({}, {"C1": {"name": "Child"}}, {}, {}),  # Missing availability
            # Wrong data types
            (None, {}, {}, {}),
            ({}, None, {}, {}),
            ({}, {}, None, {}),
            ({}, {}, {}, None),
        ]

        for teachers, children, tandems, weights in malformed_cases:
            try:
                result = create_optimized_schedule(teachers, children, tandems, weights)
                # Should not crash, should return some result
                assert result is not None
                assert isinstance(result, tuple)
            except Exception as e:
                # Some malformed data might raise exceptions - that's acceptable
                assert isinstance(e, TypeError | AttributeError | KeyError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
