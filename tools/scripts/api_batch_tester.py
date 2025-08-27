"""
API Batch Tester

This script runs comprehensive batch testing of financial APIs across multiple tickers
and generates detailed analytics about data availability, reliability, and performance.

Usage:
    python api_batch_tester.py --config api_config.json
    python api_batch_tester.py --tickers MSFT,AAPL,GOOGL --quick-test
"""

import json
import sys
import os
import time
import argparse
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
from api_diagnostic_tool import (
    FinancialApiDiagnostic,
    ApiCallResult,
    DataCompleteness,
    ApiErrorType,
)


class ApiBatchTester:
    """Batch tester for multiple tickers across financial APIs"""

    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.diagnostic = FinancialApiDiagnostic(config_file, log_level='INFO')
        self.batch_results = {}
        self.analytics = {}

    def _load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "test_tickers": ["MSFT", "AAPL", "GOOGL", "NVDA", "TSLA"],
            "timeout": 30,
            "rate_limit_delay": 1.0,
            "quick_test": False,
            "max_concurrent": 1,
        }

        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")

        return default_config

    def run_batch_test(self, tickers: List[str] = None, quick_test: bool = False) -> Dict[str, Any]:
        """Run batch testing across multiple tickers"""
        if tickers is None:
            tickers = self.config.get('test_tickers', ['MSFT', 'AAPL'])

        print(f"Starting batch test for {len(tickers)} tickers: {', '.join(tickers)}")
        print(f"Quick test mode: {quick_test}")
        print("-" * 60)

        batch_start_time = time.time()

        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] Testing {ticker}...")

            try:
                ticker_start_time = time.time()

                # Run comprehensive test for this ticker
                results = self.diagnostic.test_all_apis(
                    ticker=ticker, include_statements=not quick_test
                )

                ticker_duration = time.time() - ticker_start_time
                results['test_duration'] = ticker_duration

                self.batch_results[ticker] = results

                print(f"  [OK] {ticker} completed in {ticker_duration:.1f}s")

                # Add delay between tickers to respect rate limits
                if i < len(tickers):
                    delay = self.config.get('rate_limit_delay', 1.0)
                    time.sleep(delay)

            except Exception as e:
                print(f"  [FAIL] {ticker} failed: {e}")
                self.batch_results[ticker] = {'error': str(e), 'test_duration': 0}

        batch_duration = time.time() - batch_start_time
        print(f"\nBatch testing completed in {batch_duration:.1f}s")

        # Generate analytics
        self.analytics = self._generate_batch_analytics()

        return {
            'batch_results': self.batch_results,
            'analytics': self.analytics,
            'batch_duration': batch_duration,
            'tickers_tested': tickers,
            'quick_test': quick_test,
        }

    def _generate_batch_analytics(self) -> Dict[str, Any]:
        """Generate comprehensive analytics from batch results"""
        analytics = {
            'api_reliability': {},
            'field_availability_analysis': {},
            'performance_metrics': {},
            'error_patterns': {},
            'data_quality_analysis': {},
            'ticker_coverage': {},
        }

        # Collect all results
        all_api_results = []
        ticker_success_counts = {}

        for ticker, ticker_results in self.batch_results.items():
            if 'error' in ticker_results:
                continue

            ticker_success_counts[ticker] = {'total': 0, 'successful': 0}

            for api_name, api_results in ticker_results.items():
                if api_name in ['summary', 'test_duration']:
                    continue

                if not api_results:
                    continue

                for result in api_results:
                    result.ticker = ticker  # Add ticker info
                    all_api_results.append(result)

                    ticker_success_counts[ticker]['total'] += 1
                    if result.success:
                        ticker_success_counts[ticker]['successful'] += 1

        # API Reliability Analysis
        api_stats = {}
        for result in all_api_results:
            api_name = result.api_name
            if api_name not in api_stats:
                api_stats[api_name] = {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'avg_response_time': 0,
                    'endpoints': set(),
                    'errors': [],
                }

            stats = api_stats[api_name]
            stats['total_calls'] += 1
            stats['endpoints'].add(result.endpoint)

            if result.success:
                stats['successful_calls'] += 1
                stats['avg_response_time'] += result.response_time
            else:
                stats['errors'].append(
                    {
                        'ticker': result.ticker,
                        'endpoint': result.endpoint,
                        'error_type': result.error_type.value if result.error_type else 'unknown',
                        'error_message': result.error_message,
                    }
                )

        # Calculate averages and reliability scores
        for api_name, stats in api_stats.items():
            if stats['successful_calls'] > 0:
                stats['avg_response_time'] /= stats['successful_calls']

            stats['success_rate'] = (
                stats['successful_calls'] / stats['total_calls'] if stats['total_calls'] > 0 else 0
            )
            stats['endpoints'] = list(stats['endpoints'])

            analytics['api_reliability'][api_name] = stats

        # Field Availability Analysis
        field_availability = {}

        for result in all_api_results:
            if not result.success or not result.data_received:
                continue

            for field_name, value in result.data_received.items():
                if field_name not in field_availability:
                    field_availability[field_name] = {
                        'total_occurrences': 0,
                        'non_null_occurrences': 0,
                        'apis_providing': set(),
                        'sample_values': [],
                    }

                field_info = field_availability[field_name]
                field_info['total_occurrences'] += 1
                field_info['apis_providing'].add(result.api_name)

                if value is not None and value != '' and str(value).lower() != 'none':
                    field_info['non_null_occurrences'] += 1
                    if len(field_info['sample_values']) < 3:
                        field_info['sample_values'].append(str(value)[:50])

        # Calculate field availability percentages
        for field_name, field_info in field_availability.items():
            field_info['availability_percentage'] = (
                field_info['non_null_occurrences'] / field_info['total_occurrences']
                if field_info['total_occurrences'] > 0
                else 0
            ) * 100
            field_info['apis_providing'] = list(field_info['apis_providing'])

        analytics['field_availability_analysis'] = field_availability

        # Performance Metrics
        response_times_by_api = {}
        for result in all_api_results:
            if result.success and result.response_time > 0:
                api_name = result.api_name
                if api_name not in response_times_by_api:
                    response_times_by_api[api_name] = []
                response_times_by_api[api_name].append(result.response_time)

        for api_name, times in response_times_by_api.items():
            analytics['performance_metrics'][api_name] = {
                'avg_response_time': sum(times) / len(times),
                'min_response_time': min(times),
                'max_response_time': max(times),
                'total_measurements': len(times),
            }

        # Error Pattern Analysis
        error_patterns = {}
        for result in all_api_results:
            if not result.success and result.error_type:
                error_key = f"{result.api_name}_{result.error_type.value}"
                if error_key not in error_patterns:
                    error_patterns[error_key] = {
                        'count': 0,
                        'affected_tickers': set(),
                        'affected_endpoints': set(),
                        'sample_messages': [],
                    }

                pattern = error_patterns[error_key]
                pattern['count'] += 1
                pattern['affected_tickers'].add(result.ticker)
                pattern['affected_endpoints'].add(result.endpoint)

                if len(pattern['sample_messages']) < 3 and result.error_message:
                    pattern['sample_messages'].append(result.error_message[:100])

        # Convert sets to lists for JSON serialization
        for pattern in error_patterns.values():
            pattern['affected_tickers'] = list(pattern['affected_tickers'])
            pattern['affected_endpoints'] = list(pattern['affected_endpoints'])

        analytics['error_patterns'] = error_patterns

        # Data Quality Analysis
        quality_analysis = {}
        completeness_by_api = {}

        for result in all_api_results:
            if result.success and result.data_completeness:
                api_name = result.api_name
                if api_name not in completeness_by_api:
                    completeness_by_api[api_name] = {
                        'complete': 0,
                        'partial': 0,
                        'minimal': 0,
                        'empty': 0,
                        'total': 0,
                    }

                completeness_by_api[api_name][result.data_completeness.value] += 1
                completeness_by_api[api_name]['total'] += 1

        analytics['data_quality_analysis'] = completeness_by_api

        # Ticker Coverage Analysis
        for ticker, counts in ticker_success_counts.items():
            success_rate = counts['successful'] / counts['total'] if counts['total'] > 0 else 0
            analytics['ticker_coverage'][ticker] = {
                'total_api_calls': counts['total'],
                'successful_calls': counts['successful'],
                'success_rate': success_rate,
                'coverage_score': success_rate,  # Could be enhanced with weighted scoring
            }

        return analytics

    def generate_excel_report(self, output_file: str = None) -> str:
        """Generate comprehensive Excel report with multiple sheets"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'api_batch_analysis_{timestamp}.xlsx'

        print(f"Generating Excel report: {output_file}")

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

            # Summary Sheet
            self._create_summary_sheet(writer)

            # API Reliability Sheet
            self._create_api_reliability_sheet(writer)

            # Field Availability Sheet
            self._create_field_availability_sheet(writer)

            # Performance Metrics Sheet
            self._create_performance_sheet(writer)

            # Error Analysis Sheet
            self._create_error_analysis_sheet(writer)

            # Raw Results Sheet
            self._create_raw_results_sheet(writer)

        print(f"Excel report saved to: {output_file}")
        return output_file

    def _create_summary_sheet(self, writer):
        """Create summary overview sheet"""
        analytics = self.analytics

        summary_data = []

        # Overall statistics
        total_tickers = len(
            [t for t in self.batch_results.keys() if 'error' not in self.batch_results[t]]
        )
        total_api_calls = sum(
            stats['total_calls'] for stats in analytics.get('api_reliability', {}).values()
        )
        total_successful_calls = sum(
            stats['successful_calls'] for stats in analytics.get('api_reliability', {}).values()
        )

        summary_data.append(['Metric', 'Value'])
        summary_data.append(['Total Tickers Tested', total_tickers])
        summary_data.append(['Total API Calls', total_api_calls])
        summary_data.append(['Successful API Calls', total_successful_calls])
        summary_data.append(
            [
                'Overall Success Rate',
                (
                    f"{(total_successful_calls/total_api_calls*100):.1f}%"
                    if total_api_calls > 0
                    else "N/A"
                ),
            ]
        )
        summary_data.append([''])

        # API-specific summaries
        summary_data.append(['API Performance Summary', ''])
        for api_name, stats in analytics.get('api_reliability', {}).items():
            summary_data.append(
                [f'{api_name.upper()} Success Rate', f"{stats['success_rate']*100:.1f}%"]
            )
            summary_data.append(
                [f'{api_name.upper()} Avg Response Time', f"{stats['avg_response_time']:.2f}s"]
            )

        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False, header=False)

    def _create_api_reliability_sheet(self, writer):
        """Create API reliability analysis sheet"""
        reliability_data = []

        for api_name, stats in self.analytics.get('api_reliability', {}).items():
            reliability_data.append(
                {
                    'API': api_name.upper(),
                    'Total Calls': stats['total_calls'],
                    'Successful Calls': stats['successful_calls'],
                    'Success Rate (%)': stats['success_rate'] * 100,
                    'Avg Response Time (s)': stats['avg_response_time'],
                    'Endpoints Tested': ', '.join(stats['endpoints']),
                    'Error Count': len(stats['errors']),
                }
            )

        df_reliability = pd.DataFrame(reliability_data)
        df_reliability.to_excel(writer, sheet_name='API Reliability', index=False)

    def _create_field_availability_sheet(self, writer):
        """Create field availability analysis sheet"""
        field_data = []

        for field_name, field_info in self.analytics.get('field_availability_analysis', {}).items():
            field_data.append(
                {
                    'Field Name': field_name,
                    'Availability (%)': field_info['availability_percentage'],
                    'Total Occurrences': field_info['total_occurrences'],
                    'Non-Null Occurrences': field_info['non_null_occurrences'],
                    'APIs Providing': ', '.join(field_info['apis_providing']),
                    'Sample Values': ' | '.join(field_info['sample_values']),
                }
            )

        df_fields = pd.DataFrame(field_data)
        df_fields = df_fields.sort_values('Availability (%)', ascending=False)
        df_fields.to_excel(writer, sheet_name='Field Availability', index=False)

    def _create_performance_sheet(self, writer):
        """Create performance metrics sheet"""
        perf_data = []

        for api_name, metrics in self.analytics.get('performance_metrics', {}).items():
            perf_data.append(
                {
                    'API': api_name.upper(),
                    'Average Response Time (s)': metrics['avg_response_time'],
                    'Min Response Time (s)': metrics['min_response_time'],
                    'Max Response Time (s)': metrics['max_response_time'],
                    'Total Measurements': metrics['total_measurements'],
                }
            )

        df_performance = pd.DataFrame(perf_data)
        df_performance.to_excel(writer, sheet_name='Performance', index=False)

    def _create_error_analysis_sheet(self, writer):
        """Create error analysis sheet"""
        error_data = []

        for error_key, pattern in self.analytics.get('error_patterns', {}).items():
            api_name, error_type = error_key.split('_', 1)
            error_data.append(
                {
                    'API': api_name.upper(),
                    'Error Type': error_type.replace('_', ' ').title(),
                    'Occurrence Count': pattern['count'],
                    'Affected Tickers': ', '.join(pattern['affected_tickers']),
                    'Affected Endpoints': ', '.join(pattern['affected_endpoints']),
                    'Sample Error Messages': ' | '.join(pattern['sample_messages']),
                }
            )

        df_errors = pd.DataFrame(error_data)
        if not df_errors.empty and 'Occurrence Count' in df_errors.columns:
            df_errors = df_errors.sort_values('Occurrence Count', ascending=False)
        df_errors.to_excel(writer, sheet_name='Error Analysis', index=False)

    def _create_raw_results_sheet(self, writer):
        """Create raw results sheet with all test data"""
        raw_data = []

        for ticker, ticker_results in self.batch_results.items():
            if 'error' in ticker_results:
                raw_data.append(
                    {
                        'Ticker': ticker,
                        'API': 'N/A',
                        'Endpoint': 'N/A',
                        'Success': False,
                        'Error': ticker_results['error'],
                        'Response Time (s)': 0,
                        'Data Completeness': 'N/A',
                    }
                )
                continue

            for api_name, api_results in ticker_results.items():
                if api_name in ['summary', 'test_duration']:
                    continue

                if not api_results:
                    continue

                for result in api_results:
                    raw_data.append(
                        {
                            'Ticker': ticker,
                            'API': result.api_name.upper(),
                            'Endpoint': result.endpoint,
                            'Success': result.success,
                            'Response Time (s)': result.response_time,
                            'Status Code': result.status_code or 'N/A',
                            'Data Completeness': (
                                result.data_completeness.value
                                if result.data_completeness
                                else 'N/A'
                            ),
                            'Error Type': result.error_type.value if result.error_type else 'N/A',
                            'Error Message': result.error_message or 'N/A',
                            'Missing Fields Count': (
                                len(result.missing_fields) if result.missing_fields else 0
                            ),
                        }
                    )

        df_raw = pd.DataFrame(raw_data)
        df_raw.to_excel(writer, sheet_name='Raw Results', index=False)

    def generate_markdown_summary(self, output_file: str = None) -> str:
        """Generate markdown summary report"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'api_batch_summary_{timestamp}.md'

        lines = []
        lines.append("# Financial API Batch Testing Summary")
        lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Executive Summary
        analytics = self.analytics
        total_tickers = len(
            [t for t in self.batch_results.keys() if 'error' not in self.batch_results[t]]
        )

        lines.append("## Executive Summary")
        lines.append(f"- **Tickers tested**: {total_tickers}")

        for api_name, stats in analytics.get('api_reliability', {}).items():
            lines.append(
                f"- **{api_name.upper()}**: {stats['success_rate']*100:.1f}% success rate, {stats['avg_response_time']:.2f}s avg response"
            )

        lines.append("")

        # Top Issues
        lines.append("## Key Findings")

        # Most reliable API
        if analytics.get('api_reliability'):
            best_api = max(analytics['api_reliability'].items(), key=lambda x: x[1]['success_rate'])
            lines.append(
                f"- **Most reliable API**: {best_api[0].upper()} ({best_api[1]['success_rate']*100:.1f}% success rate)"
            )

        # Most common errors
        if analytics.get('error_patterns'):
            top_error = max(analytics['error_patterns'].items(), key=lambda x: x[1]['count'])
            lines.append(
                f"- **Most common issue**: {top_error[0]} ({top_error[1]['count']} occurrences)"
            )

        # Field availability insights
        if analytics.get('field_availability_analysis'):
            high_availability_fields = [
                field
                for field, info in analytics['field_availability_analysis'].items()
                if info['availability_percentage'] > 90
            ]
            lines.append(
                f"- **Highly available fields**: {len(high_availability_fields)} fields with >90% availability"
            )

        lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("1. **Primary API**: Use the most reliable API as primary data source")
        lines.append("2. **Fallback Strategy**: Implement automatic fallback for failed requests")
        lines.append(
            "3. **Field Validation**: Focus on high-availability fields for core calculations"
        )
        lines.append("4. **Error Handling**: Implement specific handling for common error patterns")
        lines.append("")

        content = "\n".join(lines)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Markdown summary saved to: {output_file}")
        return output_file


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Financial API Batch Tester')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--tickers', '-t', help='Comma-separated list of tickers to test')
    parser.add_argument(
        '--quick-test', action='store_true', help='Run quick test (skip financial statements)'
    )
    parser.add_argument('--output-excel', help='Output Excel file path')
    parser.add_argument('--output-markdown', help='Output Markdown file path')
    parser.add_argument(
        '--sample-run', action='store_true', help='Run with sample tickers for testing'
    )

    args = parser.parse_args()

    # Initialize batch tester
    batch_tester = ApiBatchTester(config_file=args.config)

    # Determine tickers to test
    if args.sample_run:
        tickers = ['MSFT', 'AAPL']
        print("Running sample test with MSFT and AAPL")
    elif args.tickers:
        tickers = [ticker.strip().upper() for ticker in args.tickers.split(',')]
    else:
        tickers = batch_tester.config.get('test_tickers', ['MSFT'])

    # Run batch test
    results = batch_tester.run_batch_test(tickers=tickers, quick_test=args.quick_test)

    # Generate reports
    if args.output_excel:
        batch_tester.generate_excel_report(args.output_excel)
    else:
        batch_tester.generate_excel_report()

    if args.output_markdown:
        batch_tester.generate_markdown_summary(args.output_markdown)
    else:
        batch_tester.generate_markdown_summary()

    print("\nBatch testing completed successfully!")


if __name__ == "__main__":
    main()
