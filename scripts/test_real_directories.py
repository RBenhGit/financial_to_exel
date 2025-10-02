"""
Test script to validate real company directories (Task 180)

Tests the enhanced DirectoryStructureValidator with actual company data
for GOOG, MSFT, NVDA, TSLA, and V.
"""

from pathlib import Path
import json
from utils.directory_structure_helper import DirectoryStructureValidator


def test_real_companies():
    """Test validation with real company directories"""

    validator = DirectoryStructureValidator()

    # Real companies to test
    tickers = ['GOOG', 'MSFT', 'NVDA', 'TSLA', 'V']

    print("=" * 80)
    print("TESTING REAL COMPANY DIRECTORIES (Task 180)")
    print("=" * 80)
    print()

    results = {}

    for ticker in tickers:
        print(f"\n{'='*80}")
        print(f"Validating {ticker}")
        print(f"{'='*80}\n")

        # Run comprehensive validation
        report = validator.validate_directory_structure(ticker)

        # Store results
        results[ticker] = report

        # Print summary
        print(f"Ticker: {ticker}")
        print(f"Path: {report['company_path']}")
        print(f"Timestamp: {report['validation_timestamp']}")
        print()

        # Overall compliance
        compliance = report['overall_compliance']
        print(f"Overall Compliance Status: {compliance['status']}")
        print(f"Overall Score: {compliance['overall_score']:.2f}")
        print(f"  - Directory Score: {compliance['directory_score']:.2f}")
        print(f"  - Excel Score: {compliance['excel_score']:.2f}")
        print(f"Total Issues: {compliance['total_issues']}")
        print(f"Total Warnings: {compliance['total_warnings']}")
        print()

        # Directory validation summary
        dir_val = report['directory_validation']
        print(f"Directory Validation: {dir_val['validation_summary']}")
        print(f"Structure Score: {dir_val['structure_score']:.2f}")
        print(f"Missing Folders: {dir_val['missing_folders']}")
        print(f"Missing Files: {dir_val['missing_files']}")
        print()

        # Excel validations
        print(f"Excel File Validations: {len(report['excel_validations'])} files")
        for file_key, excel_val in report['excel_validations'].items():
            status_icon = "✅" if excel_val['is_valid'] else "❌"
            print(f"  {status_icon} {file_key}")
            if excel_val['is_valid']:
                print(f"     Periods: {len(excel_val['detected_periods'])} ({excel_val['detected_periods']})")
            else:
                print(f"     Issues: {len(excel_val['issues'])}")
                for issue in excel_val['issues'][:2]:  # Show first 2 issues
                    print(f"       - {issue['message']}")

        # Actionable recommendations
        recommendations = report['actionable_recommendations']
        if recommendations:
            print(f"\nActionable Recommendations: {len(recommendations)}")
            for i, rec in enumerate(recommendations[:5], 1):  # Show first 5
                print(f"  {i}. [{rec['priority']}] {rec['action']}")
                print(f"     Category: {rec['category']}")
                print(f"     Impact: {rec['impact']}")
        else:
            print("\n✅ No recommendations - directory structure is compliant!")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()

    compliant = sum(1 for r in results.values()
                   if r['overall_compliance']['status'] == 'COMPLIANT')
    partial = sum(1 for r in results.values()
                 if r['overall_compliance']['status'] == 'PARTIALLY_COMPLIANT')
    non_compliant = sum(1 for r in results.values()
                       if r['overall_compliance']['status'] == 'NON_COMPLIANT')

    print(f"Total Companies Tested: {len(tickers)}")
    print(f"  Compliant: {compliant}")
    print(f"  Partially Compliant: {partial}")
    print(f"  Non-Compliant: {non_compliant}")
    print()

    avg_overall_score = sum(r['overall_compliance']['overall_score']
                           for r in results.values()) / len(results)
    avg_dir_score = sum(r['overall_compliance']['directory_score']
                       for r in results.values()) / len(results)
    avg_excel_score = sum(r['overall_compliance']['excel_score']
                         for r in results.values()) / len(results)

    print(f"Average Scores:")
    print(f"  Overall: {avg_overall_score:.2f}")
    print(f"  Directory: {avg_dir_score:.2f}")
    print(f"  Excel: {avg_excel_score:.2f}")
    print()

    # Save detailed report
    output_file = Path("data/cache/directory_validation_report.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Detailed report saved to: {output_file}")
    print()

    return results


if __name__ == "__main__":
    test_real_companies()
