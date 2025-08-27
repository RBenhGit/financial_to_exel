#!/usr/bin/env python3
"""
Test script to verify the new configuration system integration
=============================================================

This script tests:
1. Configuration module imports correctly
2. Constants are accessible
3. Settings load properly
4. Environment detection works
5. API configuration is properly loaded
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_constants_import():
    """Test that constants can be imported and accessed"""
    print("Testing constants import...")
    
    try:
        from config.constants import (
            DEFAULT_NETWORK_TIMEOUT,
            ALPHA_VANTAGE_BASE_URL, 
            FMP_BASE_URL,
            DEFAULT_DISCOUNT_RATE,
            AV_CURRENT_PRICE
        )
        
        print(f"[OK] Constants imported successfully")
        print(f"   DEFAULT_NETWORK_TIMEOUT: {DEFAULT_NETWORK_TIMEOUT}")
        print(f"   ALPHA_VANTAGE_BASE_URL: {ALPHA_VANTAGE_BASE_URL}")
        print(f"   DEFAULT_DISCOUNT_RATE: {DEFAULT_DISCOUNT_RATE}")
        print(f"   AV_CURRENT_PRICE: {AV_CURRENT_PRICE}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Constants import failed: {e}")
        return False

def test_settings_import():
    """Test that settings can be imported and accessed"""
    print("\nTesting settings import...")
    
    try:
        from config.settings import (
            get_settings,
            get_api_config,
            get_cache_config,
            is_development
        )
        
        print(f"[OK] Settings imported successfully")
        
        # Test settings access
        settings = get_settings()
        api_config = get_api_config()
        cache_config = get_cache_config()
        
        print(f"   Environment: {settings.environment.value}")
        print(f"   API timeout: {api_config.network_timeout}")
        print(f"   Cache enabled: {cache_config.enabled}")
        print(f"   Is development: {is_development()}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Settings import failed: {e}")
        return False

def test_legacy_compatibility():
    """Test that legacy config.py functions still work"""
    print("\nTesting legacy compatibility...")
    
    try:
        from config import get_config, get_dcf_config
        
        config = get_config()
        dcf_config = get_dcf_config()
        
        print(f"[OK] Legacy config compatibility works")
        print(f"   DCF discount rate: {dcf_config.default_discount_rate}")
        print(f"   Excel data start column: {config.excel_structure.data_start_column}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Legacy compatibility failed: {e}")
        print("   This is expected if config.py has import issues")
        return False

def test_environment_detection():
    """Test environment detection and switching"""
    print("\nTesting environment detection...")
    
    try:
        from config.settings import get_current_environment, reload_settings
        
        # Test current environment
        current_env = get_current_environment()
        print(f"[OK] Current environment: {current_env}")
        
        # Test environment variable override
        original_env = os.getenv('FINANCIAL_ANALYSIS_ENV')
        os.environ['FINANCIAL_ANALYSIS_ENV'] = 'testing'
        
        reload_settings()
        test_env = get_current_environment()
        print(f"[OK] Environment switched to: {test_env}")
        
        # Restore original environment
        if original_env:
            os.environ['FINANCIAL_ANALYSIS_ENV'] = original_env
        else:
            os.environ.pop('FINANCIAL_ANALYSIS_ENV', None)
            
        reload_settings()
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Environment detection failed: {e}")
        return False

def test_api_key_loading():
    """Test API key loading from environment"""
    print("\nTesting API key loading...")
    
    try:
        from config.settings import get_api_config
        
        api_config = get_api_config()
        
        # Check API key status (don't print actual keys for security)
        av_key_status = "set" if api_config.alpha_vantage_key else "not set"
        fmp_key_status = "set" if api_config.fmp_key else "not set"
        
        print(f"[OK] API keys loaded:")
        print(f"   Alpha Vantage: {av_key_status}")
        print(f"   FMP: {fmp_key_status}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] API key loading failed: {e}")
        return False

def test_module_imports():
    """Test that refactored modules can import config"""
    print("\nTesting refactored module imports...")
    
    modules_to_test = [
        'centralized_data_manager',
        'api_diagnostic_tool', 
        'data_sources'
    ]
    
    success_count = 0
    
    for module_name in modules_to_test:
        try:
            # Just test import, don't instantiate classes
            __import__(module_name)
            print(f"[OK] {module_name} imports successfully")
            success_count += 1
        except Exception as e:
            print(f"[FAIL] {module_name} import failed: {e}")
    
    print(f"   {success_count}/{len(modules_to_test)} modules imported successfully")
    return success_count == len(modules_to_test)

def main():
    """Run all configuration tests"""
    print("Configuration Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Constants Import", test_constants_import),
        ("Settings Import", test_settings_import), 
        ("Legacy Compatibility", test_legacy_compatibility),
        ("Environment Detection", test_environment_detection),
        ("API Key Loading", test_api_key_loading),
        ("Module Imports", test_module_imports)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[FAIL] {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("All configuration tests passed!")
    else:
        print("Some tests failed - check configuration setup")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)