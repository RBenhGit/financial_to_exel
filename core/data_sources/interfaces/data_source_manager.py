"""
Data Source Manager Utility

This module provides a command-line and programmatic interface for managing
financial data sources, including configuration, testing, and monitoring.

Features:
- Interactive configuration setup
- Credential validation
- Usage monitoring and reporting
- Data source testing
- Cost management and alerts
"""

import os
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from unified_data_adapter import UnifiedDataAdapter
from data_sources import DataSourceType, FinancialDataRequest

logger = logging.getLogger(__name__)


class DataSourceManager:
    """Manager for configuring and monitoring data sources"""

    def __init__(self, base_path: str = "."):
        """
        Initialize the data source manager.

        Args:
            base_path (str): Base path for configuration and data files
        """
        self.base_path = Path(base_path)
        self.adapter = UnifiedDataAdapter(
            config_file=str(self.base_path / "data_sources_config.json"), base_path=str(base_path)
        )

    def interactive_setup(self):
        """Interactive setup wizard for data sources"""
        print("🔧 Financial Data Sources Configuration")
        print("=" * 50)

        # Configure each API source
        sources_to_configure = [
            (
                DataSourceType.ALPHA_VANTAGE,
                "Alpha Vantage",
                "Free tier: 5 calls/min, 500 calls/month",
            ),
            (
                DataSourceType.FINANCIAL_MODELING_PREP,
                "Financial Modeling Prep",
                "Free tier: 250 calls/month",
            ),
            (DataSourceType.POLYGON, "Polygon.io", "Paid service: High quality, real-time data"),
        ]

        for source_type, name, description in sources_to_configure:
            print(f"\n📊 {name}")
            print(f"   {description}")

            configure = input(f"Configure {name}? (y/n): ").lower().strip()

            if configure == 'y':
                api_key = input(f"Enter {name} API key: ").strip()

                if api_key:
                    print(f"🔍 Validating {name} credentials...")

                    success = self.adapter.configure_source(source_type, api_key)

                    if success:
                        print(f"✅ {name} configured successfully!")

                        # Ask for optional settings
                        if source_type == DataSourceType.POLYGON:
                            cost_per_call = input(
                                "Cost per API call (USD, default 0.003): "
                            ).strip()
                            if cost_per_call:
                                try:
                                    cost = float(cost_per_call)
                                    self.adapter.configure_source(
                                        source_type, api_key, cost_per_call=cost
                                    )
                                except ValueError:
                                    print("Invalid cost value, using default")
                    else:
                        print(f"❌ Failed to configure {name}. Please check your API key.")
                else:
                    print(f"Skipping {name} configuration")
            else:
                print(f"Skipping {name} configuration")

        print(f"\n✅ Configuration complete!")
        self._show_configuration_summary()

    def _show_configuration_summary(self):
        """Show summary of configured sources"""
        print(f"\n📋 Configuration Summary")
        print("-" * 30)

        active_sources = []
        for source_type, config in self.adapter.configurations.items():
            if config.is_enabled:
                if source_type == DataSourceType.EXCEL:
                    active_sources.append(f"✓ Excel Files (Priority: {config.priority.value})")
                else:
                    active_sources.append(
                        f"✓ {source_type.value.replace('_', ' ').title()} (Priority: {config.priority.value})"
                    )

        if active_sources:
            for source in active_sources:
                print(f"  {source}")
        else:
            print("  No data sources configured")

        print(
            f"\nFallback order: {' → '.join([s.split('(')[0].strip()[2:] for s in active_sources])}"
        )

    def test_sources(self, ticker: str = "AAPL") -> Dict[str, Any]:
        """Test all configured data sources"""
        print(f"\n🧪 Testing Data Sources with {ticker}")
        print("=" * 40)

        request = FinancialDataRequest(
            ticker=ticker, data_types=['price', 'fundamentals'], force_refresh=True
        )

        results = {}

        # Test each source individually
        for source_type, provider in self.adapter.providers.items():
            print(f"\n📡 Testing {source_type.value.replace('_', ' ').title()}...")

            try:
                response = provider.fetch_data(request)

                if response.success:
                    print(f"  ✅ Success! Response time: {response.response_time:.2f}s")
                    if response.quality_metrics:
                        print(f"  📊 Quality score: {response.quality_metrics.overall_score:.2f}")
                    if response.api_calls_used:
                        print(f"  📞 API calls used: {response.api_calls_used}")
                    if response.cost_incurred:
                        print(f"  💰 Cost: ${response.cost_incurred:.4f}")
                else:
                    print(f"  ❌ Failed: {response.error_message}")

                results[source_type.value] = {
                    'success': response.success,
                    'response_time': response.response_time,
                    'quality_score': (
                        response.quality_metrics.overall_score if response.quality_metrics else 0
                    ),
                    'error': response.error_message if not response.success else None,
                }

            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                results[source_type.value] = {'success': False, 'error': str(e)}

        # Test unified adapter (with fallback)
        print(f"\n🔄 Testing Unified Adapter (with fallback)...")
        try:
            response = self.adapter.fetch_data(request)

            if response.success:
                print(
                    f"  ✅ Success from {response.source_type.value if response.source_type else 'unknown'}!"
                )
                print(
                    f"  📊 Quality score: {response.quality_metrics.overall_score if response.quality_metrics else 'N/A'}"
                )
                print(f"  📞 Cache hit: {response.cache_hit}")
            else:
                print(f"  ❌ All sources failed: {response.error_message}")

            results['unified_adapter'] = {
                'success': response.success,
                'source_used': response.source_type.value if response.source_type else None,
                'cache_hit': response.cache_hit,
                'error': response.error_message if not response.success else None,
            }

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results['unified_adapter'] = {'success': False, 'error': str(e)}

        return results

    def show_usage_report(self):
        """Display usage statistics and costs"""
        report = self.adapter.get_usage_report()

        print(f"\n📊 Usage Report")
        print("=" * 30)
        print(f"Total API Calls: {report['total_calls']}")
        print(f"Total Cost: ${report['total_cost']:.4f}")
        print(f"Monthly Calls: {report['monthly_calls']}")
        print(f"Monthly Cost: ${report['monthly_cost']:.4f}")

        print(f"\n📋 By Source:")
        print("-" * 20)

        for source_name, stats in report['sources'].items():
            if stats['total_calls'] > 0:
                print(f"\n{source_name.replace('_', ' ').title()}:")
                print(
                    f"  Calls: {stats['total_calls']} (Success: {stats['successful_calls']}, Failed: {stats['failed_calls']})"
                )
                print(f"  Success Rate: {stats['success_rate']:.1%}")
                print(f"  Cost: ${stats['total_cost']:.4f}")
                print(f"  Avg Response: {stats['average_response_time']:.2f}s")
                if stats['monthly_limit']:
                    print(
                        f"  Monthly Usage: {stats['monthly_calls']}/{stats['monthly_limit']} ({stats['monthly_calls']/stats['monthly_limit']:.1%})"
                    )
                if stats['last_used']:
                    print(f"  Last Used: {stats['last_used']}")

        print(f"\n💾 Cache Statistics:")
        print(f"  Total Entries: {report['cache_stats']['total_entries']}")
        print(f"  Expired Entries: {report['cache_stats']['expired_entries']}")

    def check_limits(self):
        """Check usage limits and show warnings"""
        report = self.adapter.get_usage_report()

        warnings = []

        for source_name, stats in report['sources'].items():
            if stats['monthly_limit']:
                usage_percent = stats['monthly_calls'] / stats['monthly_limit']

                if usage_percent >= 0.9:
                    warnings.append(f"⚠️  {source_name}: {usage_percent:.1%} of monthly limit used")
                elif usage_percent >= 0.7:
                    warnings.append(f"📊 {source_name}: {usage_percent:.1%} of monthly limit used")

        if warnings:
            print(f"\n⚠️  Usage Warnings:")
            for warning in warnings:
                print(f"  {warning}")
        else:
            print(f"\n✅ All sources within limits")

        return warnings

    def cleanup_cache(self):
        """Clean up expired cache entries"""
        cache_count_before = len(self.adapter.cache)

        # Remove expired entries
        expired_keys = [key for key, entry in self.adapter.cache.items() if entry.is_expired()]
        for key in expired_keys:
            del self.adapter.cache[key]

        removed_count = len(expired_keys)
        cache_count_after = len(self.adapter.cache)

        print(f"🧹 Cache cleanup complete:")
        print(f"  Removed {removed_count} expired entries")
        print(f"  Remaining entries: {cache_count_after}")

        # Save updated cache
        self.adapter._save_cache()

        return removed_count

    def export_configuration(self, output_file: Optional[str] = None):
        """Export current configuration to file"""
        if not output_file:
            output_file = f"data_sources_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            # Get current configuration
            config_data = {
                'configuration': {},
                'usage_stats': self.adapter.get_usage_report(),
                'export_timestamp': datetime.now().isoformat(),
                'version': '1.0',
            }

            # Export configurations (without sensitive API keys)
            for source_type, config in self.adapter.configurations.items():
                config_info = {
                    'priority': config.priority.value,
                    'is_enabled': config.is_enabled,
                    'quality_threshold': config.quality_threshold,
                    'cache_ttl_hours': config.cache_ttl_hours,
                    'has_credentials': config.credentials is not None
                    and bool(config.credentials.api_key),
                }

                if config.credentials:
                    config_info['credentials_config'] = {
                        'rate_limit_calls': config.credentials.rate_limit_calls,
                        'rate_limit_period': config.credentials.rate_limit_period,
                        'timeout': config.credentials.timeout,
                        'cost_per_call': config.credentials.cost_per_call,
                        'monthly_limit': config.credentials.monthly_limit,
                        'is_active': config.credentials.is_active,
                    }

                config_data['configuration'][source_type.value] = config_info

            with open(output_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            print(f"✅ Configuration exported to {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ Export failed: {e}")
            return None


def main():
    """Command-line interface for data source management"""
    parser = argparse.ArgumentParser(description="Financial Data Sources Manager")
    parser.add_argument('--base-path', default='.', help='Base path for configuration files')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Interactive setup wizard')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test data sources')
    test_parser.add_argument('--ticker', default='AAPL', help='Ticker symbol to test with')

    # Report command
    report_parser = subparsers.add_parser('report', help='Show usage report')

    # Limits command
    limits_parser = subparsers.add_parser('limits', help='Check usage limits')

    # Cache command
    cache_parser = subparsers.add_parser('cache', help='Cache management')
    cache_parser.add_argument('--cleanup', action='store_true', help='Clean up expired cache')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export configuration')
    export_parser.add_argument('--output', help='Output file path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        manager = DataSourceManager(args.base_path)

        if args.command == 'setup':
            manager.interactive_setup()

        elif args.command == 'test':
            manager.test_sources(args.ticker)

        elif args.command == 'report':
            manager.show_usage_report()

        elif args.command == 'limits':
            manager.check_limits()

        elif args.command == 'cache':
            if args.cleanup:
                manager.cleanup_cache()
            else:
                report = manager.adapter.get_usage_report()
                print(f"Cache entries: {report['cache_stats']['total_entries']}")
                print(f"Expired entries: {report['cache_stats']['expired_entries']}")

        elif args.command == 'export':
            manager.export_configuration(args.output)

        # Cleanup
        manager.adapter.cleanup()

    except KeyboardInterrupt:
        print(f"\n🛑 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Application error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
