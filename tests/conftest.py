"""
Pytest configuration and shared fixtures for SlotPlanner tests.
"""

import pytest
from PySide6.QtWidgets import QApplication

from app.storage import Storage


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests."""
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app
    app.quit()


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage instance for testing."""
    storage = Storage(data_dir=str(tmp_path))
    return storage


@pytest.fixture
def minimal_test_data():
    """Minimal test dataset: 2 teachers, 3 children."""
    return {
        "teachers": {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "Mo": [("08:00", "11:00")],  # 3 hours: 08:00-11:00
                    "Di": [("08:00", "10:00")],  # 2 hours: 08:00-10:00
                    "Mi": [],
                    "Do": [("14:00", "16:00")],  # 2 hours: 14:00-16:00
                    "Fr": [("08:00", "09:00")],  # 1 hour: 08:00-09:00
                },
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {
                    "Mo": [("10:00", "12:00")],  # 2 hours: 10:00-12:00
                    "Di": [("08:00", "11:00")],  # 3 hours: 08:00-11:00
                    "Mi": [("14:00", "15:00")],  # 1 hour: 14:00-15:00
                    "Do": [],
                    "Fr": [("08:00", "10:00")],  # 2 hours: 08:00-10:00
                },
            },
        },
        "children": {
            "Child_1": {
                "name": "Child 1",
                "availability": {
                    "Mo": [("08:00", "12:00")],  # Available all morning
                    "Di": [("08:00", "11:00")],  # Available morning
                    "Mi": [("14:00", "15:00")],  # Available afternoon
                    "Do": [("14:00", "16:00")],  # Available afternoon
                    "Fr": [("08:00", "10:00")],  # Available morning
                },
                "preferred_teachers": ["Teacher_A"],
            },
            "Child_2": {
                "name": "Child 2",
                "availability": {
                    "Mo": [("10:00", "12:00")],  # Available late morning
                    "Di": [("08:00", "10:00")],  # Available early morning
                    "Mi": [],
                    "Do": [("14:00", "15:00")],  # Available afternoon
                    "Fr": [("08:00", "10:00")],  # Available morning
                },
                "preferred_teachers": ["Teacher_B"],
            },
            "Child_3": {
                "name": "Child 3",
                "availability": {
                    "Mo": [("08:00", "10:00")],  # Available morning
                    "Di": [("10:00", "11:00")],  # Available late morning
                    "Mi": [("14:00", "15:00")],  # Available afternoon
                    "Do": [("15:00", "16:00")],  # Available late afternoon
                    "Fr": [("08:00", "09:00")],  # Available early morning
                },
                "preferred_teachers": [],
            },
        },
        "tandems": {},
        "weights": {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4},
    }


@pytest.fixture
def tandem_test_data():
    """Test dataset with tandem scenarios."""
    return {
        "teachers": {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "Mo": [("08:00", "12:00")],  # All morning
                    "Di": [("08:00", "10:00")],  # Early morning
                    "Mi": [],
                    "Do": [("14:00", "16:00")],  # Afternoon
                    "Fr": [],
                },
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {
                    "Mo": [("10:00", "12:00"), ("14:00", "15:00")],  # Late morning + afternoon
                    "Di": [("08:00", "11:00")],  # Morning
                    "Mi": [("14:00", "16:00")],  # Afternoon
                    "Do": [],
                    "Fr": [("08:00", "10:00")],  # Morning
                },
            },
        },
        "children": {
            "Child_A": {
                "name": "Child A",
                "availability": {
                    "Mo": [("08:00", "11:00")],  # Morning
                    "Di": [("08:00", "10:00")],  # Early morning
                    "Mi": [],
                    "Do": [("14:00", "16:00")],  # Afternoon
                    "Fr": [],
                },
                "preferred_teachers": ["Teacher A"],
            },
            "Child_B": {
                "name": "Child B",
                "availability": {
                    "Mo": [("09:00", "12:00")],  # Late morning
                    "Di": [("08:00", "09:00")],  # Early morning
                    "Mi": [],
                    "Do": [("14:00", "16:00")],  # Afternoon
                    "Fr": [],
                },
                "preferred_teachers": ["Teacher A"],
            },
            "Child_C": {
                "name": "Child C",
                "availability": {
                    "Mo": [("14:00", "15:00")],  # Afternoon
                    "Di": [("10:00", "11:00")],  # Late morning
                    "Mi": [("14:00", "16:00")],  # Afternoon
                    "Do": [],
                    "Fr": [("08:00", "10:00")],  # Morning
                },
                "preferred_teachers": ["Teacher B"],
            },
        },
        "tandems": {"Tandem_AB": {"name": "Tandem AB", "child1": "Child A", "child2": "Child B", "priority": 1}},
        "weights": {"preferred_teacher": 6, "priority_early_slot": 4, "tandem_fulfilled": 8},
    }


@pytest.fixture
def complex_test_data():
    """Complex test dataset with multiple constraints."""
    teachers = {}
    children = {}

    # Create 10 teachers with varied availability
    for i in range(10):
        teacher_name = f"Teacher_{i:02d}"
        teachers[teacher_name] = {
            "name": f"Teacher {i:02d}",
            "availability": {
                "Mo": [("08:00", "10:00")] if i % 2 == 0 else [("10:00", "12:00")],
                "Di": [("08:00", "11:00")] if i < 5 else [("14:00", "16:00")],
                "Mi": [("14:00", "15:00")] if i % 3 == 0 else [],
                "Do": [("08:00", "10:00")] if i % 4 == 0 else [("15:00", "16:00")],
                "Fr": [("08:00", "11:00")] if i < 3 else [],
            },
        }

    # Create 25 children with varied preferences and availability
    for i in range(25):
        child_name = f"Child_{i:02d}"
        preferred_teachers = [f"Teacher_{j:02d}" for j in range(min(i % 3 + 1, 10)) if j < 10]

        children[child_name] = {
            "name": f"Child {i:02d}",
            "availability": {
                "Mo": [("08:00", "12:00")] if i % 5 != 0 else [("14:00", "15:00")],
                "Di": [("08:00", "10:00")] if i % 3 == 0 else [("10:00", "16:00")],
                "Mi": [("14:00", "15:00")] if i % 7 == 0 else [],
                "Do": [("08:00", "10:00"), ("15:00", "16:00")] if i % 4 != 0 else [],
                "Fr": [("08:00", "10:00")] if i < 10 else [("10:00", "11:00")],
            },
            "preferred_teachers": preferred_teachers,
        }

    return {
        "teachers": teachers,
        "children": children,
        "tandems": {},
        "weights": {"preferred_teacher": 7, "priority_early_slot": 5, "tandem_fulfilled": 6},
    }


@pytest.fixture
def edge_case_data():
    """Edge case test data with extreme constraints."""
    return {
        "teachers": {
            "Single_Slot_Teacher": {
                "name": "Single Slot Teacher",
                "availability": {
                    "Mo": [],
                    "Di": [],
                    "Mi": [("14:00", "15:00")],  # Only one 1-hour slot available
                    "Do": [],
                    "Fr": [],
                },
            },
            "No_Availability_Teacher": {
                "name": "No Availability Teacher",
                "availability": {"Mo": [], "Di": [], "Mi": [], "Do": [], "Fr": []},
            },
        },
        "children": {
            "Conflicted_Child": {
                "name": "Conflicted Child",
                "availability": {
                    "Mo": [("08:00", "09:00")],  # No teacher available at this time
                    "Di": [],
                    "Mi": [],
                    "Do": [],
                    "Fr": [],
                },
                "preferred_teachers": ["Single_Slot_Teacher"],
            },
            "Impossible_Child": {
                "name": "Impossible Child",
                "availability": {
                    "Mo": [],
                    "Di": [],
                    "Mi": [],
                    "Do": [],
                    "Fr": [],  # No availability at all
                },
                "preferred_teachers": [],
            },
        },
        "tandems": {},
        "weights": {"preferred_teacher": 10, "priority_early_slot": 0, "tandem_fulfilled": 0},
    }


@pytest.fixture
def zero_weights_data():
    """Test data with all weights set to zero."""
    return {
        "teachers": {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "Mo": [("08:00", "10:00")],  # 2 hours available
                    "Di": [],
                    "Mi": [],
                    "Do": [],
                    "Fr": [],
                },
            }
        },
        "children": {
            "Child_1": {
                "name": "Child 1",
                "availability": {
                    "Mo": [("08:00", "10:00")],  # 2 hours available
                    "Di": [],
                    "Mi": [],
                    "Do": [],
                    "Fr": [],
                },
                "preferred_teachers": ["Teacher_A"],
            }
        },
        "tandems": {},
        "weights": {"preferred_teacher": 0, "priority_early_slot": 0, "tandem_fulfilled": 0},
    }


def create_test_storage_with_data(tmp_path, test_data, year="2024_2025"):
    """Helper function to create storage with test data."""
    storage = Storage(data_dir=str(tmp_path))
    storage.save(year, test_data)
    return storage
