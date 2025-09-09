"""
Pytest configuration and fixtures for E2E tests.
"""

import pytest
import subprocess
import time
import requests
from pathlib import Path
import os
import signal


@pytest.fixture(scope="session")
def streamlit_app():
    """Start the Streamlit application for testing."""
    # Path to the main Streamlit app
    app_path = Path(__file__).parent.parent.parent / "ui" / "streamlit" / "fcf_analysis_streamlit.py"
    
    # Start Streamlit process
    process = subprocess.Popen([
        "python", "-m", "streamlit", "run", str(app_path),
        "--server.port=8501",
        "--server.headless=true",
        "--server.runOnSave=false",
        "--logger.level=error"
    ])
    
    # Wait for the app to start
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8501", timeout=2)
            if response.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(1)
    else:
        process.terminate()
        raise RuntimeError("Streamlit app failed to start within 30 seconds")
    
    yield process
    
    # Cleanup: terminate the process
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def page_setup(page):
    """Set up page with common configurations."""
    page.set_viewport_size({"width": 1280, "height": 720})
    page.set_default_timeout(30000)  # 30 seconds
    return page


@pytest.fixture
def test_company_data():
    """Provide test company data paths."""
    return {
        "MSFT": Path(__file__).parent.parent.parent / "data" / "companies" / "MSFT",
        "NVDA": Path(__file__).parent.parent.parent / "data" / "companies" / "NVDA",
        "TSLA": Path(__file__).parent.parent.parent / "data" / "companies" / "TSLA",
    }


@pytest.fixture
def wait_for_streamlit(page):
    """Wait for Streamlit to be ready."""
    def _wait():
        # Wait for Streamlit's main container to be visible
        page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
        # Wait for any initial loading to complete
        page.wait_for_timeout(2000)
    return _wait


@pytest.fixture
def streamlit_helpers():
    """Helper functions for Streamlit interactions."""
    class StreamlitHelpers:
        @staticmethod
        def select_ticker(page, ticker):
            """Select a ticker from the dropdown."""
            page.click('[data-testid="stSelectbox"]')
            page.click(f'text="{ticker}"')
        
        @staticmethod
        def click_button(page, button_text):
            """Click a button by its text."""
            page.click(f'button:has-text("{button_text}")')
        
        @staticmethod
        def wait_for_analysis_complete(page):
            """Wait for analysis to complete."""
            # Wait for any loading spinners to disappear
            page.wait_for_function(
                "document.querySelector('[data-testid=\"stSpinner\"]') === null",
                timeout=60000
            )
        
        @staticmethod
        def check_error_message(page):
            """Check if there's an error message."""
            error_elements = page.query_selector_all('[data-testid="stAlert"]')
            return len(error_elements) > 0
        
        @staticmethod
        def get_metric_value(page, metric_name):
            """Get value from a Streamlit metric widget."""
            metric_element = page.query_selector(f'[data-testid="metric-container"]:has-text("{metric_name}")')
            if metric_element:
                return metric_element.inner_text()
            return None
    
    return StreamlitHelpers()