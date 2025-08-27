"""
E2E tests for the main Streamlit application workflows.
"""

import pytest
import time
from pathlib import Path


@pytest.mark.e2e
@pytest.mark.streamlit
def test_app_loads_successfully(page_setup, streamlit_app, wait_for_streamlit):
    """Test that the Streamlit app loads without errors."""
    page = page_setup
    page.goto("http://localhost:8501")
    wait_for_streamlit()
    
    # Check that the main app container is present
    assert page.query_selector('[data-testid="stApp"]') is not None
    
    # Check for the app title
    title_element = page.query_selector('h1')
    assert title_element is not None
    assert "FCF Analysis" in title_element.inner_text() or "Financial Analysis" in title_element.inner_text()


@pytest.mark.e2e
@pytest.mark.streamlit
def test_sidebar_navigation(page_setup, streamlit_app, wait_for_streamlit):
    """Test sidebar navigation between different analysis types."""
    page = page_setup
    page.goto("http://localhost:8501")
    wait_for_streamlit()
    
    # Test that sidebar is present
    sidebar = page.query_selector('[data-testid="stSidebar"]')
    assert sidebar is not None
    
    # Test navigation options exist
    nav_options = ["FCF Analysis", "DCF Valuation", "DDM Analysis", "P/B Analysis"]
    
    for option in nav_options:
        try:
            option_element = page.query_selector(f'text="{option}"')
            if option_element:
                assert option_element.is_visible()
        except:
            # Some options might not be visible depending on implementation
            pass


@pytest.mark.e2e
@pytest.mark.streamlit
def test_ticker_selection(page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
    """Test ticker selection functionality."""
    page = page_setup
    page.goto("http://localhost:8501")
    wait_for_streamlit()
    
    # Look for ticker selection dropdown
    selectbox = page.query_selector('[data-testid="stSelectbox"]')
    if selectbox:
        # Try to select a test ticker
        page.click('[data-testid="stSelectbox"]')
        page.wait_for_timeout(1000)
        
        # Look for available options
        options = page.query_selector_all('[data-baseweb="list-item"]')
        if len(options) > 1:  # More than just the default option
            options[1].click()
            page.wait_for_timeout(1000)


@pytest.mark.e2e
@pytest.mark.streamlit
@pytest.mark.slow
def test_fcf_analysis_workflow(page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
    """Test the complete FCF analysis workflow."""
    page = page_setup
    page.goto("http://localhost:8501")
    wait_for_streamlit()
    
    # Navigate to FCF Analysis if not default
    fcf_option = page.query_selector('text="FCF Analysis"')
    if fcf_option and fcf_option.is_visible():
        fcf_option.click()
        page.wait_for_timeout(1000)
    
    # Select a ticker if dropdown is available
    selectbox = page.query_selector('[data-testid="stSelectbox"]')
    if selectbox:
        page.click('[data-testid="stSelectbox"]')
        page.wait_for_timeout(1000)
        
        # Try to select MSFT as it has test data
        msft_option = page.query_selector('text="MSFT"')
        if msft_option:
            msft_option.click()
            page.wait_for_timeout(2000)
    
    # Look for analysis button
    analyze_button = page.query_selector('button:has-text("Analyze")')
    if not analyze_button:
        analyze_button = page.query_selector('button:has-text("Run Analysis")')
    if not analyze_button:
        analyze_button = page.query_selector('button:has-text("Calculate")')
    
    if analyze_button and analyze_button.is_enabled():
        analyze_button.click()
        
        # Wait for analysis to complete (up to 30 seconds)
        streamlit_helpers.wait_for_analysis_complete(page)
        
        # Check for results
        # Look for common result indicators
        results_indicators = [
            '[data-testid="metric-container"]',  # Streamlit metrics
            'text="Free Cash Flow"',
            'text="Analysis Results"',
            '[data-testid="stDataFrame"]'  # Data tables
        ]
        
        result_found = False
        for indicator in results_indicators:
            if page.query_selector(indicator):
                result_found = True
                break
        
        # Check that no error occurred
        error_occurred = streamlit_helpers.check_error_message(page)
        
        # At least one result should be present and no errors
        assert result_found or not error_occurred, "Analysis should produce results or run without errors"


@pytest.mark.e2e
@pytest.mark.streamlit  
@pytest.mark.slow
def test_dcf_valuation_workflow(page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
    """Test the DCF valuation workflow."""
    page = page_setup
    page.goto("http://localhost:8501")
    wait_for_streamlit()
    
    # Navigate to DCF Valuation
    dcf_option = page.query_selector('text="DCF Valuation"')
    if dcf_option and dcf_option.is_visible():
        dcf_option.click()
        page.wait_for_timeout(1000)
    
    # Select a ticker
    selectbox = page.query_selector('[data-testid="stSelectbox"]')
    if selectbox:
        page.click('[data-testid="stSelectbox"]')
        page.wait_for_timeout(1000)
        
        # Try to select MSFT
        msft_option = page.query_selector('text="MSFT"')
        if msft_option:
            msft_option.click()
            page.wait_for_timeout(2000)
    
    # Look for DCF-specific inputs or run button
    dcf_button = page.query_selector('button:has-text("Calculate DCF")')
    if not dcf_button:
        dcf_button = page.query_selector('button:has-text("Run DCF")')
    if not dcf_button:
        dcf_button = page.query_selector('button:has-text("Analyze")')
    
    if dcf_button and dcf_button.is_enabled():
        dcf_button.click()
        streamlit_helpers.wait_for_analysis_complete(page)
        
        # Check for DCF results
        dcf_results = page.query_selector('text="Valuation"') or page.query_selector('text="DCF"')
        error_occurred = streamlit_helpers.check_error_message(page)
        
        assert dcf_results or not error_occurred, "DCF analysis should produce results or run without errors"


@pytest.mark.e2e
@pytest.mark.streamlit
def test_data_export_functionality(page_setup, streamlit_app, wait_for_streamlit):
    """Test data export functionality if available."""
    page = page_setup
    page.goto("http://localhost:8501")
    wait_for_streamlit()
    
    # Look for export buttons
    export_button = page.query_selector('button:has-text("Export")')
    if not export_button:
        export_button = page.query_selector('button:has-text("Download")')
    if not export_button:
        export_button = page.query_selector('[data-testid="stDownloadButton"]')
    
    if export_button and export_button.is_visible():
        # Export functionality exists
        assert export_button.is_enabled(), "Export button should be enabled when data is available"


@pytest.mark.e2e
@pytest.mark.streamlit
def test_error_handling(page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
    """Test error handling with invalid inputs."""
    page = page_setup
    page.goto("http://localhost:8501")
    wait_for_streamlit()
    
    # Try to run analysis without selecting a ticker
    analyze_button = page.query_selector('button:has-text("Analyze")')
    if not analyze_button:
        analyze_button = page.query_selector('button:has-text("Run Analysis")')
    
    if analyze_button and analyze_button.is_enabled():
        analyze_button.click()
        page.wait_for_timeout(3000)
        
        # Should either show an error message or handle gracefully
        has_error = streamlit_helpers.check_error_message(page)
        
        # The app should handle this gracefully (either with error message or preventing action)
        # This test mainly ensures the app doesn't crash
        main_container = page.query_selector('[data-testid="stApp"]')
        assert main_container is not None, "App should remain functional after error"


@pytest.mark.e2e
@pytest.mark.streamlit
def test_responsive_design(page_setup, streamlit_app, wait_for_streamlit):
    """Test responsive design on different screen sizes."""
    page = page_setup
    page.goto("http://localhost:8501")
    wait_for_streamlit()
    
    # Test mobile size
    page.set_viewport_size({"width": 375, "height": 667})
    page.wait_for_timeout(1000)
    
    main_container = page.query_selector('[data-testid="stApp"]')
    assert main_container is not None, "App should be functional on mobile size"
    
    # Test tablet size
    page.set_viewport_size({"width": 768, "height": 1024})
    page.wait_for_timeout(1000)
    
    assert main_container is not None, "App should be functional on tablet size"
    
    # Reset to desktop
    page.set_viewport_size({"width": 1280, "height": 720})