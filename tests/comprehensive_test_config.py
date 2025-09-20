"""
Comprehensive Test Configuration
===============================

Configuration for comprehensive test suites across the financial analysis toolkit.
"""

# Test configuration for unified data system testing
TEST_CONFIG = {
    'test_companies': ['AAPL', 'MSFT', 'GOOGL'],
    'timeout_seconds': 30,
    'max_retries': 3,
    'test_data_path': 'data/companies/',
    'cache_enabled': True,
    'api_rate_limit': 1.0,
    'quality_thresholds': {
        'data_completeness': 0.8,
        'data_accuracy': 0.9,
        'response_time': 5.0
    },
    'test_markers': {
        'unit': 'Unit tests',
        'integration': 'Integration tests',
        'api_dependent': 'Tests requiring API access',
        'excel_dependent': 'Tests requiring Excel files',
        'slow': 'Long-running tests'
    }
}