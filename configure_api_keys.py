"""
API Configuration Script for Financial Analysis System

This script helps you configure API keys for alternative data sources like:
- Alpha Vantage
- Financial Modeling Prep (FMP)  
- Polygon.io

Usage:
    python configure_api_keys.py
"""

import json
import os
from pathlib import Path

def load_config():
    """Load current configuration"""
    config_file = "data_sources_config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return None

def save_config(config):
    """Save configuration to file"""
    config_file = "data_sources_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"[SAVED] Configuration saved to {config_file}")

def configure_alpha_vantage():
    """Configure Alpha Vantage API"""
    print("\n[KEY] Alpha Vantage Configuration")
    print("=" * 40)
    print("Get your free API key at: https://www.alphavantage.co/support/#api-key")
    print("Free tier: 25 requests/day, 5 requests/minute")
    
    api_key = input("Enter your Alpha Vantage API key (or press Enter to skip): ").strip()
    
    if api_key:
        return {
            "priority": 2,
            "is_enabled": True,
            "quality_threshold": 0.8,
            "cache_ttl_hours": 24,
            "credentials": {
                "api_key": api_key,
                "base_url": "https://www.alphavantage.co/query",
                "rate_limit_calls": 5,
                "rate_limit_period": 60,
                "timeout": 30,
                "retry_attempts": 3,
                "cost_per_call": 0.0,
                "monthly_limit": 500,
                "is_active": True
            }
        }
    return None

def configure_fmp():
    """Configure Financial Modeling Prep API"""
    print("\n[KEY] Financial Modeling Prep Configuration")
    print("=" * 45)
    print("Get your API key at: https://financialmodelingprep.com/developer/docs")
    print("Free tier: 250 requests/day")
    
    api_key = input("Enter your FMP API key (or press Enter to skip): ").strip()
    
    if api_key:
        return {
            "priority": 2,
            "is_enabled": True,
            "quality_threshold": 0.85,
            "cache_ttl_hours": 12,
            "credentials": {
                "api_key": api_key,
                "base_url": "https://financialmodelingprep.com/api/v3",
                "rate_limit_calls": 250,
                "rate_limit_period": 3600,
                "timeout": 30,
                "retry_attempts": 3,
                "cost_per_call": 0.0,
                "monthly_limit": 250,
                "is_active": True
            }
        }
    return None

def configure_polygon():
    """Configure Polygon.io API"""
    print("\n[KEY] Polygon.io Configuration")
    print("=" * 30)
    print("Get your API key at: https://polygon.io/")
    print("Free tier: 5 requests/minute")
    
    api_key = input("Enter your Polygon.io API key (or press Enter to skip): ").strip()
    
    if api_key:
        return {
            "priority": 3,
            "is_enabled": True,
            "quality_threshold": 0.9,
            "cache_ttl_hours": 6,
            "credentials": {
                "api_key": api_key,
                "base_url": "https://api.polygon.io",
                "rate_limit_calls": 5,
                "rate_limit_period": 60,
                "timeout": 30,
                "retry_attempts": 3,
                "cost_per_call": 0.003,
                "monthly_limit": 1000,
                "is_active": True
            }
        }
    return None

def test_api_configuration():
    """Test the configured APIs"""
    print("\n[TEST] Testing API Configuration")
    print("=" * 35)
    
    try:
        from enhanced_data_manager import create_enhanced_data_manager
        
        manager = create_enhanced_data_manager()
        test_results = manager.test_all_sources("AAPL")
        
        print(f"[OK] Test completed for AAPL")
        print(f"[RESULTS] Results: {test_results['summary']['successful_sources']}/{test_results['summary']['total_sources']} sources working")
        
        for source_name, result in test_results['sources'].items():
            status = "[OK]" if result.get('success', False) else "[FAIL]" 
            print(f"  {status} {source_name}: {'Working' if result.get('success', False) else result.get('error', 'Failed')}")
        
        if test_results['summary']['best_source']:
            print(f"[BEST] Best source: {test_results['summary']['best_source']}")
        
        manager.cleanup()
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False

def show_current_config():
    """Show current configuration status"""
    config = load_config()
    if not config:
        print("[ERROR] No configuration found")
        return
    
    print("\n[CONFIG] Current API Configuration")
    print("=" * 35)
    
    for source_name, source_config in config['sources'].items():
        if source_name == 'excel' or source_name == 'yfinance':
            continue
            
        status = "[ENABLED]" if source_config.get('is_enabled', False) else "[DISABLED]"
        has_key = bool(source_config.get('credentials', {}).get('api_key', ''))
        key_status = "[KEY SET]" if has_key else "[NO KEY]"
        
        print(f"{source_name.upper()}: {status} | {key_status}")

def main():
    """Main configuration interface"""
    print("Financial Analysis API Configuration")
    print("=" * 50)
    
    # Show current status
    show_current_config()
    
    # Load existing config
    config = load_config()
    if not config:
        print("[ERROR] Configuration file not found. Please run the main application first.")
        return
    
    print("\nAvailable API providers:")
    print("1. Alpha Vantage (Free: 25 requests/day)")  
    print("2. Financial Modeling Prep (Free: 250 requests/day)")
    print("3. Polygon.io (Free: 5 requests/minute)")
    print("4. Test current configuration")
    print("5. Show current status")
    print("0. Exit")
    
    while True:
        choice = input("\nEnter your choice (0-5): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            alpha_config = configure_alpha_vantage()
            if alpha_config:
                config['sources']['alpha_vantage'] = alpha_config
                save_config(config)
        elif choice == '2':
            fmp_config = configure_fmp()
            if fmp_config:
                config['sources']['fmp'] = fmp_config
                save_config(config)
        elif choice == '3':
            polygon_config = configure_polygon()
            if polygon_config:
                config['sources']['polygon'] = polygon_config
                save_config(config)
        elif choice == '4':
            test_api_configuration()
        elif choice == '5':
            show_current_config()
        else:
            print("[ERROR] Invalid choice. Please try again.")
    
    print("\n[DONE] Configuration complete!")
    print("\nNext steps:")
    print("1. Run the Streamlit app: streamlit run fcf_analysis_streamlit.py")
    print("2. Select ticker mode and test with a stock symbol")
    print("3. The system will now use your configured APIs as fallbacks")

if __name__ == "__main__":
    main()