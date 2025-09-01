"""
Constraint violation tests for the OR-Tools optimizer.
Tests that hard constraints are properly enforced and violations are reported.
"""

import pytest
from app.logic import OptimizationSolver

pytestmark = pytest.mark.optimizer


class TestConstraintViolations:
    """Test constraint enforcement and violation handling."""

    def test_teacher_unavailability_hard_constraint(self, temp_storage):
        """Test 2.1: Teacher unavailability as hard constraint overrides child preferences."""
        test_data = {
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A", 
                    "availability": {
                        "monday": [],
                        "tuesday": ["10:00"],  # Only available Tuesday 10:00-11:00
                        "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {
                        "monday": ["08:00", "09:00"],  # Child prefers different time
                        "tuesday": ["10:00"],  # But also available when teacher is available
                        "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 1.0, "early_time": 0.8, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Child should be assigned to teacher's available time despite preference for earlier
        assignments = result["assignments"]
        assert len(assignments) == 1, "Child should be assigned"
        
        assignment = assignments[0]
        assert assignment["teacher"] == "Teacher A", "Should be assigned to preferred teacher"
        assert assignment["day"] == "tuesday", "Should be assigned on teacher's available day"
        assert assignment["time"] == "10:00", "Should be assigned at teacher's available time"

    def test_child_availability_conflict(self, temp_storage):
        """Test 2.2: Child availability conflict prevents assignment."""
        test_data = {
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A",
                    "availability": {
                        "monday": ["08:00", "09:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {
                        "monday": [],  # Child not available when teacher is
                        "tuesday": [],
                        "wednesday": ["14:00"],  # Child available when teacher is not
                        "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025") 
        result = solver.solve()
        
        # No assignment should be possible
        assert len(result["assignments"]) == 0, "No assignment should be possible due to availability conflict"
        
        # Should report constraint violation
        assert "violations" in result, "Should report constraint violations"
        violations = result["violations"]
        assert len(violations) > 0, "Should report availability conflict as violation"

    def test_insufficient_teacher_capacity(self, temp_storage):
        """Test 2.3: More children than available teacher slots."""
        test_data = {
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A",
                    "availability": {
                        "monday": ["08:00", "09:00"],  # Only 2 slots
                        "tuesday": ["10:00"],  # Plus 1 more = 3 total slots 
                        "wednesday": [], "thursday": [], "friday": []
                    }
                },
                "Teacher_B": {
                    "name": "Teacher B",
                    "availability": {
                        "monday": [],
                        "tuesday": [],
                        "wednesday": [],
                        "thursday": [],
                        "friday": []  # No availability
                    }
                }
            },
            "children": {
                **{f"Child_{i}": {
                    "name": f"Child {i}",
                    "availability": {
                        "monday": ["08:00", "09:00"],
                        "tuesday": ["10:00"],
                        "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                } for i in range(1, 6)}  # 5 children need slots
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should assign maximum possible children (3 out of 5)
        assignments = result["assignments"]
        assert len(assignments) == 3, f"Should assign 3 children, got {len(assignments)}"
        
        # All assignments should be with Teacher A (only teacher with availability)
        for assignment in assignments:
            assert assignment["teacher"] == "Teacher A", "All assignments should be with available teacher"
        
        # Should report violations for unassigned children
        assert "violations" in result, "Should report violations"
        violations = result["violations"]
        # Should have violations for the 2 unassigned children
        unassigned_count = sum(1 for v in violations if "unassigned" in v.lower() or "not assigned" in v.lower())
        assert unassigned_count >= 1, "Should report unassigned children violations"

    def test_teacher_preference_vs_availability_constraint(self, temp_storage):
        """Test that teacher availability constraints override teacher preferences."""
        test_data = {
            "teachers": {
                "Preferred_Teacher": {
                    "name": "Preferred Teacher", 
                    "availability": {
                        "monday": [],  # Preferred teacher not available
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                },
                "Available_Teacher": {
                    "name": "Available Teacher",
                    "availability": {
                        "monday": ["08:00"],  # Only this teacher available
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {
                        "monday": ["08:00"],  # Child available when Available_Teacher is
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Preferred Teacher"]  # Prefers unavailable teacher
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 1.0, "early_time": 0.0, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Child should be assigned to available teacher, not preferred unavailable one
        assignments = result["assignments"]
        assert len(assignments) == 1, "Child should be assigned"
        
        assignment = assignments[0]
        assert assignment["teacher"] == "Available Teacher", "Should be assigned to available teacher despite preference"
        assert assignment["day"] == "monday", "Should be assigned on available day"
        assert assignment["time"] == "08:00", "Should be assigned at available time"

    def test_multiple_constraint_violations(self, temp_storage):
        """Test handling of multiple simultaneous constraint violations."""
        test_data = {
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A",
                    "availability": {
                        "monday": ["08:00"],  # Very limited availability
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1", 
                    "availability": {
                        "monday": ["08:00"],  # Can be assigned
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                },
                "Child_2": {
                    "name": "Child 2",
                    "availability": {
                        "monday": [],  # Cannot be assigned - no availability overlap
                        "tuesday": ["09:00"], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                },
                "Child_3": {
                    "name": "Child 3",
                    "availability": {
                        "monday": ["08:00"],  # Conflicts with Child_1 for same slot
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Only one child can be assigned
        assignments = result["assignments"]
        assert len(assignments) == 1, "Only one child should be assignable"
        
        # Should report multiple violations
        assert "violations" in result, "Should report constraint violations"
        violations = result["violations"]
        assert len(violations) >= 2, "Should report violations for multiple unassigned children"

    def test_empty_availability_handling(self, temp_storage):
        """Test handling of completely empty availability schedules."""
        test_data = {
            "teachers": {
                "Empty_Teacher": {
                    "name": "Empty Teacher",
                    "availability": {
                        "monday": [], "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {
                        "monday": ["08:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Empty Teacher"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # No assignments possible
        assert len(result["assignments"]) == 0, "No assignments should be possible"
        
        # Should handle gracefully without crashes
        assert result is not None, "Solver should handle empty availability gracefully"
        assert "violations" in result, "Should report violations"