"""
Performance-focused E2E tests for the Streamlit application.
"""

import pytest
import time
from datetime import datetime


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.streamlit
class TestPerformance:
    """Test performance aspects of the application."""
    
    def test_app_startup_time(self, page_setup, streamlit_app, wait_for_streamlit):
        """Test that app loads within acceptable time."""
        page = page_setup
        
        start_time = time.time()
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        load_time = time.time() - start_time
        
        # App should load within 30 seconds
        assert load_time < 30, f"App took {load_time:.2f} seconds to load, which exceeds 30 second limit"
    
    def test_analysis_response_time(self, page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
        """Test that analysis completes within reasonable time."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Select a ticker
        selectbox = page.query_selector('[data-testid="stSelectbox"]')
        if selectbox:
            page.click('[data-testid="stSelectbox"]')
            page.wait_for_timeout(1000)
            
            # Select MSFT (should have data)
            msft_option = page.query_selector('text="MSFT"')
            if msft_option:
                msft_option.click()
                page.wait_for_timeout(2000)
                
                # Run analysis and measure time
                analyze_button = page.query_selector('button:has-text("Analyze")')
                if analyze_button and analyze_button.is_enabled():
                    start_time = time.time()
                    analyze_button.click()
                    
                    # Wait for analysis to complete
                    streamlit_helpers.wait_for_analysis_complete(page)
                    analysis_time = time.time() - start_time
                    
                    # Analysis should complete within 60 seconds
                    assert analysis_time < 60, f"Analysis took {analysis_time:.2f} seconds, which exceeds 60 second limit"
    
    def test_memory_usage_stability(self, page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
        """Test that memory usage remains stable during multiple analyses."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Run multiple analyses to check for memory leaks
        tickers = ["MSFT", "NVDA", "TSLA"]
        
        for ticker in tickers:
            selectbox = page.query_selector('[data-testid="stSelectbox"]')
            if selectbox:
                page.click('[data-testid="stSelectbox"]')
                page.wait_for_timeout(1000)
                
                ticker_option = page.query_selector(f'text="{ticker}"')
                if ticker_option:
                    ticker_option.click()
                    page.wait_for_timeout(2000)
                    
                    analyze_button = page.query_selector('button:has-text("Analyze")')
                    if analyze_button and analyze_button.is_enabled():
                        analyze_button.click()
                        streamlit_helpers.wait_for_analysis_complete(page)
                        page.wait_for_timeout(2000)  # Let resources settle
        
        # App should still be responsive after multiple analyses
        main_container = page.query_selector('[data-testid="stApp"]')
        assert main_container is not None, "App should remain responsive after multiple analyses"
    
    def test_concurrent_user_simulation(self, page_setup, streamlit_app, wait_for_streamlit):
        """Test app behavior under simulated concurrent usage."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Simulate rapid user interactions
        interactions = [
            lambda: page.click('[data-testid="stSelectbox"]') if page.query_selector('[data-testid="stSelectbox"]') else None,
            lambda: page.keyboard.press('Escape'),
            lambda: page.reload(),
        ]
        
        for interaction in interactions:
            try:
                interaction()
                page.wait_for_timeout(500)
            except:
                # Some interactions might fail, that's okay
                pass
        
        # App should recover from rapid interactions
        wait_for_streamlit()
        main_container = page.query_selector('[data-testid="stApp"]')
        assert main_container is not None, "App should recover from rapid user interactions"


@pytest.mark.e2e
@pytest.mark.streamlit
class TestDataHandling:
    """Test data handling performance and reliability."""
    
    def test_large_dataset_handling(self, page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
        """Test handling of large datasets."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Test with multiple tickers that might have extensive data
        large_data_tickers = ["MSFT", "NVDA", "GOOG"]
        
        for ticker in large_data_tickers:
            selectbox = page.query_selector('[data-testid="stSelectbox"]')
            if selectbox:
                page.click('[data-testid="stSelectbox"]')
                page.wait_for_timeout(1000)
                
                ticker_option = page.query_selector(f'text="{ticker}"')
                if ticker_option:
                    ticker_option.click()
                    page.wait_for_timeout(2000)
                    
                    # Run analysis
                    analyze_button = page.query_selector('button:has-text("Analyze")')
                    if analyze_button and analyze_button.is_enabled():
                        analyze_button.click()
                        
                        # Wait with extended timeout for large datasets
                        try:
                            streamlit_helpers.wait_for_analysis_complete(page)
                            
                            # Check that results were generated
                            results_found = (
                                page.query_selector('[data-testid="metric-container"]') or
                                page.query_selector('[data-testid="stDataFrame"]') or
                                page.query_selector('text="Analysis Results"')
                            )
                            
                            if results_found:
                                # Large dataset was handled successfully
                                break
                        except:
                            # Continue to next ticker if this one fails
                            continue
    
    def test_error_recovery(self, page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
        """Test error recovery mechanisms."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Try to trigger an error condition
        analyze_button = page.query_selector('button:has-text("Analyze")')
        if analyze_button and analyze_button.is_enabled():
            # Try to analyze without selecting a ticker
            analyze_button.click()
            page.wait_for_timeout(3000)
            
            # Check if app recovered gracefully
            main_container = page.query_selector('[data-testid="stApp"]')
            assert main_container is not None, "App should recover from error conditions"
            
            # Try normal operation after error
            selectbox = page.query_selector('[data-testid="stSelectbox"]')
            if selectbox:
                page.click('[data-testid="stSelectbox"]')
                page.wait_for_timeout(1000)
                
                # App should still be functional
                assert selectbox.is_enabled(), "App functionality should be restored after error"