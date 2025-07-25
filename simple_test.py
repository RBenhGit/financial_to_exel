"""
Simple Integration Test for Alternative Data Sources

This script performs basic integration testing without Unicode characters
to verify the alternative data sources implementation works correctly.
"""

import sys
import os
import logging
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test basic imports work"""
    print("Testing imports...")
    
    try:
        from enhanced_data_manager import EnhancedDataManager, create_enhanced_data_manager
        print("  PASS: enhanced_data_manager imports")
    except ImportError as e:
        print(f"  FAIL: enhanced_data_manager import - {e}")
        return False
    
    try:
        from unified_data_adapter import UnifiedDataAdapter
        print("  PASS: unified_data_adapter imports")
    except ImportError as e:
        print(f"  FAIL: unified_data_adapter import - {e}")
        return False
    
    try:
        from data_sources import DataSourceType, FinancialDataRequest
        print("  PASS: data_sources imports")
    except ImportError as e:
        print(f"  FAIL: data_sources import - {e}")
        return False
    
    return True

def test_enhanced_data_manager():
    """Test enhanced data manager creation and basic functionality"""
    print("\nTesting Enhanced Data Manager...")
    
    try:
        from enhanced_data_manager import create_enhanced_data_manager
        
        # Create manager
        manager = create_enhanced_data_manager()
        print("  PASS: EnhancedDataManager creation")
        
        # Test available sources
        sources_info = manager.get_available_data_sources()
        if isinstance(sources_info, dict):
            print(f"  PASS: Found {sources_info.get('total_sources', 0)} data sources")
        else:
            print("  FAIL: Invalid sources info")
            return False
        
        # Test backward compatibility
        if hasattr(manager, 'fetch_market_data'):
            print("  PASS: Backward compatibility maintained")
        else:
            print("  FAIL: Missing backward compatibility")
            return False
        
        # Cleanup
        manager.cleanup()
        print("  PASS: Manager cleanup")
        
        return True
        
    except Exception as e:
        print(f"  FAIL: EnhancedDataManager test - {e}")
        return False

def test_unified_adapter():
    """Test unified data adapter"""
    print("\nTesting Unified Data Adapter...")
    
    try:
        from unified_data_adapter import UnifiedDataAdapter
        from data_sources import FinancialDataRequest
        
        # Create adapter
        adapter = UnifiedDataAdapter()
        print("  PASS: UnifiedDataAdapter creation")
        
        # Test configuration
        configs = adapter.configurations
        if len(configs) > 0:
            print(f"  PASS: Loaded {len(configs)} configurations")
        else:
            print("  FAIL: No configurations loaded")
            return False
        
        # Test request creation
        request = FinancialDataRequest(ticker="AAPL", data_types=['price'])
        print("  PASS: FinancialDataRequest creation")
        
        # Test cache key generation
        cache_key = adapter._generate_cache_key(request)
        if cache_key and len(cache_key) == 32:
            print("  PASS: Cache key generation")
        else:
            print("  FAIL: Invalid cache key")
            return False
        
        # Test usage report
        usage_report = adapter.get_usage_report()
        if isinstance(usage_report, dict):
            print("  PASS: Usage report generation")
        else:
            print("  FAIL: Usage report generation failed")
            return False
        
        # Cleanup
        adapter.cleanup()
        print("  PASS: Adapter cleanup")
        
        return True
        
    except Exception as e:
        print(f"  FAIL: UnifiedDataAdapter test - {e}")
        return False

def main():
    """Run all tests"""
    print("Alternative Data Sources - Integration Test")
    print("=" * 50)
    
    # Configure logging to reduce noise
    logging.basicConfig(level=logging.WARNING)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Enhanced Data Manager", test_enhanced_data_manager),
        ("Unified Data Adapter", test_unified_adapter)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'-' * 20}")
        print(f"TEST: {test_name}")
        print(f"{'-' * 20}")
        
        try:
            if test_func():
                print(f"RESULT: {test_name} PASSED")
                passed += 1
            else:
                print(f"RESULT: {test_name} FAILED")
        except Exception as e:
            print(f"RESULT: {test_name} FAILED - {e}")
    
    print(f"\n{'=' * 50}")
    print(f"FINAL RESULTS")
    print(f"{'=' * 50}")
    print(f"Tests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\nAll tests passed! Alternative data sources implementation is working.")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed. Review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())