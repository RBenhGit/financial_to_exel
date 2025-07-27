"""
Example Usage of Alternative Financial Data Sources

This script demonstrates how to use the new alternative data sources
functionality with practical examples.
"""

import sys
import os
import logging
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def example_basic_usage():
    """Example 1: Basic usage with backward compatibility"""
    print("Example 1: Basic Market Data Fetching")
    print("-" * 40)

    from enhanced_data_manager import create_enhanced_data_manager

    # Create enhanced data manager (drop-in replacement for CentralizedDataManager)
    manager = create_enhanced_data_manager()

    # Fetch market data for a sample ticker
    ticker = "AAPL"
    print(f"Fetching market data for {ticker}...")

    data = manager.fetch_market_data(ticker)

    if data:
        print(f"Success! Data retrieved:")
        print(f"  Ticker: {data.get('ticker', 'N/A')}")
        print(f"  Company: {data.get('company_name', 'N/A')}")
        print(f"  Current Price: ${data.get('current_price', 0):.2f}")
        print(f"  Market Cap: ${data.get('market_cap', 0):.1f}M")
        print(f"  Data Source: {data.get('data_source', 'Unknown')}")
        print(f"  Last Updated: {data.get('last_updated', 'N/A')}")

        # Show additional fields if available
        additional_fields = ['pe_ratio', 'beta', 'dividend_yield', 'sector']
        for field in additional_fields:
            if field in data and data[field] is not None:
                print(f"  {field.replace('_', ' ').title()}: {data[field]}")
    else:
        print(f"Failed to fetch data for {ticker}")

    # Show available data sources
    sources_info = manager.get_available_data_sources()
    print(
        f"\nAvailable Data Sources: {sources_info['active_sources']}/{sources_info['total_sources']}"
    )

    for source_name, source_info in sources_info['enhanced_sources'].items():
        status = "ACTIVE" if source_info['enabled'] else "INACTIVE"
        has_creds = (
            "with credentials" if source_info.get('has_credentials', False) else "no credentials"
        )
        print(f"  {source_name.replace('_', ' ').title()}: {status} ({has_creds})")

    manager.cleanup()
    print()


def example_multiple_tickers():
    """Example 2: Fetching data for multiple tickers"""
    print("Example 2: Multiple Tickers")
    print("-" * 30)

    from enhanced_data_manager import create_enhanced_data_manager

    manager = create_enhanced_data_manager()

    # Test with multiple tickers
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

    print(f"Fetching data for {len(tickers)} tickers...")
    results = {}

    for ticker in tickers:
        print(f"  Processing {ticker}...", end=" ")
        start_time = time.time()

        data = manager.fetch_market_data(ticker)

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        if data:
            results[ticker] = {
                'price': data.get('current_price', 0),
                'market_cap': data.get('market_cap', 0),
                'source': data.get('data_source', 'Unknown'),
                'response_time': response_time,
            }
            print(f"OK ({response_time:.0f}ms)")
        else:
            results[ticker] = None
            print(f"FAILED ({response_time:.0f}ms)")

    # Display results
    print(f"\nResults Summary:")
    print(f"{'Ticker':<8} {'Price':<10} {'Market Cap':<12} {'Source':<20} {'Time':<8}")
    print("-" * 65)

    for ticker, result in results.items():
        if result:
            price_str = f"${result['price']:.2f}"
            mcap_str = f"${result['market_cap']:.1f}M"
            source_str = result['source'][:18]
            time_str = f"{result['response_time']:.0f}ms"
            print(f"{ticker:<8} {price_str:<10} {mcap_str:<12} {source_str:<20} {time_str:<8}")
        else:
            print(f"{ticker:<8} {'FAILED':<10} {'-':<12} {'-':<20} {'-':<8}")

    manager.cleanup()
    print()


def example_source_testing():
    """Example 3: Testing individual data sources"""
    print("Example 3: Data Source Testing")
    print("-" * 32)

    from enhanced_data_manager import create_enhanced_data_manager

    manager = create_enhanced_data_manager()

    # Test all sources with a sample ticker
    test_ticker = "AAPL"
    print(f"Testing all data sources with {test_ticker}...")

    test_results = manager.test_all_sources(test_ticker)

    print(f"\nTest Results:")
    print(f"{'Source':<20} {'Status':<8} {'Time':<10} {'Quality':<8} {'API Calls':<10}")
    print("-" * 65)

    for source_name, result in test_results['sources'].items():
        status = "PASS" if result.get('success', False) else "FAIL"
        response_time = f"{result.get('response_time', 0):.2f}s"
        quality = f"{result.get('quality_score', 0):.2f}" if result.get('quality_score') else "N/A"
        api_calls = str(result.get('api_calls_used', 0)) if result.get('api_calls_used') else "N/A"

        source_display = source_name.replace('_', ' ').title()[:18]
        print(f"{source_display:<20} {status:<8} {response_time:<10} {quality:<8} {api_calls:<10}")

        if not result.get('success', False) and result.get('error'):
            error_msg = (
                result['error'][:50] + "..." if len(result['error']) > 50 else result['error']
            )
            print(f"  Error: {error_msg}")

    # Show summary
    summary = test_results['summary']
    print(f"\nSummary:")
    print(f"  Total Sources: {summary['total_sources']}")
    print(f"  Successful: {summary['successful_sources']}")
    print(f"  Success Rate: {summary['success_rate']:.1%}")

    if summary.get('best_source'):
        print(f"  Best Quality: {summary['best_source'].replace('_', ' ').title()}")
    if summary.get('fastest_source'):
        print(f"  Fastest: {summary['fastest_source'].replace('_', ' ').title()}")

    manager.cleanup()
    print()


def example_usage_monitoring():
    """Example 4: Usage monitoring and cost tracking"""
    print("Example 4: Usage Monitoring")
    print("-" * 28)

    from enhanced_data_manager import create_enhanced_data_manager

    manager = create_enhanced_data_manager()

    # Make a few requests to generate usage data
    print("Generating sample usage data...")
    sample_tickers = ["AAPL", "MSFT", "GOOGL"]

    for ticker in sample_tickers:
        manager.fetch_market_data(ticker)
        time.sleep(0.1)  # Small delay

    # Get usage report
    usage_report = manager.get_enhanced_usage_report()

    if 'enhanced_adapter' in usage_report:
        enhanced_stats = usage_report['enhanced_adapter']

        print(f"\nOverall Usage Statistics:")
        print(f"  Total API Calls: {enhanced_stats.get('total_calls', 0)}")
        print(f"  Monthly Calls: {enhanced_stats.get('monthly_calls', 0)}")
        print(f"  Total Cost: ${enhanced_stats.get('total_cost', 0):.4f}")
        print(f"  Monthly Cost: ${enhanced_stats.get('monthly_cost', 0):.4f}")

        # Show per-source statistics
        sources_stats = enhanced_stats.get('sources', {})
        active_sources = {k: v for k, v in sources_stats.items() if v.get('total_calls', 0) > 0}

        if active_sources:
            print(f"\nPer-Source Statistics:")
            print(f"{'Source':<20} {'Calls':<8} {'Success':<8} {'Cost':<10} {'Avg Time':<10}")
            print("-" * 65)

            for source_name, stats in active_sources.items():
                calls = stats.get('total_calls', 0)
                success_rate = f"{stats.get('success_rate', 0):.1%}"
                cost = f"${stats.get('total_cost', 0):.4f}"
                avg_time = f"{stats.get('average_response_time', 0):.2f}s"

                source_display = source_name.replace('_', ' ').title()[:18]
                print(
                    f"{source_display:<20} {calls:<8} {success_rate:<8} {cost:<10} {avg_time:<10}"
                )
        else:
            print("\nNo active source usage found.")

    # Show cache statistics
    if 'legacy_fallback' in usage_report and 'cache_stats' in usage_report['legacy_fallback']:
        cache_stats = usage_report['legacy_fallback']['cache_stats']
        print(f"\nCache Statistics:")
        print(f"  Total Entries: {cache_stats.get('total_entries', 0)}")
        print(f"  Active Entries: {cache_stats.get('active_entries', 0)}")
        print(f"  Expired Entries: {cache_stats.get('expired_entries', 0)}")

    manager.cleanup()
    print()


def example_configuration():
    """Example 5: Configuration management"""
    print("Example 5: Configuration Management")
    print("-" * 35)

    from enhanced_data_manager import create_enhanced_data_manager

    manager = create_enhanced_data_manager()

    # Show current configuration
    sources_info = manager.get_available_data_sources()

    print("Current Data Source Configuration:")
    print(f"{'Source':<25} {'Status':<10} {'Priority':<10} {'Credentials':<12}")
    print("-" * 70)

    for source_name, source_info in sources_info['enhanced_sources'].items():
        status = "ENABLED" if source_info['enabled'] else "DISABLED"
        priority = str(source_info['priority'])
        has_creds = "YES" if source_info.get('has_credentials', False) else "NO"

        source_display = source_name.replace('_', ' ').title()
        print(f"{source_display:<25} {status:<10} {priority:<10} {has_creds:<12}")

    print(f"\nFallback Hierarchy:")
    enabled_sources = [
        (name, info) for name, info in sources_info['enhanced_sources'].items() if info['enabled']
    ]

    # Sort by priority
    enabled_sources.sort(key=lambda x: x[1]['priority'])

    for i, (source_name, source_info) in enumerate(enabled_sources, 1):
        source_display = source_name.replace('_', ' ').title()
        print(f"  {i}. {source_display}")

    # Example of how to configure a source (without actually doing it)
    print(f"\nTo configure a new data source:")
    print(f"  manager.configure_enhanced_source('alpha_vantage', 'your_api_key_here')")
    print(f"  manager.configure_enhanced_source('fmp', 'your_fmp_key_here')")
    print(f"  manager.configure_enhanced_source('polygon', 'your_polygon_key_here')")

    manager.cleanup()
    print()


def main():
    """Run all examples"""
    print("Alternative Financial Data Sources - Usage Examples")
    print("=" * 55)
    print()

    # Configure logging to reduce noise during examples
    logging.basicConfig(level=logging.WARNING)

    examples = [
        example_basic_usage,
        example_multiple_tickers,
        example_source_testing,
        example_usage_monitoring,
        example_configuration,
    ]

    try:
        for example_func in examples:
            example_func()

        print("All examples completed successfully!")
        print("\nTo get started with your own implementation:")
        print("1. Import: from enhanced_data_manager import create_enhanced_data_manager")
        print("2. Create: manager = create_enhanced_data_manager()")
        print("3. Use: data = manager.fetch_market_data('AAPL')")
        print("4. Configure API keys for better reliability (optional)")
        print("\nSee ALTERNATIVE_DATA_SOURCES_GUIDE.md for detailed documentation.")

    except KeyboardInterrupt:
        print("\nExamples interrupted by user.")
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
