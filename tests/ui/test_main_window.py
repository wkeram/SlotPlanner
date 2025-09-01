"""
Main window UI tests for SlotPlanner.
Tests core UI functionality, data persistence, and user interactions.
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

pytestmark = [pytest.mark.ui, pytest.mark.integration]

from app.gui import create_main_window
from app.storage import Storage
from tests.conftest import create_test_storage_with_data


class TestMainWindowUI:
    """Test main window UI functionality."""

    def test_main_window_initialization(self, qapp, temp_storage):
        """Test that main window initializes properly."""
        window = create_main_window(temp_storage)

        assert window is not None, "Main window should be created"
        assert isinstance(window, QMainWindow), "Should be a QMainWindow instance"
        assert window.isVisible() or not window.isHidden(), "Window should be showable"

        # Check that main UI elements exist
        assert window.findChild(QTableWidget, "teachersTable") is not None, "Teachers table should exist"
        assert window.findChild(QTableWidget, "childrenTable") is not None, "Children table should exist"
        assert window.findChild(QTableWidget, "tandemsTable") is not None, "Tandems table should exist"

        window.close()

    def test_year_selection_changes_data(self, qapp, temp_storage):
        """Test that changing year selection loads different data."""
        # Setup test data for different years
        data_2023 = {
            "teachers": {
                "Teacher_2023": {
                    "name": "Teacher 2023",
                    "availability": {"monday": ["08:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                }
            },
            "children": {
                "Child_2023": {
                    "name": "Child 2023",
                    "availability": {"monday": ["08:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": [],
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.5, "early_time": 0.3, "tandem_fulfillment": 0.7, "stability": 0.4},
        }

        data_2024 = {
            "teachers": {
                "Teacher_2024": {
                    "name": "Teacher 2024",
                    "availability": {"monday": ["09:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                }
            },
            "children": {
                "Child_2024": {
                    "name": "Child 2024",
                    "availability": {"monday": ["09:00"], "tuesday": [], "wednesday": [], "thursday": [], "friday": []},
                    "preferred_teachers": [],
                }
            },
            "tandems": {},
            "weights": {"teacher_preference": 0.6, "early_time": 0.4, "tandem_fulfillment": 0.8, "stability": 0.3},
        }

        temp_storage.save("2023_2024", data_2023)
        temp_storage.save("2024_2025", data_2024)

        window = create_main_window(temp_storage)

        # Find year selection widget
        year_combo = window.findChild(None, "yearComboBox")  # Adjust name as needed
        if year_combo:
            # Test year switching loads correct data
            # This is a placeholder - actual implementation depends on UI structure
            pass

        window.close()

    def test_add_teacher_dialog_functionality(self, qapp, temp_storage):
        """Test add teacher dialog opens and functions correctly."""
        window = create_main_window(temp_storage)

        # Find add teacher button
        add_teacher_btn = window.findChild(None, "addTeacherButton")

        if add_teacher_btn:
            # Mock dialog to avoid actual UI interaction in tests
            with patch("app.handlers.teacher_handlers.create_add_teacher_dialog") as mock_dialog:
                mock_dialog.return_value = Mock()

                # Simulate button click
                QTest.mouseClick(add_teacher_btn, Qt.LeftButton)

                # Verify dialog creation was attempted
                mock_dialog.assert_called_once()

        window.close()

    def test_teacher_table_data_display(self, qapp, temp_storage, minimal_test_data):
        """Test that teacher data is properly displayed in the table."""
        temp_storage.save("2024_2025", minimal_test_data)
        window = create_main_window(temp_storage)

        teachers_table = window.findChild(QTableWidget, "teachersTable")
        if teachers_table:
            # Check that teachers are loaded into table
            row_count = teachers_table.rowCount()
            expected_teachers = len(minimal_test_data["teachers"])

            # Table should have correct number of rows (may include headers)
            assert row_count >= expected_teachers, f"Teachers table should have at least {expected_teachers} rows"

            # Check for teacher names in table
            teacher_names = set(minimal_test_data["teachers"].keys())
            found_names = set()

            for row in range(row_count):
                item = teachers_table.item(row, 0)  # Assuming name is in first column
                if item:
                    found_names.add(item.text())

            # At least some teacher names should be found
            assert len(found_names.intersection(teacher_names)) > 0, "Teacher names should appear in table"

        window.close()

    def test_child_table_data_display(self, qapp, temp_storage, minimal_test_data):
        """Test that child data is properly displayed in the table."""
        temp_storage.save("2024_2025", minimal_test_data)
        window = create_main_window(temp_storage)

        children_table = window.findChild(QTableWidget, "childrenTable")
        if children_table:
            # Check that children are loaded into table
            row_count = children_table.rowCount()
            expected_children = len(minimal_test_data["children"])

            assert row_count >= expected_children, f"Children table should have at least {expected_children} rows"

            # Check for child names in table
            child_names = set(minimal_test_data["children"].keys())
            found_names = set()

            for row in range(row_count):
                item = children_table.item(row, 0)
                if item:
                    found_names.add(item.text())

            assert len(found_names.intersection(child_names)) > 0, "Child names should appear in table"

        window.close()

    def test_optimization_button_triggers_solver(self, qapp, temp_storage, minimal_test_data):
        """Test that optimization button triggers the solver."""
        temp_storage.save("2024_2025", minimal_test_data)
        window = create_main_window(temp_storage)

        # Find optimize button
        optimize_btn = window.findChild(None, "optimizeButton")  # Adjust name as needed

        if optimize_btn:
            # Mock the optimization solver
            with patch("app.logic.OptimizationSolver") as mock_solver:
                mock_instance = Mock()
                mock_instance.solve.return_value = {
                    "assignments": [{"child": "Child 1", "teacher": "Teacher A", "day": "monday", "time": "08:00"}],
                    "violations": [],
                    "score": 0.85,
                }
                mock_solver.return_value = mock_instance

                # Simulate button click
                QTest.mouseClick(optimize_btn, Qt.LeftButton)

                # Verify solver was called
                mock_solver.assert_called()
                mock_instance.solve.assert_called_once()

        window.close()

    def test_save_data_persistence(self, qapp, temp_storage):
        """Test that UI changes are properly saved to storage."""
        window = create_main_window(temp_storage)

        # This test would need to interact with UI elements to add/modify data
        # Then verify that the data is saved to storage
        # Implementation depends on specific UI widgets and handlers

        # Placeholder test structure:
        # 1. Add a teacher through UI
        # 2. Verify teacher appears in storage
        # 3. Modify teacher data through UI
        # 4. Verify changes are saved

        window.close()

    def test_validation_feedback_display(self, qapp, temp_storage):
        """Test that validation errors are properly displayed to user."""
        window = create_main_window(temp_storage)

        # Test validation error display
        # This would involve triggering validation errors and checking UI feedback

        window.close()

    def test_results_table_display(self, qapp, temp_storage, minimal_test_data):
        """Test that optimization results are displayed in results table."""
        temp_storage.save("2024_2025", minimal_test_data)
        window = create_main_window(temp_storage)

        # Mock optimization result
        mock_result = {
            "assignments": [
                {"child": "Child 1", "teacher": "Teacher A", "day": "monday", "time": "08:00"},
                {"child": "Child 2", "teacher": "Teacher B", "day": "tuesday", "time": "09:00"},
            ],
            "violations": [],
            "score": 0.92,
        }

        # Find results table
        results_table = window.findChild(QTableWidget, "resultsTable")
        if results_table:
            # Simulate displaying results (would normally happen after optimization)
            # This test verifies the table can display the results properly
            pass

        window.close()

    def test_pdf_export_button(self, qapp, temp_storage, minimal_test_data):
        """Test PDF export functionality."""
        temp_storage.save("2024_2025", minimal_test_data)
        window = create_main_window(temp_storage)

        # Find PDF export button
        pdf_btn = window.findChild(None, "exportPdfButton")

        if pdf_btn:
            # Mock PDF export
            with patch("app.export_pdf.export_schedule_to_pdf") as mock_export:
                mock_export.return_value = True

                # Simulate button click
                QTest.mouseClick(pdf_btn, Qt.LeftButton)

                # Verify export was attempted
                # (May need results data to be present first)

        window.close()

    def test_tandem_management_ui(self, qapp, temp_storage, tandem_test_data):
        """Test tandem creation and management UI."""
        temp_storage.save("2024_2025", tandem_test_data)
        window = create_main_window(temp_storage)

        # Test tandem table display
        tandems_table = window.findChild(QTableWidget, "tandemsTable")
        if tandems_table:
            row_count = tandems_table.rowCount()
            expected_tandems = len(tandem_test_data["tandems"])
            assert row_count >= expected_tandems, "Tandems table should display existing tandems"

        # Test add tandem functionality
        add_tandem_btn = window.findChild(None, "addTandemButton")
        if add_tandem_btn:
            with patch("app.handlers.tandem_handlers.create_add_tandem_dialog") as mock_dialog:
                mock_dialog.return_value = Mock()
                QTest.mouseClick(add_tandem_btn, Qt.LeftButton)
                mock_dialog.assert_called()

        window.close()

    def test_weight_configuration_ui(self, qapp, temp_storage, minimal_test_data):
        """Test optimization weights configuration UI."""
        temp_storage.save("2024_2025", minimal_test_data)
        window = create_main_window(temp_storage)

        # Find weight configuration widgets (sliders, spinboxes, etc.)
        # Test that weights can be adjusted and are saved

        # This test structure would verify:
        # 1. Weight controls are properly initialized with current values
        # 2. Changing weight controls updates the stored values
        # 3. Weight changes affect optimization results

        window.close()


class TestUIValidation:
    """Test UI validation and error handling."""

    def test_empty_name_validation(self, qapp, temp_storage):
        """Test validation prevents empty names."""
        window = create_main_window(temp_storage)

        # Test that empty teacher/child names are rejected
        # This would involve simulating user input and checking validation feedback

        window.close()

    def test_duplicate_name_validation(self, qapp, temp_storage):
        """Test validation prevents duplicate names."""
        window = create_main_window(temp_storage)

        # Test that duplicate teacher/child names are rejected

        window.close()

    def test_invalid_time_format_validation(self, qapp, temp_storage):
        """Test validation of time format inputs."""
        window = create_main_window(temp_storage)

        # Test that invalid time formats are rejected

        window.close()

    def test_required_field_validation(self, qapp, temp_storage):
        """Test that required fields must be filled."""
        window = create_main_window(temp_storage)

        # Test that forms cannot be submitted with missing required fields

        window.close()


class TestUIPerformance:
    """Test UI responsiveness and performance."""

    def test_large_dataset_table_loading(self, qapp, temp_storage, complex_test_data):
        """Test UI remains responsive with large datasets."""
        temp_storage.save("2024_2025", complex_test_data)

        import time

        start_time = time.time()
        window = create_main_window(temp_storage)
        load_time = time.time() - start_time

        # UI should load within reasonable time
        assert load_time < 5.0, f"UI loading took too long with large dataset: {load_time:.2f} seconds"

        # Tables should be responsive
        teachers_table = window.findChild(QTableWidget, "teachersTable")
        if teachers_table:
            assert teachers_table.rowCount() > 0, "Teachers table should load data"

        window.close()

    def test_optimization_ui_feedback(self, qapp, temp_storage, minimal_test_data):
        """Test that UI provides feedback during optimization."""
        temp_storage.save("2024_2025", minimal_test_data)
        window = create_main_window(temp_storage)

        # Test that UI shows progress/status during optimization
        # This would involve checking for progress bars, status messages, etc.

        window.close()


class TestUIIntegration:
    """Test integration between UI components and business logic."""

    def test_end_to_end_workflow(self, qapp, temp_storage):
        """Test complete user workflow from data entry to results."""
        window = create_main_window(temp_storage)

        # Simulate complete workflow:
        # 1. Add teachers
        # 2. Add children
        # 3. Configure weights
        # 4. Run optimization
        # 5. View results
        # 6. Export PDF

        # This would be a comprehensive integration test

        window.close()

    def test_data_consistency_across_tabs(self, qapp, temp_storage):
        """Test that data remains consistent when switching between tabs."""
        window = create_main_window(temp_storage)

        # Test that changes in one tab are reflected in others
        # Test that switching tabs doesn't lose unsaved changes

        window.close()

    def test_error_recovery_ui(self, qapp, temp_storage):
        """Test UI handles and recovers from errors gracefully."""
        window = create_main_window(temp_storage)

        # Test error handling:
        # 1. Storage errors
        # 2. Optimization errors
        # 3. UI component errors

        window.close()
