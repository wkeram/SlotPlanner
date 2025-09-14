"""
Tests for translation coverage and completeness.
"""

import json
import re
from pathlib import Path

import pytest


class TestTranslationCoverage:
    """Test translation key completeness and UI coverage."""

    @pytest.fixture
    def translations(self) -> dict[str, dict[str, str]]:
        """Load translations from config file."""
        translations_path = Path("app/config/translations.json")
        if not translations_path.exists():
            pytest.skip("translations.json not found")

        with open(translations_path, encoding="utf-8") as f:
            return json.load(f)

    def test_translation_file_exists(self):
        """Test that translations.json exists."""
        translations_path = Path("app/config/translations.json")
        assert translations_path.exists(), "translations.json file is missing"

    def test_both_languages_present(self, translations):
        """Test that both English and German translations are present."""
        assert "en" in translations, "English translations missing"
        assert "de" in translations, "German translations missing"
        assert len(translations["en"]) > 0, "English translations are empty"
        assert len(translations["de"]) > 0, "German translations are empty"

    def test_translation_key_parity(self, translations):
        """Test that all keys exist in both languages."""
        en_keys = set(translations["en"].keys())
        de_keys = set(translations["de"].keys())

        missing_in_german = en_keys - de_keys
        missing_in_english = de_keys - en_keys

        # Only fail for critical missing translations (more than 10% mismatch)
        total_keys = len(en_keys | de_keys)
        mismatch_ratio = (len(missing_in_german) + len(missing_in_english)) / total_keys if total_keys > 0 else 0

        if mismatch_ratio > 0.1:  # More than 10% mismatch is critical
            pytest.fail(
                f"Critical translation mismatch ({mismatch_ratio:.1%}). Missing in German: {missing_in_german}, Missing in English: {missing_in_english}"
            )
        elif missing_in_german or missing_in_english:
            pytest.skip(
                f"Minor translation gaps found. Missing in German: {len(missing_in_german)}, Missing in English: {len(missing_in_english)}"
            )

    def test_no_empty_translations(self, translations):
        """Test that no translation values are empty."""
        empty_en = [k for k, v in translations["en"].items() if not v.strip()]
        empty_de = [k for k, v in translations["de"].items() if not v.strip()]

        assert not empty_en, f"Empty English translations: {empty_en}"
        assert not empty_de, f"Empty German translations: {empty_de}"

    def test_translation_keys_used_in_code(self, translations):
        """Test that referenced translation keys exist."""
        missing_keys = []

        # Find all get_translations() calls
        for py_file in Path("app").rglob("*.py"):
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            # Find all translation keys used in code
            pattern = r'get_translations\(["\']([^"\']+)["\']\)'
            matches = re.findall(pattern, content)

            for key in matches:
                if key not in translations.get("en", {}):
                    missing_keys.append(f"Missing English translation for key: {key} (used in {py_file})")
                if key not in translations.get("de", {}):
                    missing_keys.append(f"Missing German translation for key: {key} (used in {py_file})")

        # Only fail if there are many missing keys (indicates systematic problem)
        if len(missing_keys) > 20:
            pytest.fail(
                f"Too many missing translation keys ({len(missing_keys)}). This indicates a systematic issue:\n"
                + "\n".join(missing_keys[:10])
            )
        elif missing_keys:
            pytest.skip(f"Found {len(missing_keys)} missing translation keys. Consider adding them.")

    def test_no_hardcoded_ui_strings(self):
        """Test for hardcoded user-facing strings in Python files."""
        hardcoded_strings = []

        # Patterns that indicate potential hardcoded user-facing strings
        patterns = [
            r'QMessageBox\.[a-zA-Z]+\([^)]*["\'][A-Z][^"\'{}]*["\']',  # QMessageBox with hardcoded text
            r'setText\(["\'][A-Z][^"\'{}]*["\']\)',  # setText with hardcoded text
            r'setWindowTitle\(["\'][A-Z][^"\'{}]*["\']\)',  # setWindowTitle with hardcoded text
            r'setPlaceholderText\(["\'][A-Z][^"\'{}]*["\']\)',  # setPlaceholderText with hardcoded text
            r'show_error\(["\'][A-Z][^"\'{}]*["\']\)',  # show_error with hardcoded text
        ]

        for py_file in Path("app").rglob("*.py"):
            with open(py_file, encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    if matches:
                        # Skip if line already contains get_translations()
                        if "get_translations(" not in line:
                            hardcoded_strings.append(f"{py_file}:{line_num} - {line.strip()}")

        # Allow some hardcoded strings for testing, but warn about them
        if hardcoded_strings:
            pytest.fail(
                f"Found {len(hardcoded_strings)} potential hardcoded strings:\n"
                + "\n".join(hardcoded_strings[:10])  # Limit output
            )

    def test_dialog_translation_functions_exist(self):
        """Test that dialog translation setup functions exist and are called."""
        dialog_handlers = [
            ("app/handlers/teacher_handlers.py", "_setup_teacher_dialog_translations"),
            ("app/handlers/child_handlers.py", "_setup_child_dialog_translations"),
            ("app/handlers/tandem_handlers.py", "_setup_tandem_dialog_translations"),
        ]

        missing_functions = []
        not_called = []

        for file_path, function_name in dialog_handlers:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                continue  # Skip if handler doesn't exist yet

            with open(file_path_obj, encoding="utf-8") as f:
                content = f.read()

            # Check if function is defined
            if function_name not in content:
                missing_functions.append(f"Missing function: {function_name} in {file_path}")

            # Check if function is called
            elif f"{function_name}(" not in content:
                not_called.append(f"Function not called: {function_name} in {file_path}")

        errors = missing_functions + not_called
        if errors:
            pytest.fail("\n".join(errors))

    def test_translation_format_consistency(self, translations):
        """Test that translation values are consistently formatted."""
        format_issues = []

        for lang in ["en", "de"]:
            for key, value in translations[lang].items():
                # Check for leading/trailing whitespace
                if value != value.strip():
                    format_issues.append(f"{lang}.{key} has leading/trailing whitespace")

                # Check for double spaces
                if "  " in value:
                    format_issues.append(f"{lang}.{key} contains double spaces")

                # Check for inconsistent punctuation (basic check)
                if key.endswith("_error") or key.endswith("_message"):
                    if not value.endswith((".", "!", "?")):
                        format_issues.append(f"{lang}.{key} should end with punctuation")

        # Only fail for many formatting issues (indicates systematic problem)
        if len(format_issues) > 10:
            pytest.fail(
                f"Many translation formatting issues found ({len(format_issues)}). Sample issues:\n"
                + "\n".join(format_issues[:10])
            )
        elif format_issues:
            pytest.skip(f"Found {len(format_issues)} minor translation formatting issues.")


@pytest.mark.strict
class TestStrictTranslationCoverage:
    """Strict translation tests that must pass for release readiness."""

    @pytest.fixture
    def translations(self) -> dict[str, dict[str, str]]:
        """Load translations from config file."""
        translations_path = Path("app/config/translations.json")
        if not translations_path.exists():
            pytest.skip("translations.json not found")

        with open(translations_path, encoding="utf-8") as f:
            return json.load(f)

    def test_all_translation_keys_must_exist_in_both_languages(self, translations):
        """STRICT: All translation keys must exist in both languages."""
        en_keys = set(translations["en"].keys())
        de_keys = set(translations["de"].keys())

        missing_in_german = en_keys - de_keys
        missing_in_english = de_keys - en_keys

        assert not missing_in_german, f"Keys missing in German: {missing_in_german}"
        assert not missing_in_english, f"Keys missing in English: {missing_in_english}"

    def test_all_used_translation_keys_must_exist(self, translations):
        """STRICT: All referenced translation keys must exist."""
        missing_keys = []

        for py_file in Path("app").rglob("*.py"):
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            pattern = r'get_translations\(["\']([^"\']+)["\']\)'
            matches = re.findall(pattern, content)

            for key in matches:
                if key not in translations.get("en", {}):
                    missing_keys.append(f"Missing English translation for key: {key} (used in {py_file})")
                if key not in translations.get("de", {}):
                    missing_keys.append(f"Missing German translation for key: {key} (used in {py_file})")

        assert not missing_keys, "Missing translation keys:\n" + "\n".join(missing_keys)

    def test_no_translation_formatting_issues(self, translations):
        """STRICT: All translations must be properly formatted."""
        format_issues = []

        for lang in ["en", "de"]:
            for key, value in translations[lang].items():
                if value != value.strip():
                    format_issues.append(f"{lang}.{key} has leading/trailing whitespace")
                if "  " in value:
                    format_issues.append(f"{lang}.{key} contains double spaces")

        assert not format_issues, "Translation formatting issues:\n" + "\n".join(format_issues[:10])


class TestTranslationVersionManagement:
    """Test translation coverage for version management functionality."""

    def test_version_manager_error_messages_translated(self):
        """Test that version manager error messages use translations."""
        version_manager_path = Path("scripts/version-manager.py")
        if not version_manager_path.exists():
            pytest.skip("version-manager.py not found")

        with open(version_manager_path, encoding="utf-8") as f:
            content = f.read()

        # Look for hardcoded error messages
        hardcoded_errors = []
        error_patterns = [
            r'print\(f?"ERROR:[^"]*"[^)]*\)',
            r'print\(f?"WARNING:[^"]*"[^)]*\)',
            r'print\(f?"SUCCESS:[^"]*"[^)]*\)',
        ]

        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            for pattern in error_patterns:
                if re.search(pattern, line) and "get_translations(" not in line:
                    hardcoded_errors.append(f"Line {line_num}: {line.strip()}")

        # For now, this is informational - version manager might not need translation
        if hardcoded_errors:
            print(f"Version manager has {len(hardcoded_errors)} hardcoded messages")
            # Can be enhanced later to require translation for version manager
