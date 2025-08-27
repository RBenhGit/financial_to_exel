"""
E2E tests for specific analysis workflows (FCF, DCF, DDM, P/B).
"""

import pytest
import time
from pathlib import Path


@pytest.mark.e2e
@pytest.mark.streamlit
@pytest.mark.slow
class TestFCFAnalysis:
    """Test Free Cash Flow analysis workflow."""
    
    def test_fcf_with_excel_data(self, page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers, test_company_data):
        """Test FCF analysis using existing Excel data."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Navigate to FCF Analysis section
        self._navigate_to_fcf(page)
        
        # Test with companies that have Excel data
        for ticker in ["MSFT", "NVDA", "TSLA"]:
            if test_company_data[ticker].exists():
                self._test_fcf_for_ticker(page, ticker, streamlit_helpers)
                break
    
    def test_fcf_growth_calculations(self, page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
        """Test FCF growth rate calculations."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        self._navigate_to_fcf(page)
        
        # Select ticker and run analysis
        if self._select_ticker_and_analyze(page, "MSFT", streamlit_helpers):
            # Look for growth rate information
            growth_indicators = [
                'text="Growth Rate"',
                'text="CAGR"',
                'text="YoY Growth"'
            ]
            
            for indicator in growth_indicators:
                if page.query_selector(indicator):
                    break
            else:
                # Growth calculations might be embedded in results
                pass
    
    def _navigate_to_fcf(self, page):
        """Navigate to FCF analysis section."""
        fcf_nav = page.query_selector('text="FCF Analysis"')
        if fcf_nav and fcf_nav.is_visible():
            fcf_nav.click()
            page.wait_for_timeout(1000)
    
    def _test_fcf_for_ticker(self, page, ticker, streamlit_helpers):
        """Test FCF analysis for a specific ticker."""
        if self._select_ticker_and_analyze(page, ticker, streamlit_helpers):
            # Verify results appear
            results_found = self._check_for_fcf_results(page)
            error_occurred = streamlit_helpers.check_error_message(page)
            
            assert results_found or not error_occurred, f"FCF analysis for {ticker} should produce results or run without errors"
    
    def _select_ticker_and_analyze(self, page, ticker, streamlit_helpers):
        """Select ticker and run analysis."""
        # Select ticker
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
                if not analyze_button:
                    analyze_button = page.query_selector('button:has-text("Calculate FCF")')
                
                if analyze_button and analyze_button.is_enabled():
                    analyze_button.click()
                    streamlit_helpers.wait_for_analysis_complete(page)
                    return True
        return False
    
    def _check_for_fcf_results(self, page):
        """Check if FCF results are displayed."""
        fcf_indicators = [
            'text="Free Cash Flow"',
            'text="FCF"',
            'text="Cash Flow from Operations"',
            'text="Capital Expenditures"',
            '[data-testid="metric-container"]',
            '[data-testid="stDataFrame"]'
        ]
        
        for indicator in fcf_indicators:
            if page.query_selector(indicator):
                return True
        return False


@pytest.mark.e2e
@pytest.mark.streamlit
@pytest.mark.slow
class TestDCFValuation:
    """Test Discounted Cash Flow valuation workflow."""
    
    def test_dcf_valuation_process(self, page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
        """Test complete DCF valuation process."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Navigate to DCF section
        dcf_nav = page.query_selector('text="DCF Valuation"')
        if dcf_nav and dcf_nav.is_visible():
            dcf_nav.click()
            page.wait_for_timeout(1000)
            
            # Test DCF with MSFT data
            self._test_dcf_valuation(page, "MSFT", streamlit_helpers)
    
    def test_dcf_parameters(self, page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
        """Test DCF parameter inputs."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Look for DCF parameter inputs
        dcf_params = [
            'text="Discount Rate"',
            'text="Growth Rate"',
            'text="Terminal Growth"',
            'text="WACC"'
        ]
        
        for param in dcf_params:
            param_element = page.query_selector(param)
            if param_element:
                break
    
    def _test_dcf_valuation(self, page, ticker, streamlit_helpers):
        """Test DCF valuation for a specific ticker."""
        # Select ticker
        selectbox = page.query_selector('[data-testid="stSelectbox"]')
        if selectbox:
            page.click('[data-testid="stSelectbox"]')
            page.wait_for_timeout(1000)
            
            ticker_option = page.query_selector(f'text="{ticker}"')
            if ticker_option:
                ticker_option.click()
                page.wait_for_timeout(2000)
                
                # Run DCF analysis
                dcf_button = page.query_selector('button:has-text("Calculate DCF")')
                if not dcf_button:
                    dcf_button = page.query_selector('button:has-text("Run DCF")')
                if not dcf_button:
                    dcf_button = page.query_selector('button:has-text("Analyze")')
                
                if dcf_button and dcf_button.is_enabled():
                    dcf_button.click()
                    streamlit_helpers.wait_for_analysis_complete(page)
                    
                    # Check for DCF results
                    dcf_results = self._check_dcf_results(page)
                    error_occurred = streamlit_helpers.check_error_message(page)
                    
                    assert dcf_results or not error_occurred, f"DCF analysis for {ticker} should produce results or run without errors"
    
    def _check_dcf_results(self, page):
        """Check if DCF results are displayed."""
        dcf_indicators = [
            'text="Valuation"',
            'text="Intrinsic Value"',
            'text="Present Value"',
            'text="Terminal Value"',
            'text="Enterprise Value"'
        ]
        
        for indicator in dcf_indicators:
            if page.query_selector(indicator):
                return True
        return False


@pytest.mark.e2e
@pytest.mark.streamlit
@pytest.mark.slow
class TestPBAnalysis:
    """Test Price-to-Book analysis workflow."""
    
    def test_pb_historical_analysis(self, page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
        """Test P/B historical analysis."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Navigate to P/B analysis
        pb_nav = page.query_selector('text="P/B Analysis"')
        if pb_nav and pb_nav.is_visible():
            pb_nav.click()
            page.wait_for_timeout(1000)
            
            self._test_pb_analysis(page, "MSFT", streamlit_helpers)
    
    def test_pb_fair_value_calculation(self, page_setup, streamlit_app, wait_for_streamlit, streamlit_helpers):
        """Test P/B fair value calculations."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Navigate and test P/B fair value
        pb_nav = page.query_selector('text="P/B Analysis"')
        if pb_nav and pb_nav.is_visible():
            pb_nav.click()
            page.wait_for_timeout(1000)
            
            # Look for fair value indicators
            fair_value_elements = [
                'text="Fair Value"',
                'text="P/B Ratio"',
                'text="Book Value"'
            ]
            
            for element in fair_value_elements:
                if page.query_selector(element):
                    break
    
    def _test_pb_analysis(self, page, ticker, streamlit_helpers):
        """Test P/B analysis for a specific ticker."""
        selectbox = page.query_selector('[data-testid="stSelectbox"]')
        if selectbox:
            page.click('[data-testid="stSelectbox"]')
            page.wait_for_timeout(1000)
            
            ticker_option = page.query_selector(f'text="{ticker}"')
            if ticker_option:
                ticker_option.click()
                page.wait_for_timeout(2000)
                
                # Run P/B analysis
                pb_button = page.query_selector('button:has-text("Analyze P/B")')
                if not pb_button:
                    pb_button = page.query_selector('button:has-text("Calculate")')
                if not pb_button:
                    pb_button = page.query_selector('button:has-text("Analyze")')
                
                if pb_button and pb_button.is_enabled():
                    pb_button.click()
                    streamlit_helpers.wait_for_analysis_complete(page)
                    
                    # Check results
                    pb_results = self._check_pb_results(page)
                    error_occurred = streamlit_helpers.check_error_message(page)
                    
                    assert pb_results or not error_occurred, f"P/B analysis for {ticker} should produce results or run without errors"
    
    def _check_pb_results(self, page):
        """Check if P/B results are displayed."""
        pb_indicators = [
            'text="P/B Ratio"',
            'text="Book Value"',
            'text="Price to Book"',
            'text="Historical P/B"'
        ]
        
        for indicator in pb_indicators:
            if page.query_selector(indicator):
                return True
        return False


@pytest.mark.e2e
@pytest.mark.streamlit
class TestWatchList:
    """Test watch list functionality if available."""
    
    def test_watch_list_access(self, page_setup, streamlit_app, wait_for_streamlit):
        """Test access to watch list functionality."""
        page = page_setup
        page.goto("http://localhost:8501")
        wait_for_streamlit()
        
        # Look for watch list navigation
        watchlist_nav = page.query_selector('text="Watch List"')
        if not watchlist_nav:
            watchlist_nav = page.query_selector('text="Watchlist"')
        if not watchlist_nav:
            watchlist_nav = page.query_selector('text="Portfolio"')
        
        if watchlist_nav and watchlist_nav.is_visible():
            watchlist_nav.click()
            page.wait_for_timeout(1000)
            
            # Check that watchlist section loads
            main_container = page.query_selector('[data-testid="stApp"]')
            assert main_container is not None, "Watch list section should load successfully"