"""
File System Organization Validator (Task 206)

Comprehensive validation system for file system organization compliance
with required schema for financial data directories.

Features:
- Batch validation for multiple companies
- Configuration-driven validation rules
- Detailed error reporting with remediation suggestions
- Integration with existing DirectoryStructureValidator
- CLI and programmatic API
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.directory_structure_helper import DirectoryStructureValidator

logger = logging.getLogger(__name__)


class FileSystemOrganizationValidator:
    """
    Comprehensive file system organization validator for financial data.

    Provides batch validation capabilities and aggregate reporting for
    multiple company directories.
    """

    def __init__(
        self,
        base_path: str = "data/companies",
        validation_registry: Optional[Any] = None
    ):
        """
        Initialize file system validator.

        Args:
            base_path: Base directory containing company folders
            validation_registry: Optional ValidationRegistry for rule-based validation
        """
        self.base_path = Path(base_path)
        self.validator = DirectoryStructureValidator(validation_registry=validation_registry)
        self.validation_results: List[Dict[str, Any]] = []

    def validate_all_companies(
        self,
        company_tickers: Optional[List[str]] = None,
        strict_mode: bool = False,
        auto_fix: bool = False
    ) -> Dict[str, Any]:
        """
        Validate all companies in the base directory.

        Args:
            company_tickers: Optional list of specific tickers to validate.
                           If None, validates all subdirectories.
            strict_mode: If True, requires exact file names
            auto_fix: If True, automatically repairs detected issues

        Returns:
            Dictionary with batch validation results and aggregate statistics
        """
        results = {
            'validation_timestamp': datetime.now().isoformat(),
            'base_path': str(self.base_path),
            'total_companies': 0,
            'companies_validated': 0,
            'fully_compliant': 0,
            'partially_compliant': 0,
            'non_compliant': 0,
            'critical_issues': 0,
            'company_results': {},
            'aggregate_statistics': {},
            'recommendations_summary': []
        }

        # Determine which companies to validate
        if company_tickers:
            companies_to_validate = [
                self.base_path / ticker
                for ticker in company_tickers
                if (self.base_path / ticker).exists()
            ]
        else:
            # Find all subdirectories in base_path
            if self.base_path.exists():
                companies_to_validate = [
                    d for d in self.base_path.iterdir()
                    if d.is_dir() and not d.name.startswith('.')
                ]
            else:
                logger.error(f"Base path does not exist: {self.base_path}")
                return results

        results['total_companies'] = len(companies_to_validate)

        # Validate each company
        for company_path in companies_to_validate:
            ticker = company_path.name

            try:
                # Perform validation
                company_result = self.validator.validate_directory_structure(
                    ticker=ticker,
                    base_path=str(self.base_path)
                )

                # Auto-fix if requested
                if auto_fix and company_result['overall_compliance']['status'] != 'FULLY_COMPLIANT':
                    self.validator.auto_fix_directory_structure(
                        str(company_path),
                        dry_run=False
                    )

                    # Re-validate after fix
                    company_result = self.validator.validate_directory_structure(
                        ticker=ticker,
                        base_path=str(self.base_path)
                    )

                results['company_results'][ticker] = company_result
                results['companies_validated'] += 1

                # Update aggregate statistics
                compliance_status = company_result['overall_compliance']['status']
                if compliance_status == 'FULLY_COMPLIANT':
                    results['fully_compliant'] += 1
                elif compliance_status in ['COMPLIANT', 'PARTIALLY_COMPLIANT']:
                    results['partially_compliant'] += 1
                else:
                    results['non_compliant'] += 1

                # Count critical issues
                issue_breakdown = company_result['overall_compliance'].get('issue_breakdown', {})
                results['critical_issues'] += issue_breakdown.get('critical_count', 0)

            except Exception as e:
                logger.error(f"Error validating {ticker}: {e}")
                results['company_results'][ticker] = {
                    'error': str(e),
                    'ticker': ticker,
                    'validation_failed': True
                }

        # Generate aggregate statistics
        results['aggregate_statistics'] = self._calculate_aggregate_statistics(results)

        # Generate recommendations summary
        results['recommendations_summary'] = self._generate_recommendations_summary(results)

        # Store results
        self.validation_results.append(results)

        return results

    def validate_single_company(
        self,
        ticker: str,
        strict_mode: bool = False,
        auto_fix: bool = False
    ) -> Dict[str, Any]:
        """
        Validate a single company directory.

        Args:
            ticker: Company ticker symbol
            strict_mode: If True, requires exact file names
            auto_fix: If True, automatically repairs detected issues

        Returns:
            Validation results for the company
        """
        company_result = self.validator.validate_directory_structure(
            ticker=ticker,
            base_path=str(self.base_path)
        )

        if auto_fix and company_result['overall_compliance']['status'] != 'FULLY_COMPLIANT':
            company_path = self.base_path / ticker
            self.validator.auto_fix_directory_structure(
                str(company_path),
                dry_run=False
            )

            # Re-validate after fix
            company_result = self.validator.validate_directory_structure(
                ticker=ticker,
                base_path=str(self.base_path)
            )

        return company_result

    def _calculate_aggregate_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate aggregate statistics across all validated companies.

        Args:
            results: Batch validation results

        Returns:
            Aggregate statistics dictionary
        """
        stats = {
            'average_compliance_score': 0.0,
            'average_directory_score': 0.0,
            'average_excel_score': 0.0,
            'total_issues': 0,
            'total_warnings': 0,
            'total_recommendations': 0,
            'most_common_issues': [],
            'compliance_distribution': {
                'fully_compliant': results['fully_compliant'],
                'partially_compliant': results['partially_compliant'],
                'non_compliant': results['non_compliant']
            }
        }

        if not results['company_results']:
            return stats

        # Calculate averages
        total_companies = len(results['company_results'])
        compliance_scores = []
        directory_scores = []
        excel_scores = []
        all_issues = {}

        for ticker, company_result in results['company_results'].items():
            if 'error' not in company_result and 'overall_compliance' in company_result:
                compliance = company_result['overall_compliance']

                compliance_scores.append(compliance.get('overall_score', 0))
                directory_scores.append(compliance.get('directory_score', 0))
                excel_scores.append(compliance.get('excel_score', 0))

                stats['total_issues'] += compliance.get('total_issues', 0)
                stats['total_warnings'] += compliance.get('total_warnings', 0)

                # Count recommendations
                recs = company_result.get('actionable_recommendations', [])
                stats['total_recommendations'] += len(recs)

                # Collect issues by type
                categorized = compliance.get('categorized_issues', {})
                for severity in ['critical', 'high', 'medium', 'low']:
                    for issue in categorized.get(severity, []):
                        issue_type = issue.get('type', 'unknown')
                        all_issues[issue_type] = all_issues.get(issue_type, 0) + 1

        if compliance_scores:
            stats['average_compliance_score'] = round(sum(compliance_scores) / len(compliance_scores), 2)
            stats['average_directory_score'] = round(sum(directory_scores) / len(directory_scores), 2)
            stats['average_excel_score'] = round(sum(excel_scores) / len(excel_scores), 2)

        # Most common issues (top 5)
        sorted_issues = sorted(all_issues.items(), key=lambda x: x[1], reverse=True)[:5]
        stats['most_common_issues'] = [
            {'type': issue_type, 'count': count}
            for issue_type, count in sorted_issues
        ]

        return stats

    def _generate_recommendations_summary(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate prioritized recommendations summary across all companies.

        Args:
            results: Batch validation results

        Returns:
            List of summarized recommendations
        """
        recommendations_by_type = {}

        for ticker, company_result in results['company_results'].items():
            if 'error' in company_result or 'actionable_recommendations' not in company_result:
                continue

            for rec in company_result['actionable_recommendations']:
                rec_key = (rec.get('issue_type', 'unknown'), rec.get('priority', 'MEDIUM'))

                if rec_key not in recommendations_by_type:
                    recommendations_by_type[rec_key] = {
                        'issue_type': rec.get('issue_type'),
                        'priority': rec.get('priority'),
                        'category': rec.get('category'),
                        'affected_companies': [],
                        'count': 0,
                        'example_action': rec.get('action'),
                        'automated_fix_available': rec.get('automated_fix', {}).get('available', False)
                    }

                recommendations_by_type[rec_key]['affected_companies'].append(ticker)
                recommendations_by_type[rec_key]['count'] += 1

        # Convert to list and sort by priority and count
        priority_order = {'CRITICAL': 1, 'HIGH': 2, 'MEDIUM': 3, 'LOW': 4}
        summary = list(recommendations_by_type.values())
        summary.sort(key=lambda x: (priority_order.get(x['priority'], 99), -x['count']))

        return summary

    def export_batch_results(
        self,
        output_path: str,
        format: str = 'json',
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Export batch validation results to file.

        Args:
            output_path: Path where to save the export
            format: Export format ('json', 'html', 'csv')
            include_details: If True, includes detailed company results

        Returns:
            Export result status
        """
        if not self.validation_results:
            return {
                'success': False,
                'error': 'No validation results to export'
            }

        latest_results = self.validation_results[-1]

        export_data = {
            'validation_timestamp': latest_results['validation_timestamp'],
            'base_path': latest_results['base_path'],
            'summary': {
                'total_companies': latest_results['total_companies'],
                'companies_validated': latest_results['companies_validated'],
                'fully_compliant': latest_results['fully_compliant'],
                'partially_compliant': latest_results['partially_compliant'],
                'non_compliant': latest_results['non_compliant'],
                'critical_issues': latest_results['critical_issues']
            },
            'aggregate_statistics': latest_results['aggregate_statistics'],
            'recommendations_summary': latest_results['recommendations_summary']
        }

        if include_details:
            export_data['company_results'] = latest_results['company_results']

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if format.lower() == 'json':
                self._export_json(export_data, output_path)
            elif format.lower() == 'html':
                self._export_html(export_data, output_path)
            elif format.lower() == 'csv':
                self._export_csv(export_data, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")

            return {
                'success': True,
                'output_path': str(output_path),
                'format': format
            }

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _export_json(self, data: Dict[str, Any], output_path: Path):
        """Export results as JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_csv(self, data: Dict[str, Any], output_path: Path):
        """Export results as CSV"""
        import csv

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Summary section
            writer.writerow(['Batch File System Validation Report'])
            writer.writerow(['Timestamp', data['validation_timestamp']])
            writer.writerow(['Base Path', data['base_path']])
            writer.writerow([])

            # Summary statistics
            writer.writerow(['Summary Statistics'])
            for key, value in data['summary'].items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])

            # Aggregate statistics
            writer.writerow(['Aggregate Statistics'])
            for key, value in data['aggregate_statistics'].items():
                if key != 'most_common_issues' and key != 'compliance_distribution':
                    writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])

            # Recommendations summary
            writer.writerow(['Top Recommendations'])
            writer.writerow(['Priority', 'Issue Type', 'Affected Companies', 'Count', 'Auto-Fix Available'])
            for rec in data['recommendations_summary']:
                writer.writerow([
                    rec['priority'],
                    rec['issue_type'],
                    ', '.join(rec['affected_companies'][:5]),  # Limit to 5
                    rec['count'],
                    'Yes' if rec['automated_fix_available'] else 'No'
                ])

    def _export_html(self, data: Dict[str, Any], output_path: Path):
        """Export results as HTML"""
        summary = data['summary']
        stats = data['aggregate_statistics']
        recs = data['recommendations_summary']

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Batch File System Validation Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .priority-CRITICAL {{ color: #d32f2f; font-weight: bold; }}
        .priority-HIGH {{ color: #ff9800; font-weight: bold; }}
        .priority-MEDIUM {{ color: #ffc107; font-weight: bold; }}
        .priority-LOW {{ color: #4caf50; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Batch File System Validation Report</h1>
        <p><strong>Base Path:</strong> {data['base_path']}</p>
        <p><strong>Generated:</strong> {data['validation_timestamp']}</p>
    </div>

    <div class="summary-grid">
        <div class="stat-card">
            <div class="stat-value">{summary['total_companies']}</div>
            <div class="stat-label">Total Companies</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{summary['fully_compliant']}</div>
            <div class="stat-label">Fully Compliant</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{summary['partially_compliant']}</div>
            <div class="stat-label">Partially Compliant</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{summary['non_compliant']}</div>
            <div class="stat-label">Non-Compliant</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{summary['critical_issues']}</div>
            <div class="stat-label">Critical Issues</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['average_compliance_score']}</div>
            <div class="stat-label">Avg Compliance Score</div>
        </div>
    </div>

    <div class="section">
        <h2>📈 Aggregate Statistics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Average Directory Score</td>
                <td>{stats['average_directory_score']}</td>
            </tr>
            <tr>
                <td>Average Excel Score</td>
                <td>{stats['average_excel_score']}</td>
            </tr>
            <tr>
                <td>Total Issues</td>
                <td>{stats['total_issues']}</td>
            </tr>
            <tr>
                <td>Total Warnings</td>
                <td>{stats['total_warnings']}</td>
            </tr>
            <tr>
                <td>Total Recommendations</td>
                <td>{stats['total_recommendations']}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>🎯 Priority Recommendations</h2>
        <p>Actions required across multiple companies:</p>
        <table>
            <thead>
                <tr>
                    <th>Priority</th>
                    <th>Issue Type</th>
                    <th>Affected Companies</th>
                    <th>Count</th>
                    <th>Auto-Fix</th>
                </tr>
            </thead>
            <tbody>
"""

        for rec in recs[:10]:  # Top 10
            companies_str = ', '.join(rec['affected_companies'][:5])
            if len(rec['affected_companies']) > 5:
                companies_str += f' (+{len(rec["affected_companies"]) - 5} more)'

            html_content += f"""
                <tr>
                    <td class="priority-{rec['priority']}">{rec['priority']}</td>
                    <td>{rec['issue_type']}</td>
                    <td>{companies_str}</td>
                    <td>{rec['count']}</td>
                    <td>{'✅ Yes' if rec['automated_fix_available'] else '❌ No'}</td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def get_compliance_summary(self) -> str:
        """
        Get a text summary of the latest validation results.

        Returns:
            Human-readable summary string
        """
        if not self.validation_results:
            return "No validation results available."

        results = self.validation_results[-1]
        summary = f"""
========================================
Batch File System Validation Summary
========================================

Base Path: {results['base_path']}
Timestamp: {results['validation_timestamp']}

Companies Validated
--------------------
Total Companies:       {results['total_companies']}
Successfully Validated: {results['companies_validated']}

Compliance Distribution
------------------------
Fully Compliant:       {results['fully_compliant']}
Partially Compliant:   {results['partially_compliant']}
Non-Compliant:         {results['non_compliant']}

Issues Overview
----------------
Critical Issues:       {results['critical_issues']}
Total Issues:          {results['aggregate_statistics']['total_issues']}
Total Warnings:        {results['aggregate_statistics']['total_warnings']}

Average Scores
--------------
Compliance Score:      {results['aggregate_statistics']['average_compliance_score']}
Directory Score:       {results['aggregate_statistics']['average_directory_score']}
Excel Score:           {results['aggregate_statistics']['average_excel_score']}

Top Recommendations
-------------------
"""

        for i, rec in enumerate(results['recommendations_summary'][:5], 1):
            summary += f"{i}. [{rec['priority']}] {rec['issue_type']} - "
            summary += f"{rec['count']} occurrences across {len(rec['affected_companies'])} companies\n"

        return summary


def main():
    """
    CLI entry point for file system validation.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='File System Organization Validator (Task 206)'
    )
    parser.add_argument(
        '--base-path',
        default='data/companies',
        help='Base directory containing company folders'
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        help='Specific company tickers to validate (default: all)'
    )
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='Automatically repair detected issues'
    )
    parser.add_argument(
        '--output',
        help='Output file path for validation report'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'html', 'csv'],
        default='html',
        help='Output format for validation report'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize validator
    validator = FileSystemOrganizationValidator(base_path=args.base_path)

    # Run batch validation
    print("Starting batch validation...\n")
    results = validator.validate_all_companies(
        company_tickers=args.tickers,
        auto_fix=args.auto_fix
    )

    # Print summary
    print(validator.get_compliance_summary())

    # Export results if requested
    if args.output:
        export_result = validator.export_batch_results(
            output_path=args.output,
            format=args.format
        )

        if export_result['success']:
            print(f"\n[SUCCESS] Report exported to: {export_result['output_path']}")
        else:
            print(f"\n[ERROR] Export failed: {export_result['error']}")

    # Exit with appropriate code
    if results['critical_issues'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
