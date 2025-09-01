"""
Basic functionality tests for the OR-Tools optimizer.
Tests fundamental assignment capabilities without complex constraints.
"""

import pytest
from app.logic import OptimizationSolver

pytestmark = pytest.mark.optimizer


class TestBasicFunctionality:
    """Test basic assignment functionality of the optimizer."""

    def test_simple_assignment(self, temp_storage, minimal_test_data):
        """Test 1.1: Simple assignment with 2 teachers, 3 children, no special constraints."""
        # Setup storage with test data
        temp_storage.save("2024_2025", minimal_test_data)
        
        # Create solver and run optimization
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Validate basic requirements
        assert result is not None, "Solver should return a result"
        assert "assignments" in result, "Result should contain assignments"
        
        # Each child should be assigned exactly once
        assigned_children = set()
        for assignment in result["assignments"]:
            child_name = assignment["child"] 
            assert child_name not in assigned_children, f"Child {child_name} assigned multiple times"
            assigned_children.add(child_name)
        
        # All children should be assigned (no unassigned children)
        expected_children = set(minimal_test_data["children"].keys())
        assert assigned_children == expected_children, "Not all children were assigned"
        
        # No double bookings - same teacher cannot have overlapping slots
        teacher_slots = {}
        for assignment in result["assignments"]:
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
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A",
                    "availability": {
                        "monday": ["09:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                },
                "Teacher_B": {
                    "name": "Teacher B", 
                    "availability": {
                        "monday": ["09:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                },
                "Teacher_C": {
                    "name": "Teacher C",
                    "availability": {
                        "monday": ["09:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {"monday": ["09:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": []
                },
                "Child_2": {
                    "name": "Child 2",
                    "availability": {"monday": ["09:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": []
                },
                "Child_3": {
                    "name": "Child 3", 
                    "availability": {"monday": ["09:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": []
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # All children should be assigned to different teachers at the same time
        assignments = result["assignments"]
        assert len(assignments) == 3, "All 3 children should be assigned"
        
        # All assignments should be at Monday 09:00
        for assignment in assignments:
            assert assignment["day"] == "monday", "All assignments should be on Monday"
            assert assignment["time"] == "09:00", "All assignments should be at 09:00"
        
        # Each teacher should be assigned exactly one child
        assigned_teachers = [assignment["teacher"] for assignment in assignments]
        assert len(set(assigned_teachers)) == 3, "Each teacher should get exactly one assignment"
        assert set(assigned_teachers) == {"Teacher A", "Teacher B", "Teacher C"}, "All teachers should be used"

    def test_sequential_time_slots(self, temp_storage):
        """Test 1.3: Sequential time slots with single teacher, multiple children."""
        test_data = {
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A",
                    "availability": {
                        "monday": ["08:00", "09:00", "10:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {"monday": ["08:00", "09:00", "10:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": ["Teacher A"]
                },
                "Child_2": {
                    "name": "Child 2", 
                    "availability": {"monday": ["08:00", "09:00", "10:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": ["Teacher A"]
                },
                "Child_3": {
                    "name": "Child 3",
                    "availability": {"monday": ["08:00", "09:00", "10:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # All children should be assigned  
        assignments = result["assignments"]
        assert len(assignments) == 3, "All 3 children should be assigned"
        
        # All assignments should be with Teacher A on Monday
        for assignment in assignments:
            assert assignment["teacher"] == "Teacher A", "All assignments should be with Teacher A"
            assert assignment["day"] == "monday", "All assignments should be on Monday"
        
        # Assignments should be at different time slots (no overlaps)
        assigned_times = [assignment["time"] for assignment in assignments]
        assert len(set(assigned_times)) == 3, "All assignments should be at different times"
        assert set(assigned_times) == {"08:00", "09:00", "10:00"}, "Should use all available time slots"

    def test_no_assignments_possible(self, temp_storage):
        """Test edge case where no assignments are possible due to no availability overlap."""
        test_data = {
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A",
                    "availability": {
                        "monday": ["08:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {"monday": [], "tuesday": ["09:00"], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should handle impossible assignments gracefully
        assert result is not None, "Solver should return a result even when no assignments possible"
        assert "assignments" in result, "Result should contain assignments field"
        assert len(result["assignments"]) == 0, "No assignments should be possible"
        
        # Should report violations
        assert "violations" in result, "Result should contain violations"
        assert len(result["violations"]) > 0, "Should report constraint violations"

    def test_partial_assignment_insufficient_capacity(self, temp_storage):
        """Test partial assignment when there are more children than available slots."""
        test_data = {
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A",
                    "availability": {
                        "monday": ["08:00", "09:00"],  # Only 2 slots available
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {"monday": ["08:00", "09:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": ["Teacher A"]
                },
                "Child_2": {
                    "name": "Child 2",
                    "availability": {"monday": ["08:00", "09:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": ["Teacher A"]
                },
                "Child_3": {
                    "name": "Child 3",
                    "availability": {"monday": ["08:00", "09:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": ["Teacher A"]
                },
                "Child_4": {
                    "name": "Child 4", 
                    "availability": {"monday": ["08:00", "09:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should assign maximum possible children (2 out of 4)
        assignments = result["assignments"]
        assert len(assignments) == 2, "Should assign maximum possible children (2 out of 4)"
        
        # Should report violations for unassigned children
        assert "violations" in result, "Should report violations for unassigned children"
        violations = result["violations"]
        unassigned_violations = [v for v in violations if "unassigned" in v.lower()]
        assert len(unassigned_violations) >= 1, "Should report unassigned children as violations"