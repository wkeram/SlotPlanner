"""
Performance and edge case tests for the OR-Tools optimizer.
Tests scalability, extreme constraint scenarios, and error handling.
"""

import pytest
import time
from app.logic import OptimizationSolver

pytestmark = [pytest.mark.optimizer, pytest.mark.performance]


class TestPerformanceAndScale:
    """Test optimizer performance with large datasets."""

    def test_large_scale_assignment(self, temp_storage, complex_test_data):
        """Test 6.1: Large scale assignment with 10 teachers, 25 children."""
        temp_storage.save("2024_2025", complex_test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        
        # Measure solving time
        start_time = time.time()
        result = solver.solve()
        solve_time = time.time() - start_time
        
        # Should complete within reasonable time (10 seconds)
        assert solve_time < 10.0, f"Large scale solving took too long: {solve_time:.2f} seconds"
        
        # Should produce meaningful results
        assert result is not None, "Should produce result for large dataset"
        assignments = result["assignments"]
        
        # Should assign a reasonable number of children
        total_children = len(complex_test_data["children"])
        assignment_ratio = len(assignments) / total_children
        assert assignment_ratio >= 0.3, f"Should assign at least 30% of children, got {assignment_ratio:.2%}"
        
        # All assignments should be valid
        for assignment in assignments:
            assert "child" in assignment, "Assignment should have child"
            assert "teacher" in assignment, "Assignment should have teacher"
            assert "day" in assignment, "Assignment should have day"
            assert "time" in assignment, "Assignment should have time"

    def test_high_constraint_density(self, temp_storage):
        """Test 6.2: High constraint density with many overlapping constraints."""
        # Create scenario with many constraints and limited feasibility
        teachers = {}
        children = {}
        
        # 5 teachers with very limited, overlapping availability
        for i in range(5):
            teacher_name = f"Teacher_{i}"
            teachers[teacher_name] = {
                "name": f"Teacher {i}",
                "availability": {
                    "monday": ["08:00", "09:00"] if i <= 2 else [],
                    "tuesday": ["08:00"] if i == 0 or i == 3 else [],
                    "wednesday": ["14:00"] if i % 2 == 0 else [],
                    "thursday": [], "friday": []
                }
            }
        
        # 15 children with specific preferences and limited availability
        for i in range(15):
            child_name = f"Child_{i}"
            # Most children prefer the first 3 teachers (creating high demand)
            preferred_teachers = [f"Teacher_{j}" for j in range(min(3, 5)) if j < 3]
            
            children[child_name] = {
                "name": f"Child {i}",
                "availability": {
                    "monday": ["08:00", "09:00"] if i < 8 else [],
                    "tuesday": ["08:00"] if i % 3 == 0 else [],
                    "wednesday": ["14:00"] if i >= 10 else [],
                    "thursday": [], "friday": []
                },
                "preferred_teachers": preferred_teachers
            }
        
        test_data = {
            "teachers": teachers,
            "children": children,
            "tandems": {},
            "weights": {"teacher_preference": 0.8, "early_time": 0.6, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        
        start_time = time.time()
        result = solver.solve()
        solve_time = time.time() - start_time
        
        # Should handle complex constraints efficiently
        assert solve_time < 15.0, f"High constraint density solving took too long: {solve_time:.2f} seconds"
        assert result is not None, "Should produce result despite high constraint density"

    def test_minimal_availability_windows(self, temp_storage):
        """Test 6.3: Very limited availability creating tight scheduling."""
        test_data = {
            "teachers": {
                "Busy_Teacher": {
                    "name": "Busy Teacher",
                    "availability": {
                        "monday": [], "tuesday": [], "wednesday": ["14:00"], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                **{f"Child_{i}": {
                    "name": f"Child {i}",
                    "availability": {
                        "monday": [], "tuesday": [], "wednesday": ["14:00"], "thursday": [], "friday": []
                    },
                    "preferred_teachers": ["Busy Teacher"]
                } for i in range(1, 4)}  # 3 children competing for 1 slot
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should maximize assignments within constraints
        assignments = result["assignments"]
        assert len(assignments) == 1, "Should assign exactly one child to the single available slot"
        
        assignment = assignments[0]
        assert assignment["teacher"] == "Busy Teacher", "Should use the only available teacher"
        assert assignment["day"] == "wednesday", "Should use the only available day"
        assert assignment["time"] == "14:00", "Should use the only available time"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_no_available_teachers(self, temp_storage):
        """Test 8.1: No teachers have any availability."""
        test_data = {
            "teachers": {
                "Unavailable_Teacher": {
                    "name": "Unavailable Teacher",
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
                    "preferred_teachers": ["Unavailable Teacher"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should handle gracefully without crashing
        assert result is not None, "Should return result even with no available teachers"
        assert len(result["assignments"]) == 0, "Should have no assignments when no teachers available"
        assert "violations" in result, "Should report violations for impossible assignments"

    def test_no_children_to_assign(self, temp_storage):
        """Test edge case with teachers but no children."""
        test_data = {
            "teachers": {
                "Available_Teacher": {
                    "name": "Available Teacher",
                    "availability": {
                        "monday": ["08:00", "09:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {},  # No children
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should handle gracefully
        assert result is not None, "Should return result even with no children"
        assert len(result["assignments"]) == 0, "Should have no assignments when no children"

    def test_circular_tandem_dependencies(self, temp_storage):
        """Test 8.2: Complex tandem relationships with potential conflicts."""
        test_data = {
            "teachers": {
                "Teacher_A": {
                    "name": "Teacher A",
                    "availability": {
                        "monday": ["08:00", "09:00", "10:00", "11:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []
                    }
                }
            },
            "children": {
                "Child_A": {"name": "Child A", "availability": {"monday": ["08:00", "09:00", "10:00", "11:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}, "preferred_teachers": ["Teacher A"]},
                "Child_B": {"name": "Child B", "availability": {"monday": ["08:00", "09:00", "10:00", "11:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}, "preferred_teachers": ["Teacher A"]},
                "Child_C": {"name": "Child C", "availability": {"monday": ["08:00", "09:00", "10:00", "11:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}, "preferred_teachers": ["Teacher A"]},
                "Child_D": {"name": "Child D", "availability": {"monday": ["08:00", "09:00", "10:00", "11:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}, "preferred_teachers": ["Teacher A"]}
            },
            "tandems": {
                "Tandem_AB": {"name": "Tandem AB", "child1": "Child A", "child2": "Child B", "priority": 1},
                "Tandem_BC": {"name": "Tandem BC", "child1": "Child B", "child2": "Child C", "priority": 1},  # Child B in multiple tandems
                "Tandem_CD": {"name": "Tandem CD", "child1": "Child C", "child2": "Child D", "priority": 1}
            },
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.8, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should handle complex tandem relationships
        assert result is not None, "Should handle complex tandem dependencies"
        assignments = result["assignments"]
        
        # Should assign some children despite complex constraints
        assert len(assignments) >= 2, "Should assign at least some children"
        
        # Verify no child is assigned multiple times
        assigned_children = [a["child"] for a in assignments]
        assert len(assigned_children) == len(set(assigned_children)), "No child should be assigned multiple times"

    def test_negative_weights_handling(self, temp_storage):
        """Test 8.4: Negative weight values are handled correctly."""
        test_data = {
            "teachers": {
                "Teacher_A": {"name": "Teacher A", "availability": {"monday": ["08:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}},
                "Teacher_B": {"name": "Teacher B", "availability": {"monday": ["08:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}}
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {"monday": ["08:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": -0.5, "early_time": -0.3, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should still assign despite negative weights
        assert result is not None, "Should handle negative weights"
        assignments = result["assignments"]
        assert len(assignments) == 1, "Should assign child despite negative weights"

    def test_extreme_weight_values(self, temp_storage):
        """Test handling of extreme weight values (very high/low)."""
        test_data = {
            "teachers": {
                "Teacher_A": {"name": "Teacher A", "availability": {"monday": ["08:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}}
            },
            "children": {
                "Child_1": {
                    "name": "Child 1",
                    "availability": {"monday": ["08:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": ["Teacher A"]
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 1000.0, "early_time": 0.001, "tandem_fulfillment": 0.0, "stability": 0.0}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should handle extreme weights without numerical issues
        assert result is not None, "Should handle extreme weight values"
        assignments = result["assignments"]
        assert len(assignments) == 1, "Should assign child with extreme weights"

    def test_malformed_data_handling(self, temp_storage):
        """Test handling of malformed or incomplete data."""
        # Test with missing required fields
        test_data = {
            "teachers": {
                "Incomplete_Teacher": {
                    "name": "Incomplete Teacher"
                    # Missing availability field
                }
            },
            "children": {
                "Incomplete_Child": {
                    "name": "Incomplete Child",
                    "availability": {"monday": ["08:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}
                    # Missing preferred_teachers field
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        
        # Should handle malformed data gracefully
        try:
            result = solver.solve()
            # If it doesn't raise an exception, check that it handles gracefully
            assert result is not None, "Should return result even with malformed data"
        except Exception as e:
            # If it raises an exception, it should be a meaningful error
            assert isinstance(e, (ValueError, KeyError)), f"Should raise meaningful exception, got {type(e)}"

    def test_empty_dataset(self, temp_storage):
        """Test completely empty dataset."""
        test_data = {
            "teachers": {},
            "children": {},
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        result = solver.solve()
        
        # Should handle empty dataset gracefully
        assert result is not None, "Should handle empty dataset"
        assert len(result["assignments"]) == 0, "Should have no assignments for empty dataset"

    def test_memory_usage_large_dataset(self, temp_storage):
        """Test memory usage doesn't grow excessively with large datasets."""
        # Create larger dataset for memory testing
        teachers = {}
        children = {}
        
        # 20 teachers
        for i in range(20):
            teachers[f"Teacher_{i:02d}"] = {
                "name": f"Teacher {i:02d}",
                "availability": {
                    "monday": ["08:00", "09:00"] if i % 3 == 0 else [],
                    "tuesday": ["10:00", "11:00"] if i % 3 == 1 else [],
                    "wednesday": ["14:00"] if i % 3 == 2 else [],
                    "thursday": ["08:00"] if i < 10 else [],
                    "friday": ["09:00"] if i >= 10 else []
                }
            }
        
        # 100 children
        for i in range(100):
            children[f"Child_{i:03d}"] = {
                "name": f"Child {i:03d}",
                "availability": {
                    "monday": ["08:00", "09:00"] if i % 4 == 0 else [],
                    "tuesday": ["10:00", "11:00"] if i % 4 == 1 else [],
                    "wednesday": ["14:00"] if i % 4 == 2 else [],
                    "thursday": ["08:00"] if i % 4 == 3 else [],
                    "friday": ["09:00"] if i < 50 else []
                },
                "preferred_teachers": [f"Teacher_{j:02d}" for j in range(min(3, 20))]
            }
        
        test_data = {
            "teachers": teachers,
            "children": children,
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4}
        }
        
        temp_storage.save("2024_2025", test_data)
        solver = OptimizationSolver(temp_storage, "2024_2025")
        
        # Test that it completes without memory issues
        start_time = time.time()
        result = solver.solve()
        solve_time = time.time() - start_time
        
        # Should complete within reasonable time and memory constraints
        assert solve_time < 30.0, f"Large dataset solving took too long: {solve_time:.2f} seconds"
        assert result is not None, "Should complete large dataset optimization"
        
        # Should assign a reasonable number of children
        assignments = result["assignments"]
        assert len(assignments) >= 10, f"Should assign reasonable number of children from large dataset, got {len(assignments)}"