#!/usr/bin/env python3
"""Translation Coverage Verification Tool

This script validates that all UI elements have proper translation coverage
and identifies any remaining hardcoded strings.
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple


def load_translations() -> Dict[str, Dict[str, str]]:
    """Load the translations.json file."""
    translations_path = Path("app/config/translations.json")
    with open(translations_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def scan_python_files() -> List[Tuple[str, int, str]]:
    """Scan Python files for potential hardcoded strings."""
    issues = []
    
    # Patterns that indicate potential hardcoded user-facing strings
    patterns = [
        r'QMessageBox\.[a-zA-Z]+\([^)]*["\'][A-Z][^"\'{}]*["\']',  # QMessageBox with hardcoded text
        r'setText\(["\'][A-Z][^"\'{}]*["\']\)',  # setText with hardcoded text
        r'setWindowTitle\(["\'][A-Z][^"\'{}]*["\']\)',  # setWindowTitle with hardcoded text
        r'setPlaceholderText\(["\'][A-Z][^"\'{}]*["\']\)',  # setPlaceholderText with hardcoded text
        r'show_error\(["\'][A-Z][^"\'{}]*["\']\)',  # show_error with hardcoded text
    ]
    
    # Scan all Python files
    for py_file in Path("app").rglob("*.py"):
        with open(py_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                matches = re.findall(pattern, line)
                if matches:
                    # Skip if line already contains get_translations()
                    if 'get_translations(' not in line:
                        issues.append((str(py_file), line_num, line.strip()))
    
    return issues


def scan_ui_files() -> List[Tuple[str, int, str]]:
    """Scan .ui files for hardcoded English strings."""
    issues = []
    
    # Pattern for hardcoded English text in UI files
    pattern = r'<string>([A-Z][a-zA-Z ]+)</string>'
    
    for ui_file in Path("app/ui").rglob("*.ui"):
        with open(ui_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            matches = re.findall(pattern, line)
            for match in matches:
                # Skip class names and other non-user-facing strings
                if match not in ['Dialog', 'MainWindow']:
                    issues.append((str(ui_file), line_num, match))
    
    return issues


def check_translation_keys_exist(translations: Dict[str, Dict[str, str]]) -> List[str]:
    """Check for missing translation keys by scanning get_translations() calls."""
    missing_keys = []
    
    # Find all get_translations() calls
    for py_file in Path("app").rglob("*.py"):
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all translation keys used in code
        pattern = r'get_translations\(["\']([^"\']+)["\']\)'
        matches = re.findall(pattern, content)
        
        for key in matches:
            # Check if key exists in both languages
            if key not in translations.get('en', {}):
                missing_keys.append(f"Missing English translation for key: {key}")
            if key not in translations.get('de', {}):
                missing_keys.append(f"Missing German translation for key: {key}")
    
    return missing_keys


def check_translation_completeness(translations: Dict[str, Dict[str, str]]) -> List[str]:
    """Check if all translation keys exist in both languages."""
    issues = []
    
    en_keys = set(translations.get('en', {}).keys())
    de_keys = set(translations.get('de', {}).keys())
    
    # Find keys that exist in English but not German
    missing_in_german = en_keys - de_keys
    for key in missing_in_german:
        issues.append(f"Key '{key}' exists in English but missing in German")
    
    # Find keys that exist in German but not English
    missing_in_english = de_keys - en_keys
    for key in missing_in_english:
        issues.append(f"Key '{key}' exists in German but missing in English")
    
    return issues


def verify_dialog_translations() -> List[str]:
    """Verify that dialog translation setup functions are called."""
    issues = []
    
    dialog_handlers = [
        ('app/handlers/teacher_handlers.py', '_setup_teacher_dialog_translations'),
        ('app/handlers/child_handlers.py', '_setup_child_dialog_translations'),
        ('app/handlers/tandem_handlers.py', '_setup_tandem_dialog_translations'),
    ]
    
    for file_path, function_name in dialog_handlers:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if function is defined
        if function_name not in content:
            issues.append(f"Missing translation setup function: {function_name} in {file_path}")
        
        # Check if function is called
        if f"{function_name}(" not in content:
            issues.append(f"Translation setup function not called: {function_name} in {file_path}")
    
    return issues


def main():
    """Run the translation verification."""
    print("Translation Coverage Verification")
    print("=" * 50)
    
    try:
        # Load translations
        translations = load_translations()
        print(f"Loaded translations: {len(translations.get('en', {}))} English, {len(translations.get('de', {}))} German keys")
        
        # Scan for hardcoded strings in Python files
        print("\nScanning Python files for hardcoded strings...")
        python_issues = scan_python_files()
        if python_issues:
            print(f"Found {len(python_issues)} potential hardcoded strings:")
            for file_path, line_num, line in python_issues:
                print(f"  {file_path}:{line_num} - {line}")
        else:
            print("No hardcoded strings found in Python files")
        
        # Scan UI files
        print("\nScanning UI files for hardcoded text...")
        ui_issues = scan_ui_files()
        if ui_issues:
            print(f"Found {len(ui_issues)} hardcoded strings in UI files:")
            for file_path, line_num, text in ui_issues:
                print(f"  {file_path}:{line_num} - '{text}'")
            print("  Note: UI files contain hardcoded text by design. These should be translated in Python code.")
        else:
            print("No hardcoded strings found in UI files")
        
        # Check for missing translation keys
        print("\nChecking for missing translation keys...")
        missing_keys = check_translation_keys_exist(translations)
        if missing_keys:
            print(f"Found {len(missing_keys)} missing translation keys:")
            for issue in missing_keys:
                print(f"  {issue}")
        else:
            print("All referenced translation keys exist")
        
        # Check translation completeness
        print("\nChecking translation completeness...")
        completeness_issues = check_translation_completeness(translations)
        if completeness_issues:
            print(f"Found {len(completeness_issues)} completeness issues:")
            for issue in completeness_issues:
                print(f"  {issue}")
        else:
            print("All translations are complete in both languages")
        
        # Verify dialog translations
        print("\nVerifying dialog translation setup...")
        dialog_issues = verify_dialog_translations()
        if dialog_issues:
            print(f"Found {len(dialog_issues)} dialog translation issues:")
            for issue in dialog_issues:
                print(f"  {issue}")
        else:
            print("All dialog translation functions are properly set up")
        
        # Summary
        total_issues = len(python_issues) + len(missing_keys) + len(completeness_issues) + len(dialog_issues)
        print(f"\nSummary")
        print(f"  Python hardcoded strings: {len(python_issues)}")
        print(f"  UI hardcoded strings: {len(ui_issues)} (expected)")
        print(f"  Missing translation keys: {len(missing_keys)}")
        print(f"  Translation completeness issues: {len(completeness_issues)}")
        print(f"  Dialog setup issues: {len(dialog_issues)}")
        print(f"  Total critical issues: {total_issues}")
        
        if total_issues == 0:
            print("\nExcellent! Translation coverage appears to be complete.")
            print("   Consider running the application to verify everything works as expected.")
        else:
            print(f"\nFound {total_issues} issues that should be addressed.")
        
        return total_issues
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return 1


if __name__ == "__main__":
    exit(main())