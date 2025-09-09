"""
Industry Data Service Integration Example
=========================================

This script demonstrates how to integrate the new IndustryDataService
with the existing P/B valuation system to provide dynamic industry benchmarks
instead of static hardcoded values.

Usage:
    python industry_data_integration_example.py AAPL
"""

import sys
import logging
from pathlib import Path

# Add core modules to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the new industry data service
from core.data_sources.industry_data_service import IndustryDataService

# Import existing financial calculation components
try:
    from core.analysis.engines.financial_calculations import FinancialCalculator
    FINANCIAL_CALC_AVAILABLE = True
except ImportError:
    logger.warning("FinancialCalculator not available - using mock data")
    FINANCIAL_CALC_AVAILABLE = False


def demonstrate_industry_data_service(ticker: str = "AAPL"):
    """
    Demonstrate the industry data service functionality
    
    Args:
        ticker: Stock ticker to analyze
    """
    print(f"\n{'='*60}")
    print(f"INDUSTRY DATA SERVICE DEMONSTRATION")
    print(f"{'='*60}")
    print(f"Ticker: {ticker}")
    print()
    
    # Initialize the industry data service
    industry_service = IndustryDataService(
        cache_dir="data/cache/industry",
        cache_ttl_hours=24
    )
    
    print("1. SECTOR CLASSIFICATION")
    print("-" * 25)
    
    # Get sector classification
    sector_info = industry_service._get_sector_classification(ticker)
    if sector_info:
        print(f"   Company: {sector_info['company_name']}")
        print(f"   Sector: {sector_info['sector']}")
        print(f"   Industry: {sector_info['industry']}")
    else:
        print(f"   ⚠️  Could not determine sector for {ticker}")
        return
        
    print("\n2. PEER COMPANY IDENTIFICATION")
    print("-" * 30)
    
    # Find peer companies
    peer_tickers = industry_service._find_peer_companies(
        sector_info['sector'], 
        sector_info['industry']
    )
    
    print(f"   Found {len(peer_tickers)} potential peers in {sector_info['sector']} sector:")
    for i, peer in enumerate(peer_tickers[:10], 1):  # Show first 10
        print(f"   {i:2d}. {peer}")
    if len(peer_tickers) > 10:
        print(f"   ... and {len(peer_tickers) - 10} more")
        
    print("\n3. INDUSTRY P/B STATISTICS")
    print("-" * 26)
    
    # Get industry statistics
    try:
        statistics = industry_service.get_industry_pb_statistics(ticker)
        
        if statistics:
            print(f"   [SUCCESS] Successfully calculated industry statistics!")
            print(f"   Sector: {statistics.sector}")
            print(f"   Industry: {statistics.industry}")
            print(f"   Peer Count: {statistics.peer_count}")
            print(f"   Data Quality Score: {statistics.data_quality_score:.2f}")
            print()
            print("   P/B RATIO STATISTICS:")
            print(f"   - Median P/B: {statistics.median_pb:.2f}")
            print(f"   - Mean P/B: {statistics.mean_pb:.2f}")
            print(f"   - Range: {statistics.min_pb:.2f} - {statistics.max_pb:.2f}")
            print(f"   - 25th Percentile: {statistics.q1_pb:.2f}")
            print(f"   - 75th Percentile: {statistics.q3_pb:.2f}")
            print(f"   - Standard Deviation: {statistics.std_pb:.2f}")
            print()
            print("   PEER COMPANIES:")
            for i, peer_ticker in enumerate(statistics.peer_tickers[:10], 1):
                print(f"   {i:2d}. {peer_ticker}")
            if len(statistics.peer_tickers) > 10:
                print(f"   ... and {len(statistics.peer_tickers) - 10} more peers")
                
        else:
            print(f"   [WARNING] Could not calculate industry statistics")
            print(f"   Possible reasons:")
            print(f"   - Insufficient peer companies (need minimum 5)")
            print(f"   - API rate limiting or errors")
            print(f"   - Invalid P/B ratio data from peers")
            
    except Exception as e:
        print(f"   [ERROR] Error calculating statistics: {e}")
        
    print("\n4. CACHING INFORMATION")
    print("-" * 21)
    
    # Show cache information
    cache_info = industry_service.get_cache_info()
    print(f"   Cache Directory: {cache_info['cache_dir']}")
    print(f"   Cache TTL: {cache_info['cache_ttl_hours']} hours")
    print(f"   Cached Files: {cache_info['total_cached_files']}")
    
    if cache_info['files']:
        print("   Recent Cache Files:")
        for file_info in cache_info['files'][:5]:  # Show first 5
            print(f"   - {file_info['file']} ({file_info['size_bytes']} bytes)")


def demonstrate_integration_with_pb_valuation(ticker: str = "AAPL"):
    """
    Demonstrate integration with existing P/B valuation system
    
    Args:
        ticker: Stock ticker to analyze
    """
    print(f"\n{'='*60}")
    print(f"P/B VALUATION INTEGRATION EXAMPLE")
    print(f"{'='*60}")
    
    if not FINANCIAL_CALC_AVAILABLE:
        print("[WARNING] FinancialCalculator not available - skipping integration demo")
        return
        
    try:
        # Initialize financial calculator
        calc = FinancialCalculator(ticker)
        
        # Initialize industry service
        industry_service = IndustryDataService()
        
        # Get company's current P/B ratio
        company_pb = getattr(calc, 'pb_ratio', None)
        if not company_pb:
            print(f"[WARNING] Could not get P/B ratio for {ticker}")
            return
            
        # Get industry statistics
        industry_stats = industry_service.get_industry_pb_statistics(ticker)
        
        if industry_stats:
            print(f"VALUATION COMPARISON FOR {ticker}")
            print("-" * 30)
            print(f"Company P/B Ratio: {company_pb:.2f}")
            print(f"Industry Median P/B: {industry_stats.median_pb:.2f}")
            print(f"Industry Range: {industry_stats.min_pb:.2f} - {industry_stats.max_pb:.2f}")
            print()
            
            # Calculate relative position
            if company_pb < industry_stats.q1_pb:
                position = "Undervalued (Below 25th percentile)"
            elif company_pb < industry_stats.median_pb:
                position = "Below Median"
            elif company_pb < industry_stats.q3_pb:
                position = "Above Median"
            else:
                position = "Premium Valuation (Above 75th percentile)"
                
            print(f"Relative Position: {position}")
            
            # Calculate percentile ranking
            percentile = (sum(1 for pb in [industry_stats.min_pb, industry_stats.q1_pb, 
                             industry_stats.median_pb, industry_stats.q3_pb] if pb < company_pb) / 4) * 100
            print(f"Approximate Percentile: {percentile:.0f}%")
            
        else:
            print(f"[ERROR] Could not get industry data for comparison")
            
    except Exception as e:
        print(f"[ERROR] Integration error: {e}")


def main():
    """Main function to run the demonstration"""
    # Get ticker from command line argument
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    
    # Run demonstrations
    demonstrate_industry_data_service(ticker)
    demonstrate_integration_with_pb_valuation(ticker)
    
    print(f"\n{'='*60}")
    print("DEMONSTRATION COMPLETE")
    print(f"{'='*60}")
    print()
    print("Key Benefits of Dynamic Industry Data Service:")
    print("- Replaces static hardcoded industry benchmarks")
    print("- Provides real-time peer comparison data")
    print("- Calculates comprehensive industry statistics")
    print("- Implements intelligent caching for performance")
    print("- Supports multiple data sources with fallback")
    print("- Validates data quality and peer count requirements")
    print()
    print("Integration Points:")
    print("- Replace static industry_benchmarks dict in pb_valuation.py")
    print("- Use industry_stats.median_pb for valuation calculations")
    print("- Display peer_count and data_quality_score to users")
    print("- Show industry position (percentile ranking)")
    print()


if __name__ == "__main__":
    main()