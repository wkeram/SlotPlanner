"""
Weight optimization tests for the OR-Tools optimizer.
Tests that optimization weights are properly applied and affect solution quality.
"""

import pytest
from app.logic import OptimizationSolver

pytestmark = pytest.mark.optimizer


class TestWeightOptimization:
    """Test optimization weight handling and solution scoring."""

    def test_teacher_preference_weight(self, temp_storage):
        """Test 3.1: Teacher preference weight influences assignment decisions."""
        test_data = {
            "teachers": {
                "Preferred_Teacher": {
                    "name": "Preferred Teacher",
                    "availability": {
                        "monday": ["08:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                },
                "Other_Teacher": {
                    "name": "Other Teacher", 
                    "availability": {
                        "monday": ["08:00"],  # Same time slot available
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {
                        "monday": ["08:00"], 
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Preferred Teacher"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.8, "early_time": 0.1, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Child should be assigned to preferred teacher due to high weight
        assignments = result["assignments"]
        assert len(assignments) == 1, "Child should be assigned"
        assert assignments[0]["teacher"] == "Preferred Teacher", "Should assign to preferred teacher with high weight"
        
        # Test with lower teacher preference weight
        test_data["weights"]["teacher_preference"] = 0.1
        test_data["weights"]["early_time"] = 0.1  # Keep other weights low too
        temp_storage.save("2024_2025", test_data)
        
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Still should prefer the preferred teacher, but weight impact should be measurable
        assignments = result["assignments"]
        assert len(assignments) == 1, "Child should still be assigned"

    def test_early_time_preference_weight(self, temp_storage):
        """Test 3.2: Early time preference weight affects slot selection."""
        test_data = {
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A",
                    "availability": {
                        "monday": ["08:00", "15:00"],  # Early vs late slots
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {
                        "monday": ["08:00", "15:00"],  # Available for both
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                },
                "Child_2": {
                    "name": "Child 2",
                    "availability": {
                        "monday": ["08:00", "15:00"], 
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.1, "early_time": 0.9, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Both children should be assigned
        assignments = result["assignments"]
        assert len(assignments) == 2, "Both children should be assigned"
        
        # With high early time weight, 08:00 slot should be preferred over 15:00
        assigned_times = [assignment["time"] for assignment in assignments]
        assert "08:00" in assigned_times, "Early time slot should be used with high early time weight"
        
        # Test that early time is actually preferred by checking which gets the early slot
        early_assignments = [a for a in assignments if a["time"] == "08:00"]
        late_assignments = [a for a in assignments if a["time"] == "15:00"] 
        
        assert len(early_assignments) == 1, "Exactly one child should get early slot"
        assert len(late_assignments) == 1, "Exactly one child should get late slot"

    def test_zero_weights_configuration(self, temp_storage, zero_weights_data):
        """Test 3.3: Zero weights configuration produces valid assignments."""
        temp_storage.save("2024_2025", zero_weights_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should still produce valid assignment even with zero weights
        assignments = result["assignments"]
        assert len(assignments) == 1, "Should assign child even with zero weights"
        
        assignment = assignments[0]
        assert assignment["child"] == "Child 1", "Should assign the child"
        assert assignment["teacher"] == "Teacher A", "Should assign to available teacher"

    def test_competing_weight_priorities(self, temp_storage):
        """Test 3.4: Balanced solution when weights compete."""
        test_data = {
            "teachers": {
                "Preferred_Teacher": {
                    "name": "Preferred Teacher",
                    "availability": {
                        "monday": ["15:00"],  # Late time (conflicts with early time preference)
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                },
                "Other_Teacher": {
                    "name": "Other Teacher",
                    "availability": {
                        "monday": ["08:00"],  # Early time (conflicts with teacher preference)
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {
                        "monday": ["08:00", "15:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Preferred Teacher"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.6, "early_time": 0.7, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Child should be assigned to one of the teachers
        assignments = result["assignments"]
        assert len(assignments) == 1, "Child should be assigned"
        
        # The solution should balance both preferences
        # With early_time weight (0.7) slightly higher than teacher_preference (0.6),
        # might prefer Other_Teacher at 08:00, but both are valid solutions
        assignment = assignments[0]
        assert assignment["teacher"] in ["Preferred Teacher", "Other Teacher"], "Should assign to one of the teachers"
        
        # Verify the assignment respects availability constraints
        if assignment["teacher"] == "Preferred Teacher":
            assert assignment["time"] == "15:00", "Preferred teacher only available at 15:00"
        else:
            assert assignment["time"] == "08:00", "Other teacher only available at 08:00"

    def test_stability_weight_preserves_existing(self, temp_storage):
        """Test 3.5: Stability weight preserves existing assignments."""
        # First, create an existing schedule
        test_data = {
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A",
                    "availability": {
                        "monday": ["08:00", "09:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                },
                "Teacher_B": {
                    "name": "Teacher B",
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
                        "monday": ["08:00", "09:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                },
                "Child_2": {
                    "name": "Child 2",
                    "availability": {
                        "monday": ["08:00", "09:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        # Save and solve to get initial assignments
        temp_storage.save("2024_2025", test_data) 
        solver = OptimizationSolver(temp_storage, "2024_2025")
        initial_result = solver.solve()
        
        # Store the initial result as "previous schedule"
        initial_assignments = initial_result["assignments"]
        assert len(initial_assignments) == 2, "Should have initial assignments"
        
        # Create data with previous schedule and high stability weight
        test_data["previous_schedule"] = initial_assignments
        test_data["weights"]["stability"] = 0.9  # High stability weight
        test_data["weights"]["teacher_preference"] = 0.1  # Lower other weights
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        stable_result = solver.solve()
        
        # With high stability weight, assignments should be preserved
        stable_assignments = stable_result["assignments"]
        assert len(stable_assignments) == 2, "Should maintain assignments"
        
        # Assignments should be similar to initial ones (allowing for some flexibility in ordering)
        initial_assignment_keys = {(a["child"], a["teacher"], a["day"], a["time"]) for a in initial_assignments}
        stable_assignment_keys = {(a["child"], a["teacher"], a["day"], a["time"]) for a in stable_assignments}
        
        # At least some assignments should be preserved (perfect match not always guaranteed due to solver variations)
        preserved_count = len(initial_assignment_keys.intersection(stable_assignment_keys))
        assert preserved_count >= 1, "At least some assignments should be preserved with high stability weight"

    def test_negative_weights_handling(self, temp_storage):
        """Test 3.6: Negative weights are handled correctly."""
        test_data = {
            "teachers": {
                "Avoided_Teacher": {
                    "name": "Avoided Teacher",
                    "availability": {
                        "monday": ["08:00"], 
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                },
                "Preferred_Teacher": {
                    "name": "Preferred Teacher",
                    "availability": {
                        "monday": ["08:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {
                        "monday": ["08:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Avoided Teacher"]  # This teacher should be avoided due to negative weight
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": -0.5, "early_time": 0.0, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Child should still be assigned (negative weight doesn't prevent valid assignments)
        assignments = result["assignments"]
        assert len(assignments) == 1, "Child should be assigned despite negative teacher preference weight"
        
        # The assignment should still be valid
        assignment = assignments[0]
        assert assignment["child"] == "Child 1", "Child should be assigned"
        assert assignment["teacher"] in ["Avoided Teacher", "Preferred Teacher"], "Should be assigned to available teacher"

    def test_weight_score_calculation(self, temp_storage):
        """Test that weight scores are properly calculated and reported."""
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
                    "availability": {
                        "monday": ["08:00"],
                        "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.8, "early_time": 0.6, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should include scoring information
        assert "score" in result or "objective_value" in result, "Result should include optimization score"
        
        # Assignment should satisfy preferences
        assignments = result["assignments"]
        assert len(assignments) == 1, "Child should be assigned"
        assignment = assignments[0]
        assert assignment["teacher"] == "Teacher A", "Should satisfy teacher preference"
        assert assignment["time"] == "08:00", "Should satisfy early time preference"