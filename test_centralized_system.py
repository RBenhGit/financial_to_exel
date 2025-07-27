# Windows FCF Analysis - Centralized System Test
"""
Test script for the centralized data collection and processing system.
"""

import sys
import os
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from centralized_data_manager import CentralizedDataManager
from centralized_data_processor import CentralizedDataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_centralized_system():
    """Test the centralized data collection and processing system"""

    print("=" * 60)
    print("TESTING CENTRALIZED DATA COLLECTION AND PROCESSING SYSTEM")
    print("=" * 60)

    # Initialize the system
    base_path = Path(__file__).parent
    print(f"\nInitializing system with base path: {base_path}")

    # Create data manager
    data_manager = CentralizedDataManager(str(base_path))

    # Create data processor
    data_processor = CentralizedDataProcessor(data_manager)

    # Test companies
    # Use available company directories for testing
    import os

    available_companies = [
        d for d in os.listdir('.') if os.path.isdir(d) and len(d) <= 5 and d.isupper()
    ]
    test_companies = (
        available_companies[:4]
        if len(available_companies) >= 4
        else ['TEST1', 'TEST2', 'TEST3', 'TEST4']
    )

    for company in test_companies:
        print(f"\n{'='*50}")
        print(f"TESTING COMPANY: {company}")
        print(f"{'='*50}")

        # Check if company folder exists
        company_path = base_path / company
        if not company_path.exists():
            print(f"❌ Company folder {company} not found, skipping...")
            continue

        # Test 1: Load Excel data
        print(f"\n1. Testing Excel data loading for {company}...")
        try:
            financial_data = data_manager.load_excel_data(company)
            print(f"✅ Successfully loaded {len(financial_data)} datasets")
            for key, df in financial_data.items():
                print(f"   - {key}: {df.shape[0]} rows, {df.shape[1]} columns")
        except Exception as e:
            print(f"❌ Error loading Excel data: {e}")
            continue

        # Test 2: Fetch market data
        print(f"\n2. Testing market data fetching for {company}...")
        try:
            market_data = data_manager.fetch_market_data(company)
            if market_data:
                print(f"✅ Successfully fetched market data")
                print(f"   - Price: ${market_data['current_price']:.2f}")
                print(f"   - Market Cap: ${market_data['market_cap']:.0f}M")
                print(f"   - Shares Outstanding: {market_data['shares_outstanding']/1000000:.0f}M")
            else:
                print(f"⚠️ Market data fetch failed (likely rate limited)")
        except Exception as e:
            print(f"❌ Error fetching market data: {e}")

        # Test 3: Extract financial metrics
        print(f"\n3. Testing financial metrics extraction for {company}...")
        try:
            metrics_result = data_processor.extract_financial_metrics(company)
            if metrics_result.success:
                print(f"✅ Successfully extracted financial metrics")
                metrics = metrics_result.data
                print(f"   - Years processed: {len(metrics.years)}")
                print(f"   - EBIT values: {len(metrics.ebit)}")
                print(f"   - Net Income values: {len(metrics.net_income)}")
                if metrics_result.warnings:
                    print(f"   - Warnings: {len(metrics_result.warnings)}")
            else:
                print(f"❌ Financial metrics extraction failed")
                for error in metrics_result.errors:
                    print(f"     Error: {error}")
        except Exception as e:
            print(f"❌ Error extracting financial metrics: {e}")
            continue

        # Test 4: Calculate FCF
        print(f"\n4. Testing FCF calculations for {company}...")
        try:
            fcf_result = data_processor.calculate_fcf(company)
            if fcf_result.success:
                print(f"✅ Successfully calculated FCF")
                fcf_data = fcf_result.data
                print(f"   - FCFF: {len(fcf_data.fcff)} years, latest: ${fcf_data.fcff[-1]:.0f}M")
                print(f"   - FCFE: {len(fcf_data.fcfe)} years, latest: ${fcf_data.fcfe[-1]:.0f}M")
                print(f"   - LFCF: {len(fcf_data.lfcf)} years, latest: ${fcf_data.lfcf[-1]:.0f}M")
                print(f"   - Growth rates calculated: {len(fcf_data.growth_rates)} types")
            else:
                print(f"❌ FCF calculation failed")
                for error in fcf_result.errors:
                    print(f"     Error: {error}")
        except Exception as e:
            print(f"❌ Error calculating FCF: {e}")

        # Test 5: Test caching
        print(f"\n5. Testing caching for {company}...")
        try:
            # Second call should use cache
            start_time = time.time()
            fcf_result_cached = data_processor.calculate_fcf(company)
            end_time = time.time()

            if fcf_result_cached.success:
                print(f"✅ Cache test successful (took {end_time - start_time:.3f}s)")
            else:
                print(f"❌ Cache test failed")
        except Exception as e:
            print(f"❌ Error testing cache: {e}")

        # Break after first successful test to avoid rate limiting
        print(f"\n✅ Testing complete for {company}")
        break

    # Test 6: System statistics
    print(f"\n{'='*50}")
    print("SYSTEM STATISTICS")
    print(f"{'='*50}")

    try:
        # Data manager stats
        cache_stats = data_manager.get_cache_stats()
        print(f"\nData Manager Cache Stats:")
        print(f"  - Total entries: {cache_stats['total_entries']}")
        print(f"  - Active entries: {cache_stats['active_entries']}")
        print(f"  - Expired entries: {cache_stats['expired_entries']}")
        print(f"  - Source breakdown: {cache_stats['source_breakdown']}")

        # Data processor stats
        processing_stats = data_processor.get_processing_statistics()
        print(f"\nData Processor Stats:")
        print(
            f"  - Supported metrics: {len(processing_stats['processing_stats']['supported_metrics'])}"
        )
        print(f"  - FCF types: {processing_stats['processing_stats']['fcf_types']}")
        print(
            f"  - Growth rate periods: {processing_stats['processing_stats']['growth_rate_periods']}"
        )

    except Exception as e:
        print(f"❌ Error getting system statistics: {e}")

    print(f"\n{'='*60}")
    print("CENTRALIZED SYSTEM TEST COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    import time

    test_centralized_system()
