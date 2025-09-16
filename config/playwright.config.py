"""
Playwright configuration for E2E tests of the Financial Analysis Streamlit app.
"""

from playwright.sync_api import Playwright
import os

# Test configuration
BASE_URL = "http://localhost:8501"  # Default Streamlit port
TIMEOUT = 30000  # 30 seconds
EXPECT_TIMEOUT = 10000  # 10 seconds

def pytest_playwright_configure(config):
    """Configure Playwright with custom settings."""
    config.option.base_url = BASE_URL
    config.option.browser_name = ["chromium"]
    config.option.headed = False  # Set to True for debugging

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "streamlit: mark test as streamlit-specific"
    )

# Browser configuration
BROWSER_CONFIG = {
    "headless": True,
    "viewport": {"width": 1280, "height": 720},
    "timeout": TIMEOUT,
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-web-security",
    ]
}

# Test data paths
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "tests", "e2e", "test_data")
COMPANY_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "companies")