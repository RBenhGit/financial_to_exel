"""
Pytest configuration and shared fixtures for the test suite.

This module provides centralized test configuration and reusable fixtures
to eliminate code duplication across test files.
"""

import os
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from openpyxl import Workbook, load_workbook
import tempfile
import shutil
from typing import Dict, List, Any

# Import fixtures from organized modules
from tests.fixtures.company_data import CompanyDataFixture
from tests.fixtures.excel_helpers import ExcelTestHelper
from tests.fixtures.mock_data import MockDataGenerator
from tests.fixtures.api_helpers import APITestHelper


@pytest.fixture(scope='session')
def company_data_manager():
    """Centralized company data discovery and management"""
    return CompanyDataFixture()


@pytest.fixture(scope='function')
def temp_company_structure():
    """Create temporary company directory structure for testing"""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample company structure
    company_dir = os.path.join(temp_dir, 'TEST')
    os.makedirs(company_dir)
    
    # Create FY and LTM subdirectories
    for period in ['FY', 'LTM']:
        period_dir = os.path.join(company_dir, period)
        os.makedirs(period_dir)
        
        # Create sample Excel files
        for statement in ['Income Statement', 'Balance Sheet', 'Cash Flow Statement']:
            file_path = os.path.join(period_dir, f'TEST - {statement}.xlsx')
            ExcelTestHelper.create_sample_excel_file(file_path, statement)
    
    yield company_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_excel_data():
    """Mock Excel data for testing without file dependencies"""
    return ExcelTestHelper.create_sample_data()


@pytest.fixture
def mock_yfinance_responses():
    """Mock yfinance API responses to avoid rate limiting in tests"""
    return APITestHelper.create_mock_responses()


@pytest.fixture
def sample_fcf_data():
    """Generate sample FCF data for testing calculations"""
    return MockDataGenerator.generate_fcf_data()


@pytest.fixture
def sample_financial_metrics():
    """Generate sample financial metrics for testing"""
    return MockDataGenerator.generate_financial_metrics()


@pytest.fixture(scope='function')
def clean_cache():
    """Ensure clean state between tests by clearing caches"""
    yield
    # Clear any cached data after each test
    import gc
    gc.collect()


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = {
        'excel_structure': {
            'data_start_column': 4,
            'ltm_column': 15,
            'max_scan_rows': 59
        },
        'dcf': {
            'default_discount_rate': 0.10,
            'default_terminal_growth_rate': 0.025,
            'growth_rate_periods': [1, 3, 5, 10]
        },
        'validation': {
            'min_data_completeness': 0.7,
            'strict_validation': False
        }
    }
    return config


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (deselect with '-m \"not unit\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "api_dependent: marks tests that require API access"
    )
    config.addinivalue_line(
        "markers", "excel_dependent: marks tests that require Excel files"
    )


# Auto-use fixtures for common setup
@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests"""
    import logging
    logging.basicConfig(level=logging.WARNING, format='%(name)s - %(levelname)s - %(message)s')