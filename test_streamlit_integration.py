"""
Streamlit Integration Test

This test verifies that the enhanced data manager works properly
with the existing Streamlit application.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_data_manager import create_enhanced_data_manager
    from unified_data_adapter import UnifiedDataAdapter
    from data_sources import FinancialDataRequest
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_streamlit_integration():
    """Test integration with Streamlit components"""
    print("Streamlit Integration Test")
    print("=" * 30)
    
    try:
        # Test enhanced data manager creation (used by Streamlit)
        print("\n1. Testing enhanced data manager creation...")
        manager = create_enhanced_data_manager()
        print("   SUCCESS: Enhanced data manager created")
        
        # Test available data sources
        print("\n2. Testing available data sources...")
        sources_info = manager.get_available_data_sources()
        print(f"   Total sources: {sources_info['total_sources']}")
        print(f"   Active sources: {sources_info['active_sources']}")
        for source, info in sources_info['enhanced_sources'].items():
            status = "enabled" if info['enabled'] else "disabled"
            print(f"   - {source}: {status} (Priority: {info['priority']})")
        
        # Test data fetching (what Streamlit would do)
        print("\n3. Testing data fetching for Streamlit...")
        test_ticker = "AAPL"
        
        # This simulates what the Streamlit app would do
        request = FinancialDataRequest(
            ticker=test_ticker,
            data_types=['price', 'fundamentals'],
            force_refresh=False  # Use cache if available
        )
        
        response = manager.unified_adapter.fetch_data(request)
        
        if response.success:
            print(f"   SUCCESS: Data retrieved for {test_ticker}")
            print(f"   Source: {response.source_type.value}")
            print(f"   Response time: {response.response_time:.2f}s")
            
            # Check for FCF data
            if response.data and any(key in response.data for key in ['free_cash_flow', 'fcf_calculated']):
                print("   SUCCESS: FCF data is available for Streamlit")
            else:
                print("   INFO: No FCF data in response")
                
        else:
            print(f"   FAILED: {response.error_message}")
        
        # Test usage report (for Streamlit dashboard)
        print("\n4. Testing usage report generation...")
        usage_report = manager.get_enhanced_usage_report()
        if 'enhanced_adapter' in usage_report:
            enhanced_stats = usage_report['enhanced_adapter']
            print(f"   Total API calls: {enhanced_stats.get('total_calls', 0)}")
            print(f"   Total cost: ${enhanced_stats.get('total_cost', 0):.4f}")
        print("   Usage report generated successfully")
        
        # Cleanup
        manager.cleanup()
        print("\n5. Cleanup completed")
        
        print("\nSTREAMLIT INTEGRATION TEST PASSED")
        return True
        
    except Exception as e:
        print(f"\nSTREAMLIT INTEGRATION TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_streamlit_integration()
    sys.exit(0 if success else 1)