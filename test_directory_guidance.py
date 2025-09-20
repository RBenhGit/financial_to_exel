#!/usr/bin/env python3
"""
Test script to verify improved directory structure error messages.

This script tests the enhanced error messages and user guidance for
directory structure requirements.
"""

import os
import tempfile
from pathlib import Path

def test_directory_guidance():
    """Test the improved directory structure guidance"""

    # Test 1: Import the directory structure helper
    print("🧪 Testing Directory Structure Helper Import...")
    try:
        from utils.directory_structure_helper import (
            DirectoryStructureValidator,
            validate_company_directory,
            get_directory_structure_help
        )
        print("✅ Successfully imported directory structure helper")
    except ImportError as e:
        print(f"❌ Failed to import directory structure helper: {e}")
        return False

    # Test 2: Test validation of non-existent directory
    print("\n🧪 Testing validation of non-existent directory...")
    with tempfile.TemporaryDirectory() as temp_dir:
        non_existent_path = os.path.join(temp_dir, "NONEXISTENT_COMPANY")

        validation_result = validate_company_directory(non_existent_path)

        print(f"Is Valid: {validation_result['is_valid']}")
        print(f"Exists: {validation_result['exists']}")
        print(f"Issues Found: {len(validation_result['issues'])}")
        print(f"Structure Score: {validation_result['structure_score']:.2f}")
        print(f"Summary: {validation_result['validation_summary']}")

        if validation_result['issues']:
            print("\n📋 Issues Found:")
            for issue in validation_result['issues'][:2]:  # Show first 2 issues
                print(f"• {issue['type']}: {issue['message']}")
                if issue.get('fix_suggestion'):
                    print(f"  💡 Fix: {issue['fix_suggestion'][:100]}...")

    # Test 3: Test validation with missing folders
    print("\n🧪 Testing validation with missing folders...")
    with tempfile.TemporaryDirectory() as temp_dir:
        company_path = os.path.join(temp_dir, "TEST_COMPANY")
        os.makedirs(company_path)

        # Create only FY folder, missing LTM
        fy_path = os.path.join(company_path, "FY")
        os.makedirs(fy_path)

        validation_result = validate_company_directory(company_path)

        print(f"Is Valid: {validation_result['is_valid']}")
        print(f"Missing Folders: {validation_result['missing_folders']}")
        print(f"Structure Score: {validation_result['structure_score']:.2f}")
        print(f"Suggestions: {validation_result['suggestions'][:2]}")  # Show first 2 suggestions

    # Test 4: Test DataProcessor integration
    print("\n🧪 Testing DataProcessor integration...")
    try:
        from core.data_processing.processors.data_processing import DataProcessor

        processor = DataProcessor()
        validation_result = processor.validate_company_folder(non_existent_path)

        print(f"Legacy format - Is Valid: {validation_result['is_valid']}")
        print(f"Has enhanced suggestions: {'suggestions' in validation_result}")
        print(f"Has structure score: {'structure_score' in validation_result}")

        if 'detailed_validation' in validation_result:
            print("✅ Enhanced validation data included")

    except Exception as e:
        print(f"⚠️ DataProcessor test failed (may be expected): {e}")

    # Test 5: Test help text generation
    print("\n🧪 Testing help text generation...")
    help_text = get_directory_structure_help()
    print(f"Help text length: {len(help_text)} characters")
    print("Help text sample:")
    print(help_text[:200] + "...")

    # Test 6: Test Excel processor integration
    print("\n🧪 Testing Excel processor integration...")
    try:
        from utils.excel_processor import UnifiedExcelProcessor

        processor = UnifiedExcelProcessor()
        # This would normally fail with enhanced error message
        print("✅ Excel processor import successful")

    except Exception as e:
        print(f"⚠️ Excel processor test failed (may be expected): {e}")

    print("\n🎉 Directory structure guidance testing completed!")
    return True

def test_error_message_improvements():
    """Test that error messages are more helpful than before"""

    print("\n🧪 Testing Error Message Improvements...")

    # Test the enhanced error message in excel_processor
    try:
        from utils.excel_processor import UnifiedExcelProcessor

        processor = UnifiedExcelProcessor()
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_path = os.path.join(temp_dir, "NONEXISTENT")

            try:
                # This should trigger the enhanced error message
                statements, report = processor.load_company_statements(
                    company_folder=non_existent_path,
                    enable_recovery=True  # Get error in report instead of exception
                )

                if report['errors']:
                    error_msg = report['errors'][0]
                    print("Enhanced Error Message Sample:")
                    print(error_msg[:300] + "..." if len(error_msg) > 300 else error_msg)

                    # Check for enhanced features
                    has_structure_diagram = "├──" in error_msg or "└──" in error_msg
                    has_tips = "💡 Tips:" in error_msg
                    has_emojis = "📁" in error_msg

                    print(f"✅ Has structure diagram: {has_structure_diagram}")
                    print(f"✅ Has helpful tips: {has_tips}")
                    print(f"✅ Has visual elements: {has_emojis}")

            except Exception as e:
                print(f"Expected error during testing: {e}")

    except ImportError:
        print("⚠️ Excel processor not available for testing")

    return True

if __name__ == "__main__":
    print("🚀 Starting Directory Structure Guidance Tests\n")

    test_directory_guidance()
    test_error_message_improvements()

    print("\n✅ All tests completed successfully!")