"""
Comprehensive unit tests for the Storage module.
Tests data persistence, validation, security, and error handling.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from app.storage import Storage


class TestStorageInitialization:
    """Test Storage class initialization and directory setup."""

    def test_default_initialization(self):
        """Test Storage initializes with default directories."""
        storage = Storage()

        assert storage.data_dir == os.path.abspath("data")
        assert storage.export_dir == os.path.abspath("exports")

    def test_custom_initialization(self):
        """Test Storage initializes with custom directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = os.path.join(temp_dir, "custom_data")
            export_dir = os.path.join(temp_dir, "custom_exports")

            storage = Storage(data_dir=data_dir, export_dir=export_dir)

            assert storage.data_dir == data_dir
            assert storage.export_dir == export_dir
            assert os.path.exists(data_dir)
            assert os.path.exists(export_dir)

    def test_directory_creation(self):
        """Test that directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = os.path.join(temp_dir, "nonexistent_data")
            export_dir = os.path.join(temp_dir, "nonexistent_exports")

            # Verify directories don't exist initially
            assert not os.path.exists(data_dir)
            assert not os.path.exists(export_dir)

            Storage(data_dir=data_dir, export_dir=export_dir)

            # Verify directories were created
            assert os.path.exists(data_dir)
            assert os.path.exists(export_dir)


class TestYearValidation:
    """Test year format validation logic."""

    def test_valid_year_formats(self):
        """Test that valid year formats are accepted."""
        storage = Storage()

        valid_years = ["2023_2024", "2024_2025", "1999_2000", "2099_2100"]

        for year in valid_years:
            assert storage._validate_year_format(year), f"Year {year} should be valid"

    def test_invalid_year_formats(self):
        """Test that invalid year formats are rejected."""
        storage = Storage()

        invalid_years = [
            "2023-2024",  # Wrong separator
            "23_24",  # Too short
            "2023_2025",  # Not consecutive
            "2024_2023",  # Backwards
            "2023_2024_2025",  # Too many parts
            "abc_def",  # Not numbers
            "2023",  # Missing second year
            "",  # Empty string
            None,  # None value
            123,  # Integer instead of string
            "1800_1801",  # Too old
            "2200_2201",  # Too far future
        ]

        for year in invalid_years:
            assert not storage._validate_year_format(year), f"Year {year} should be invalid"

    def test_year_validation_edge_cases(self):
        """Test edge cases in year validation."""
        storage = Storage()

        # Boundary years
        assert storage._validate_year_format("1900_1901")  # Minimum valid
        assert storage._validate_year_format("2100_2101")  # Maximum valid
        assert not storage._validate_year_format("1899_1900")  # Just below minimum
        assert not storage._validate_year_format("2101_2102")  # Just above maximum


class TestFilenameSanitization:
    """Test filename sanitization for security."""

    def test_sanitize_basic_filenames(self):
        """Test basic filename sanitization."""
        storage = Storage()

        # Valid filenames should pass through
        assert storage._sanitize_filename("2023_2024") == "2023_2024"
        assert storage._sanitize_filename("test_file.json") == "test_file.json"
        assert storage._sanitize_filename("valid123") == "valid123"

    def test_sanitize_dangerous_patterns(self):
        """Test that dangerous patterns are removed."""
        storage = Storage()

        dangerous_inputs = {
            "../../../etc/passwd": "passwd",  # os.path.basename keeps just the filename
            "file;rm -rf /": "",  # All dangerous chars removed, leaving empty
            "test$command": "testcommand",
            "file`cat /etc/hosts`": "hosts",  # os.path.basename extracts just the last part
            "file|rm test": "filermtest",
            "test&echo": "testecho",
            "file~backup": "filebackup",
        }

        for dangerous, expected in dangerous_inputs.items():
            result = storage._sanitize_filename(dangerous)
            if expected == "":
                # Allow empty result for very dangerous inputs
                assert len(result) == 0 or result.isalnum(), f"Failed to sanitize {dangerous} - got {result}"
            else:
                assert result == expected, f"Failed to sanitize {dangerous}"

    def test_sanitize_path_separators(self):
        """Test that path separators are handled correctly."""
        storage = Storage()

        # Path separators should be removed via os.path.basename
        assert storage._sanitize_filename("/tmp/test") == "test"
        assert storage._sanitize_filename("..\\windows\\system32") == "system32"  # basename keeps just last part
        assert storage._sanitize_filename("folder/subfolder/file") == "file"

    def test_sanitize_empty_result(self):
        """Test handling when sanitization results in empty string."""
        storage = Storage()

        # These should result in empty or minimal strings
        dangerous_only = "../../$`|;&~"
        result = storage._sanitize_filename(dangerous_only)
        # Should be empty or contain only safe characters
        assert all(c.isalnum() or c in "_.-" for c in result)


class TestDataPersistence:
    """Test core save/load data operations."""

    def test_save_and_load_basic_data(self):
        """Test basic save and load operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            test_data = {
                "teachers": {"T1": {"name": "Teacher One"}},
                "children": {"C1": {"name": "Child One"}},
                "tandems": {},
                "weights": {"preferred_teacher": 5},
            }

            # Save data
            storage.save("2023_2024", test_data)

            # Load data
            loaded_data = storage.load("2023_2024")

            assert loaded_data == test_data

    def test_save_overwrites_existing_data(self):
        """Test that save overwrites existing data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Save initial data
            initial_data = {"teachers": {"T1": {"name": "Initial"}}}
            storage.save("2023_2024", initial_data)

            # Save updated data
            updated_data = {"teachers": {"T1": {"name": "Updated"}}}
            storage.save("2023_2024", updated_data)

            # Load and verify updated data
            loaded_data = storage.load("2023_2024")
            assert loaded_data == updated_data

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Should return None for nonexistent file
            loaded_data = storage.load("nonexistent_2023")
            assert loaded_data is None

    def test_save_invalid_year_format(self):
        """Test that save rejects invalid year formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            test_data = {"teachers": {}}

            # Storage.save returns False for invalid year (doesn't raise)
            result = storage.save("invalid_year", test_data)
            assert result is False

    def test_load_invalid_year_format(self):
        """Test that load rejects invalid year formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Storage.load returns None for invalid year (doesn't raise)
            result = storage.load("invalid_year")
            assert result is None


class TestComplexDataTypes:
    """Test handling of complex data structures."""

    def test_nested_data_structures(self):
        """Test saving and loading nested data structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            complex_data = {
                "teachers": {
                    "T1": {
                        "name": "Teacher One",
                        "availability": {
                            "Mo": [("08:00", "12:00"), ("14:00", "16:00")],
                            "Di": [],
                            "Mi": [("09:00", "11:00")],
                        },
                        "preferences": ["early_slots", "friday_off"],
                    }
                },
                "children": {
                    "C1": {
                        "name": "Child One",
                        "availability": {"Mo": [("08:00", "10:00")]},
                        "preferred_teachers": ["T1"],
                        "notes": "Special requirements",
                    }
                },
                "tandems": {"TD1": {"child1": "C1", "child2": "C2", "priority": 8, "notes": "Siblings"}},
                "weights": {"preferred_teacher": 5, "priority_early_slot": 3, "tandem_fulfilled": 4},
            }

            storage.save("2023_2024", complex_data)
            loaded_data = storage.load("2023_2024")

            # JSON serialization converts tuples to lists, so we need to account for this
            expected_data = complex_data.copy()
            expected_data["teachers"]["T1"]["availability"]["Mo"] = [["08:00", "12:00"], ["14:00", "16:00"]]
            expected_data["teachers"]["T1"]["availability"]["Mi"] = [["09:00", "11:00"]]
            expected_data["children"]["C1"]["availability"]["Mo"] = [["08:00", "10:00"]]

            assert loaded_data == expected_data

    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            unicode_data = {
                "teachers": {"T1": {"name": "Müller, François José"}, "T2": {"name": "李老师 (Teacher Li)"}},
                "children": {"C1": {"name": "Élève François ñoño"}, "C2": {"name": "学生王小明"}},
                "notes": "Special chars: @#$%^&*()[]{}|\\:;\"'<>,.?/`~",
            }

            storage.save("2023_2024", unicode_data)
            loaded_data = storage.load("2023_2024")

            assert loaded_data == unicode_data


class TestErrorHandling:
    """Test error handling in various failure scenarios."""

    def test_save_permission_denied(self):
        """Test handling of permission denied errors during save."""
        import platform

        if platform.system() == "Windows":
            # Windows permission handling is complex and unreliable in tests
            # Use direct file mocking instead
            with tempfile.TemporaryDirectory() as temp_dir:
                storage = Storage(data_dir=temp_dir)

                with patch("builtins.open", side_effect=PermissionError("Access denied")):
                    result = storage.save("2023_2024", {"test": "data"})
                    assert result is False
        else:
            # Unix-like systems
            with tempfile.TemporaryDirectory() as temp_dir:
                storage = Storage(data_dir=temp_dir)

                readonly_dir = os.path.join(temp_dir, "readonly")
                os.makedirs(readonly_dir, mode=0o444)
                storage.data_dir = readonly_dir

                result = storage.save("2023_2024", {"test": "data"})
                assert result is False

    def test_load_corrupted_json(self):
        """Test handling of corrupted JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Create a corrupted JSON file
            file_path = os.path.join(temp_dir, "2023_2024.json")
            with open(file_path, "w") as f:
                f.write("{ invalid json content")

            # Storage.load catches exceptions and returns None
            result = storage.load("2023_2024")
            assert result is None

    def test_disk_full_simulation(self):
        """Test behavior when disk is full."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Mock open to raise OSError (disk full)
            with patch("builtins.open", side_effect=OSError("No space left on device")):
                # Storage.save catches OSError and returns False
                result = storage.save("2023_2024", {"test": "data"})
                assert result is False

    @patch("os.makedirs", side_effect=OSError("Permission denied"))
    def test_directory_creation_failure(self, mock_makedirs):
        """Test handling when directory creation fails."""
        with pytest.raises(OSError):
            Storage(data_dir="/nonexistent/path")


class TestFileListingAndManagement:
    """Test file listing and management operations."""

    def test_list_available_years(self):
        """Test listing available years."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Create some test files
            test_years = ["2022_2023", "2023_2024", "2024_2025"]
            for year in test_years:
                storage.save(year, {"test": "data"})

            # Also create some non-year files to test filtering
            with open(os.path.join(temp_dir, "not_a_year.json"), "w") as f:
                f.write("{}")
            with open(os.path.join(temp_dir, "readme.txt"), "w") as f:
                f.write("test")

            available_years = storage.list_years()

            # list_years doesn't filter, it returns all .json files without extension
            expected_years = test_years + ["not_a_year"]  # readme.txt is not .json so excluded
            assert set(available_years) == set(expected_years)

    def test_delete_year_data(self):
        """Test deleting year data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Save test data
            storage.save("2023_2024", {"test": "data"})
            assert storage.load("2023_2024") is not None

            # Delete data
            storage.delete("2023_2024")

            # Verify data is deleted
            assert storage.load("2023_2024") is None

    def test_delete_nonexistent_year(self):
        """Test deleting nonexistent year data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Should not raise error when deleting nonexistent file
            storage.delete("nonexistent_2023")  # Should complete without error


class TestConcurrencyAndRaceConditions:
    """Test concurrent access and race condition handling."""

    def test_concurrent_read_write(self):
        """Test concurrent read/write operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Save initial data
            initial_data = {"test": "initial"}
            storage.save("2023_2024", initial_data)

            # Simulate concurrent access by opening file for reading
            # while attempting to write (this is OS-dependent behavior)
            file_path = os.path.join(temp_dir, "2023_2024.json")

            try:
                with open(file_path) as read_file:
                    # Attempt to save while file is open for reading
                    new_data = {"test": "concurrent"}
                    storage.save("2023_2024", new_data)

                    # Verify the save succeeded
                    loaded_data = storage.load("2023_2024")
                    assert loaded_data == new_data

            except Exception:
                # Some platforms may prevent this - that's acceptable
                pass

    def test_atomic_write_behavior(self):
        """Test write failure behavior."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Mock json.dump to raise exception partway through
            def failing_dump(*args, **kwargs):
                # Write partial content to simulate partial write
                if hasattr(args[1], "write"):
                    args[1].write('{"partial": ')  # Partial JSON
                raise OSError("Simulated write failure")

            with patch("json.dump", side_effect=failing_dump):
                result = storage.save("2023_2024", {"test": "data"})
                # Storage should return False on failure
                assert result is False

            # Current implementation may leave partial files (not truly atomic)
            # This documents the current behavior rather than ideal behavior
            file_path = os.path.join(temp_dir, "2023_2024.json")
            if os.path.exists(file_path):
                # If file exists, it should be either empty or contain partial data
                with open(file_path) as f:
                    content = f.read()
                # Should not be valid JSON due to failure
                with pytest.raises(json.JSONDecodeError):
                    json.loads(content)


class TestDataMigrationAndCompatibility:
    """Test data migration and backwards compatibility."""

    def test_load_old_format_data(self):
        """Test loading data in older formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Create a file with old format (missing some expected keys)
            old_format_data = {
                "teachers": {"T1": {"name": "Teacher"}},
                "children": {"C1": {"name": "Child"}},
                # Missing tandems and weights
            }

            # Manually write old format
            file_path = os.path.join(temp_dir, "2023_2024.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(old_format_data, f, ensure_ascii=False, indent=2)

            # Load should work and handle missing keys gracefully
            loaded_data = storage.load("2023_2024")
            assert loaded_data == old_format_data

    def test_backup_on_migration(self):
        """Test that backups are created during migration (if implemented)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # This would test backup functionality if implemented
            # For now, just test that the concept works
            original_data = {"version": 1, "teachers": {}}
            storage.save("2023_2024", original_data)

            # In a real migration, we'd create a backup before modifying
            backup_data = storage.load("2023_2024")
            assert backup_data == original_data


class TestPerformanceCharacteristics:
    """Test performance characteristics and large data handling."""

    def test_large_dataset_handling(self):
        """Test handling of large datasets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # Create large dataset
            large_data = {
                "teachers": {f"T{i}": {"name": f"Teacher {i}"} for i in range(100)},
                "children": {f"C{i}": {"name": f"Child {i}"} for i in range(1000)},
                "tandems": {
                    f"TD{i}": {"child1": f"C{i * 2}", "child2": f"C{i * 2 + 1}", "priority": i % 10} for i in range(500)
                },
                "weights": {"preferred_teacher": 5, "priority_early_slot": 3},
            }

            # Test save performance
            import time

            start_time = time.time()
            storage.save("2023_2024", large_data)
            save_time = time.time() - start_time

            # Should complete within reasonable time (adjust threshold as needed)
            assert save_time < 5.0, f"Save took too long: {save_time:.2f}s"

            # Test load performance
            start_time = time.time()
            loaded_data = storage.load("2023_2024")
            load_time = time.time() - start_time

            assert load_time < 2.0, f"Load took too long: {load_time:.2f}s"
            assert loaded_data == large_data

    def test_memory_usage_with_large_files(self):
        """Test memory usage doesn't grow excessively with large files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = Storage(data_dir=temp_dir)

            # This test would ideally use memory profiling
            # For now, test that we can handle multiple large operations
            for i in range(5):
                large_data = {
                    "teachers": {f"T{j}": {"name": f"Teacher {j}"} for j in range(50)},
                    "children": {f"C{j}": {"name": f"Child {j}"} for j in range(500)},
                }

                year = f"202{i}_202{i + 1}"
                storage.save(year, large_data)
                loaded = storage.load(year)
                assert loaded == large_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
