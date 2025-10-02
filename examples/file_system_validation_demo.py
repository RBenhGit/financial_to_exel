"""
File System Organization Validator - Usage Examples (Task 206)

Demonstrates how to use the FileSystemOrganizationValidator for:
- Single company validation
- Batch validation of multiple companies
- Automated repair of directory structures
- Export of validation reports
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.file_system_validator import FileSystemOrganizationValidator
from utils.directory_structure_helper import DirectoryStructureValidator


def example_1_single_company_validation():
    """
    Example 1: Validate a single company directory structure
    """
    print("=" * 80)
    print("Example 1: Single Company Validation")
    print("=" * 80)

    # Initialize validator
    validator = FileSystemOrganizationValidator(base_path="data/companies")

    # Validate a single company
    print("\n🔍 Validating AMD company structure...")
    result = validator.validate_single_company("AMD")

    # Display results
    compliance = result['overall_compliance']
    print(f"\n📊 Compliance Status: {compliance['status']}")
    print(f"   Overall Score: {compliance['overall_score']}")
    print(f"   Directory Score: {compliance['directory_score']}")
    print(f"   Excel Score: {compliance['excel_score']}")
    print(f"   Issues: {compliance['total_issues']}")
    print(f"   Warnings: {compliance['total_warnings']}")

    # Show top recommendations if any
    if result['actionable_recommendations']:
        print(f"\n📋 Top Recommendations:")
        for i, rec in enumerate(result['actionable_recommendations'][:3], 1):
            print(f"   {i}. [{rec['priority']}] {rec['action']}")

    print()


def example_2_batch_validation():
    """
    Example 2: Batch validate multiple companies
    """
    print("=" * 80)
    print("Example 2: Batch Validation")
    print("=" * 80)

    # Initialize validator
    validator = FileSystemOrganizationValidator(base_path="data/companies")

    # Validate all companies
    print("\n🔍 Running batch validation on all companies...")
    results = validator.validate_all_companies()

    # Display batch summary
    print(f"\n📊 Batch Validation Summary:")
    print(f"   Total Companies: {results['total_companies']}")
    print(f"   Successfully Validated: {results['companies_validated']}")
    print(f"   Fully Compliant: {results['fully_compliant']}")
    print(f"   Partially Compliant: {results['partially_compliant']}")
    print(f"   Non-Compliant: {results['non_compliant']}")
    print(f"   Critical Issues: {results['critical_issues']}")

    # Display aggregate statistics
    stats = results['aggregate_statistics']
    print(f"\n📈 Aggregate Statistics:")
    print(f"   Average Compliance Score: {stats['average_compliance_score']}")
    print(f"   Average Directory Score: {stats['average_directory_score']}")
    print(f"   Average Excel Score: {stats['average_excel_score']}")
    print(f"   Total Issues: {stats['total_issues']}")
    print(f"   Total Warnings: {stats['total_warnings']}")

    # Show most common issues
    if stats['most_common_issues']:
        print(f"\n⚠️  Most Common Issues:")
        for issue in stats['most_common_issues'][:5]:
            print(f"   - {issue['type']}: {issue['count']} occurrences")

    print()


def example_3_specific_companies():
    """
    Example 3: Validate specific companies only
    """
    print("=" * 80)
    print("Example 3: Validate Specific Companies")
    print("=" * 80)

    # Initialize validator
    validator = FileSystemOrganizationValidator(base_path="data/companies")

    # Validate only specific tickers
    companies = ['AMD', 'NVDA']
    print(f"\n🔍 Validating specific companies: {', '.join(companies)}...")

    results = validator.validate_all_companies(company_tickers=companies)

    # Display results for each company
    for ticker in companies:
        if ticker in results['company_results']:
            company_result = results['company_results'][ticker]

            if 'error' not in company_result:
                compliance = company_result['overall_compliance']
                print(f"\n📊 {ticker}:")
                print(f"   Status: {compliance['status']}")
                print(f"   Score: {compliance['overall_score']}")
                print(f"   Issues: {compliance['total_issues']}")
            else:
                print(f"\n❌ {ticker}: Validation failed - {company_result['error']}")

    print()


def example_4_auto_repair():
    """
    Example 4: Validate with automatic repair
    """
    print("=" * 80)
    print("Example 4: Validation with Auto-Repair")
    print("=" * 80)

    # Initialize validator
    validator = FileSystemOrganizationValidator(base_path="data/companies")

    print("\n🔧 Running validation with auto-repair enabled...")
    print("   (This will attempt to fix detected issues automatically)")

    results = validator.validate_all_companies(auto_fix=True)

    print(f"\n✅ Auto-repair completed!")
    print(f"   Companies repaired: {results['companies_validated']}")
    print(f"   Remaining issues: {results['critical_issues']}")

    print()


def example_5_export_reports():
    """
    Example 5: Export validation reports
    """
    print("=" * 80)
    print("Example 5: Export Validation Reports")
    print("=" * 80)

    # Initialize validator
    validator = FileSystemOrganizationValidator(base_path="data/companies")

    # Run validation
    print("\n🔍 Running validation...")
    validator.validate_all_companies()

    # Export to different formats
    output_dir = Path("validation_reports")
    output_dir.mkdir(exist_ok=True)

    print("\n📤 Exporting reports...")

    # JSON export
    json_result = validator.export_batch_results(
        output_path=str(output_dir / "validation_report.json"),
        format='json'
    )
    if json_result['success']:
        print(f"   ✅ JSON report: {json_result['output_path']}")

    # HTML export
    html_result = validator.export_batch_results(
        output_path=str(output_dir / "validation_report.html"),
        format='html'
    )
    if html_result['success']:
        print(f"   ✅ HTML report: {html_result['output_path']}")

    # CSV export
    csv_result = validator.export_batch_results(
        output_path=str(output_dir / "validation_report.csv"),
        format='csv'
    )
    if csv_result['success']:
        print(f"   ✅ CSV report: {csv_result['output_path']}")

    print()


def example_6_text_summary():
    """
    Example 6: Get text summary of validation results
    """
    print("=" * 80)
    print("Example 6: Text Summary")
    print("=" * 80)

    # Initialize validator
    validator = FileSystemOrganizationValidator(base_path="data/companies")

    # Run validation
    validator.validate_all_companies()

    # Get and display text summary
    print("\n📄 Validation Summary:")
    print(validator.get_compliance_summary())


def example_7_programmatic_integration():
    """
    Example 7: Programmatic integration in application code
    """
    print("=" * 80)
    print("Example 7: Programmatic Integration")
    print("=" * 80)

    # Initialize validator with custom base path
    validator = FileSystemOrganizationValidator(
        base_path="data/companies"
    )

    # Run validation
    results = validator.validate_all_companies()

    # Check if validation passed
    if results['critical_issues'] > 0:
        print("\n❌ Validation FAILED - Critical issues detected!")
        print(f"   Critical Issues: {results['critical_issues']}")

        # Get detailed recommendations
        for rec in results['recommendations_summary']:
            if rec['priority'] == 'CRITICAL':
                print(f"\n   🚨 {rec['issue_type']}:")
                print(f"      Affected: {', '.join(rec['affected_companies'][:3])}")
                if rec['automated_fix_available']:
                    print(f"      Auto-fix: Available ✅")
                else:
                    print(f"      Auto-fix: Manual intervention required")

        # Exit with error code
        print("\n   Exiting with error code 1")
        return 1

    else:
        print("\n✅ Validation PASSED - All companies compliant!")
        print(f"   Average Compliance Score: {results['aggregate_statistics']['average_compliance_score']}")
        return 0


def example_8_integration_with_registry():
    """
    Example 8: Integration with ValidationRegistry for rule-based validation
    """
    print("=" * 80)
    print("Example 8: ValidationRegistry Integration")
    print("=" * 80)

    try:
        from core.validation.validation_registry import ValidationRegistry

        # Create registry
        registry = ValidationRegistry()

        # Initialize validator with registry
        validator = FileSystemOrganizationValidator(
            base_path="data/companies",
            validation_registry=registry
        )

        print("\n✅ ValidationRegistry integrated successfully!")
        print("   Validation rules will be applied from registry")

        # Run validation with registry rules
        results = validator.validate_all_companies()

        print(f"\n📊 Validation completed with registry rules:")
        print(f"   Companies validated: {results['companies_validated']}")
        print(f"   Average score: {results['aggregate_statistics']['average_compliance_score']}")

    except ImportError:
        print("\n⚠️  ValidationRegistry not available - using standard validation")
        print("   Install ValidationRegistry for enhanced rule-based validation")

    print()


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print(" File System Organization Validator - Usage Examples")
    print("=" * 80 + "\n")

    try:
        # Run examples
        example_1_single_company_validation()
        example_2_batch_validation()
        example_3_specific_companies()
        # example_4_auto_repair()  # Commented out to avoid modifying data
        example_5_export_reports()
        example_6_text_summary()
        example_7_programmatic_integration()
        example_8_integration_with_registry()

        print("\n" + "=" * 80)
        print(" All examples completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
