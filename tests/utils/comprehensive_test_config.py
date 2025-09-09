"""
Comprehensive Test Configuration for Unified Data System
Task #70 Implementation: Testing Framework Setup
"""
import pytest
import sys
import os
from pathlib import Path
import tempfile
import json
from typing import Dict, List, Any

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class ComprehensiveTestConfig:
    """Configuration manager for comprehensive testing framework"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.test_dir = self.project_root / "tests" 
        self.coverage_target = 90.0
        self.test_categories = {
            "unit": "Unit tests for individual components",
            "integration": "Integration tests with real data sources",
            "performance": "Performance tests with large datasets",
            "regression": "Regression tests ensuring no functionality loss",
            "e2e": "End-to-end workflow tests"
        }
    
    def get_core_modules_for_coverage(self) -> List[str]:
        """Get list of core modules that need >90% coverage"""
        return [
            "core.data_processing.financial_variable_registry",
            "core.data_processing.var_input_data", 
            "core.data_processing.adapters",
            "core.analysis.engines.financial_calculations",
            "core.analysis.dcf",
            "core.analysis.ddm",
            "core.analysis.pb"
        ]
    
    def get_test_data_sources(self) -> Dict[str, Path]:
        """Get paths to test data sources"""
        return {
            "excel_data": self.project_root / "data" / "companies",
            "cache_data": self.project_root / "data_cache",
            "test_fixtures": self.test_dir / "fixtures"
        }
    
    def create_test_environment(self) -> Dict[str, Any]:
        """Create isolated test environment"""
        return {
            "temp_dir": tempfile.mkdtemp(prefix="fcf_test_"),
            "mock_apis": True,
            "use_cache": False,
            "strict_validation": True
        }
    
    def get_coverage_report_config(self) -> Dict[str, Any]:
        """Get coverage report configuration"""
        return {
            "formats": ["html", "term-missing", "json", "xml"],
            "output_dir": self.test_dir / "coverage_reports",
            "target_percentage": self.coverage_target,
            "fail_under": 85.0  # Minimum acceptable coverage
        }

# Global test configuration instance
TEST_CONFIG = ComprehensiveTestConfig()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with comprehensive markers"""
    markers = [
        "unit: Unit tests for individual components",
        "integration: Integration tests with real data sources", 
        "performance: Performance tests with large datasets",
        "regression: Regression tests ensuring no functionality loss",
        "e2e: End-to-end workflow tests",
        "api_dependent: Tests requiring API access",
        "excel_dependent: Tests requiring Excel files",
        "slow: Long-running tests",
        "unified_system: Tests for the new unified data system"
    ]
    
    for marker in markers:
        config.addinivalue_line("markers", marker)

# Test fixtures for comprehensive testing
@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return TEST_CONFIG

@pytest.fixture(scope="session") 
def core_modules_coverage():
    """List of core modules requiring >90% coverage"""
    return TEST_CONFIG.get_core_modules_for_coverage()

@pytest.fixture
def test_environment(tmp_path):
    """Create isolated test environment"""
    env = TEST_CONFIG.create_test_environment()
    env["temp_dir"] = tmp_path
    return env

@pytest.fixture
def unified_system_sample_data():
    """Sample data for unified system testing"""
    return {
        "financial_variables": {
            "total_revenue": [1000, 1100, 1200],
            "net_income": [100, 110, 125],
            "free_cash_flow": [80, 95, 105]
        },
        "market_data": {
            "ticker": "TEST", 
            "share_price": 50.0,
            "shares_outstanding": 1000000
        },
        "excel_structure": {
            "income_statement": "Income Statement.xlsx",
            "balance_sheet": "Balance Sheet.xlsx", 
            "cash_flow": "Cash Flow Statement.xlsx"
        }
    }

if __name__ == "__main__":
    print(f"Comprehensive Test Framework Configuration")
    print(f"Project Root: {TEST_CONFIG.project_root}")
    print(f"Coverage Target: {TEST_CONFIG.coverage_target}%")
    print(f"Test Categories: {list(TEST_CONFIG.test_categories.keys())}")