"""
Pytest configuration and shared fixtures for SlotPlanner tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

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
                    "monday": ["08:00", "09:00", "10:00"],
                    "tuesday": ["08:00", "09:00"],
                    "wednesday": [],
                    "thursday": ["14:00", "15:00"],
                    "friday": ["08:00"]
                }
            },
            "Teacher_B": {
                "name": "Teacher B", 
                "availability": {
                    "monday": ["10:00", "11:00"],
                    "tuesday": ["08:00", "09:00", "10:00"],
                    "wednesday": ["14:00"],
                    "thursday": [],
                    "friday": ["08:00", "09:00"]
                }
            }
        },
        "children": {
            "Child_1": {
                "name": "Child 1",
                "availability": {
                    "monday": ["08:00", "09:00", "10:00", "11:00"],
                    "tuesday": ["08:00", "09:00", "10:00"],
                    "wednesday": ["14:00"],
                    "thursday": ["14:00", "15:00"],
                    "friday": ["08:00", "09:00"]
                },
                "preferred_teachers": ["Teacher A"]
            },
            "Child_2": {
                "name": "Child 2",
                "availability": {
                    "monday": ["10:00", "11:00"],
                    "tuesday": ["08:00", "09:00"],
                    "wednesday": [],
                    "thursday": ["14:00"],
                    "friday": ["08:00", "09:00"]
                },
                "preferred_teachers": ["Teacher B"]
            },
            "Child_3": {
                "name": "Child 3",
                "availability": {
                    "monday": ["08:00", "09:00"],
                    "tuesday": ["10:00"],
                    "wednesday": ["14:00"],
                    "thursday": ["15:00"],
                    "friday": ["08:00"]
                },
                "preferred_teachers": []
            }
        },
        "tandems": {},
        "weights": {
            "teacher_preference": 0.5,
            "early_time": 0.3,
            "tandem_fulfillment": 0.7,
            "stability": 0.4
        }
    }


@pytest.fixture
def tandem_test_data():
    """Test dataset with tandem scenarios."""
    return {
        "teachers": {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "monday": ["08:00", "09:00", "10:00", "11:00"],
                    "tuesday": ["08:00", "09:00"],
                    "wednesday": [],
                    "thursday": ["14:00", "15:00"],
                    "friday": []
                }
            },
            "Teacher_B": {
                "name": "Teacher B",
                "availability": {
                    "monday": ["10:00", "11:00", "14:00"],
                    "tuesday": ["08:00", "09:00", "10:00"],
                    "wednesday": ["14:00", "15:00"],
                    "thursday": [],
                    "friday": ["08:00", "09:00"]
                }
            }
        },
        "children": {
            "Child_A": {
                "name": "Child A",
                "availability": {
                    "monday": ["08:00", "09:00", "10:00"],
                    "tuesday": ["08:00", "09:00"],
                    "wednesday": [],
                    "thursday": ["14:00", "15:00"],
                    "friday": []
                },
                "preferred_teachers": ["Teacher A"]
            },
            "Child_B": {
                "name": "Child B", 
                "availability": {
                    "monday": ["09:00", "10:00", "11:00"],
                    "tuesday": ["08:00"],
                    "wednesday": [],
                    "thursday": ["14:00", "15:00"],
                    "friday": []
                },
                "preferred_teachers": ["Teacher A"]
            },
            "Child_C": {
                "name": "Child C",
                "availability": {
                    "monday": ["14:00"],
                    "tuesday": ["10:00"],
                    "wednesday": ["14:00", "15:00"], 
                    "thursday": [],
                    "friday": ["08:00", "09:00"]
                },
                "preferred_teachers": ["Teacher B"]
            }
        },
        "tandems": {
            "Tandem_AB": {
                "name": "Tandem AB",
                "child1": "Child A", 
                "child2": "Child B",
                "priority": 1
            }
        },
        "weights": {
            "teacher_preference": 0.6,
            "early_time": 0.4,
            "tandem_fulfillment": 0.8,
            "stability": 0.3
        }
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
                "monday": ["08:00", "09:00"] if i % 2 == 0 else ["10:00", "11:00"],
                "tuesday": ["08:00", "09:00", "10:00"] if i < 5 else ["14:00", "15:00"],
                "wednesday": ["14:00"] if i % 3 == 0 else [],
                "thursday": ["08:00", "09:00"] if i % 4 == 0 else ["15:00"],
                "friday": ["08:00", "09:00", "10:00"] if i < 3 else []
            }
        }
    
    # Create 25 children with varied preferences and availability
    for i in range(25):
        child_name = f"Child_{i:02d}"
        preferred_teachers = [f"Teacher_{j:02d}" for j in range(min(i % 3 + 1, 10)) if j < 10]
        
        children[child_name] = {
            "name": f"Child {i:02d}",
            "availability": {
                "monday": ["08:00", "09:00", "10:00", "11:00"] if i % 5 != 0 else ["14:00"],
                "tuesday": ["08:00", "09:00"] if i % 3 == 0 else ["10:00", "14:00", "15:00"],
                "wednesday": ["14:00"] if i % 7 == 0 else [],
                "thursday": ["08:00", "09:00", "15:00"] if i % 4 != 0 else [],
                "friday": ["08:00", "09:00"] if i < 10 else ["10:00"]
            },
            "preferred_teachers": preferred_teachers
        }
    
    return {
        "teachers": teachers,
        "children": children,
        "tandems": {},
        "weights": {
            "teacher_preference": 0.7,
            "early_time": 0.5,
            "tandem_fulfillment": 0.6,
            "stability": 0.4
        }
    }


@pytest.fixture
def edge_case_data():
    """Edge case test data with extreme constraints."""
    return {
        "teachers": {
            "Single_Slot_Teacher": {
                "name": "Single Slot Teacher",
                "availability": {
                    "monday": [],
                    "tuesday": [],
                    "wednesday": ["14:00"],  # Only one slot available
                    "thursday": [],
                    "friday": []
                }
            },
            "No_Availability_Teacher": {
                "name": "No Availability Teacher", 
                "availability": {
                    "monday": [],
                    "tuesday": [],
                    "wednesday": [],
                    "thursday": [],
                    "friday": []
                }
            }
        },
        "children": {
            "Conflicted_Child": {
                "name": "Conflicted Child",
                "availability": {
                    "monday": ["08:00"],  # No teacher available at this time
                    "tuesday": [],
                    "wednesday": [],
                    "thursday": [],
                    "friday": []
                },
                "preferred_teachers": ["Single Slot Teacher"]
            },
            "Impossible_Child": {
                "name": "Impossible Child",
                "availability": {
                    "monday": [],
                    "tuesday": [],
                    "wednesday": [],
                    "thursday": [],
                    "friday": []  # No availability at all
                },
                "preferred_teachers": []
            }
        },
        "tandems": {},
        "weights": {
            "teacher_preference": 1.0,
            "early_time": 0.0,
            "tandem_fulfillment": 0.0,
            "stability": 0.0
        }
    }


@pytest.fixture
def zero_weights_data():
    """Test data with all weights set to zero."""
    return {
        "teachers": {
            "Teacher_A": {
                "name": "Teacher A",
                "availability": {
                    "monday": ["08:00", "09:00"],
                    "tuesday": [],
                    "wednesday": [],
                    "thursday": [],
                    "friday": []
                }
            }
        },
        "children": {
            "Child_1": {
                "name": "Child 1", 
                "availability": {
                    "monday": ["08:00", "09:00"],
                    "tuesday": [],
                    "wednesday": [],
                    "thursday": [],
                    "friday": []
                },
                "preferred_teachers": ["Teacher A"]
            }
        },
        "tandems": {},
        "weights": {
            "teacher_preference": 0.0,
            "early_time": 0.0,
            "tandem_fulfillment": 0.0,
            "stability": 0.0
        }
    }


def create_test_storage_with_data(tmp_path, test_data, year="2024_2025"):
    """Helper function to create storage with test data."""
    storage = Storage(data_dir=str(tmp_path))
    storage.save(year, test_data)
    return storage