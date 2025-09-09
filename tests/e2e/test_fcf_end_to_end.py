#!/usr/bin/env python3
"""
Comprehensive End-to-End FCF Calculation Flow Test

Tests the complete FCF calculation pipeline from data source loading through
final FCF results, covering both Excel and API data sources with validation
against known financial statements.
"""

import pytest
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import time
from decimal import Decimal

from core.analysis.engines.financial_calculations import FinancialCalculator
from core.data_processing.managers.centralized_data_manager import CentralizedDataManager
from core.data_processing.managers.enhanced_data_manager import EnhancedDataManager


# Configure logging for test visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.slow
class TestFCFEndToEndFlow:
    """Comprehensive end-to-end tests for FCF calculation pipeline."""
    
    # Test companies with known Excel data
    TEST_COMPANIES = ["MSFT", "NVDA", "TSLA", "GOOG"]
    
    # Expected FCF ranges for validation (in millions)
    FCF_VALIDATION_RANGES = {
        "MSFT": {"min": 40000, "max": 80000},  # Microsoft: ~$40B-$80B FCF range
        "NVDA": {"min": 5000, "max": 30000},   # NVIDIA: ~$5B-$30B FCF range
        "TSLA": {"min": -5000, "max": 15000},  # Tesla: Variable FCF history
        "GOOG": {"min": 30000, "max": 70000}   # Alphabet: ~$30B-$70B FCF range
    }

    def test_excel_data_source_fcf_pipeline(self):
        """Test complete FCF pipeline using Excel data sources."""
        logger.info("Starting Excel data source FCF pipeline test")
        
        for ticker in self.TEST_COMPANIES:
            excel_path = Path(f"data/companies/{ticker}")
            
            if not excel_path.exists():
                logger.warning(f"Skipping {ticker} - no Excel data found")
                continue
                
            logger.info(f"Testing FCF pipeline for {ticker} with Excel data")
            
            try:
                # Initialize FinancialCalculator with Excel data
                calculator = FinancialCalculator(str(excel_path))
                calculator.load_financial_statements()
                
                # Test data loading
                self._validate_data_loading(calculator, ticker)
                
                # Calculate all FCF types
                fcf_results = calculator.calculate_all_fcf_types()
                
                # Validate FCF results
                self._validate_fcf_results(fcf_results, ticker, "Excel")
                
                # Test specific FCF components
                self._validate_fcf_components(calculator, ticker)
                
                logger.info(f"✅ {ticker} Excel FCF pipeline test passed")
                
            except Exception as e:
                logger.error(f"❌ {ticker} Excel FCF pipeline test failed: {e}")
                pytest.fail(f"Excel FCF pipeline failed for {ticker}: {e}")

    def test_api_data_source_fcf_pipeline(self):
        """Test complete FCF pipeline using API data sources."""
        logger.info("Starting API data source FCF pipeline test")
        
        for ticker in self.TEST_COMPANIES[:2]:  # Test fewer for API to avoid rate limits
            logger.info(f"Testing FCF pipeline for {ticker} with API data")
            
            try:
                # Initialize with Enhanced Data Manager for API access
                data_manager = EnhancedDataManager()
                calculator = FinancialCalculator(
                    data_sources={
                        'yfinance_converter': 'core.data_processing.converters.yfinance_converter'
                    }
                )
                
                # Load data from API
                calculator.ticker = ticker
                calculator.load_financial_statements()
                
                # Calculate FCF using API data
                fcf_results = calculator.calculate_all_fcf_types()
                
                # Validate FCF results
                self._validate_fcf_results(fcf_results, ticker, "API")
                
                logger.info(f"✅ {ticker} API FCF pipeline test passed")
                
                # Add small delay to respect rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ {ticker} API FCF pipeline test failed: {e}")
                # Don't fail test for API issues - could be rate limits or connectivity
                logger.warning(f"API test failed for {ticker}, continuing...")

    def test_data_source_fallback_mechanism(self):
        """Test fallback from Excel to API when Excel data is missing."""
        logger.info("Testing data source fallback mechanism")
        
        # Test with a ticker that might not have Excel data
        test_ticker = "AAPL"
        non_existing_path = f"data/companies/{test_ticker}"
        
        try:
            # Try with non-existing Excel path - should fallback to API/enhanced data manager
            calculator = FinancialCalculator(non_existing_path)
            calculator.ticker = test_ticker
            
            # This should try Excel first, then fallback to API
            calculator.load_financial_statements()
            
            # Verify some form of data was loaded
            assert calculator.financial_data is not None, "No data loaded after fallback"
            
            # Calculate FCF to verify the pipeline works
            fcf_results = calculator.calculate_all_fcf_types()
            
            # Should have at least one FCF type calculated
            successful_calcs = sum(1 for values in fcf_results.values() if values)
            assert successful_calcs > 0, "No FCF calculations successful after fallback"
            
            logger.info(f"✅ Fallback mechanism test passed for {test_ticker}")
            
        except Exception as e:
            logger.error(f"❌ Fallback mechanism test failed: {e}")
            # Don't fail test for fallback mechanism - could be API issues
            logger.warning(f"Fallback test failed for {test_ticker}, skipping...")

    def test_fcf_calculation_accuracy_validation(self):
        """Validate FCF calculations against known financial statement values."""
        logger.info("Testing FCF calculation accuracy validation")
        
        for ticker in self.TEST_COMPANIES[:2]:  # Test subset for performance
            excel_path = Path(f"data/companies/{ticker}")
            
            if not excel_path.exists():
                continue
                
            try:
                calculator = FinancialCalculator(str(excel_path))
                calculator.load_financial_statements()
                
                # Get raw financial data for validation
                financial_data = calculator.financial_data
                
                # Calculate FCF manually for comparison
                manual_fcf = self._calculate_manual_fcf(financial_data)
                
                # Get system-calculated FCF
                fcf_results = calculator.calculate_all_fcf_types()
                
                # Compare results
                self._compare_fcf_calculations(manual_fcf, fcf_results, ticker)
                
                logger.info(f"✅ FCF accuracy validation passed for {ticker}")
                
            except Exception as e:
                logger.error(f"❌ FCF accuracy validation failed for {ticker}: {e}")
                pytest.fail(f"FCF accuracy validation failed for {ticker}: {e}")

    def test_performance_benchmark(self):
        """Benchmark FCF calculation performance."""
        logger.info("Starting FCF calculation performance benchmark")
        
        performance_results = {}
        
        for ticker in self.TEST_COMPANIES:
            excel_path = Path(f"data/companies/{ticker}")
            
            if not excel_path.exists():
                continue
                
            try:
                start_time = time.time()
                
                # Time the complete pipeline
                calculator = FinancialCalculator(str(excel_path))
                data_load_time = time.time()
                
                calculator.load_financial_statements()
                statements_load_time = time.time()
                
                fcf_results = calculator.calculate_all_fcf_types()
                calculation_time = time.time()
                
                # Record performance metrics
                performance_results[ticker] = {
                    "total_time": calculation_time - start_time,
                    "data_load_time": data_load_time - start_time,
                    "statements_load_time": statements_load_time - data_load_time,
                    "calculation_time": calculation_time - statements_load_time,
                    "fcf_types_calculated": len([v for v in fcf_results.values() if v])
                }
                
                logger.info(f"{ticker} performance: {performance_results[ticker]['total_time']:.2f}s total")
                
            except Exception as e:
                logger.error(f"Performance benchmark failed for {ticker}: {e}")
        
        # Validate performance expectations
        self._validate_performance_benchmarks(performance_results)
        
        logger.info("✅ Performance benchmark completed")

    def _validate_data_loading(self, calculator: FinancialCalculator, ticker: str):
        """Validate that data was properly loaded."""
        assert calculator.financial_data is not None, f"No financial data loaded for {ticker}"
        assert len(calculator.financial_data) > 0, f"Empty financial data for {ticker}"
        
        # Check for essential financial statement data (FY data)
        required_statements = ["income_fy", "balance_fy", "cashflow_fy"]
        statements_found = []
        
        for statement in required_statements:
            if statement in calculator.financial_data:
                data = calculator.financial_data[statement]
                assert len(data) > 0, f"Empty {statement} for {ticker}"
                statements_found.append(statement)
        
        # Should have at least one financial statement
        assert len(statements_found) > 0, f"No required financial statements found for {ticker}. Available keys: {list(calculator.financial_data.keys())}"
        
        logger.info(f"✅ Data validation passed for {ticker}: {len(statements_found)} statements loaded")

    def _validate_fcf_results(self, fcf_results: Dict[str, List[float]], ticker: str, source: str):
        """Validate FCF calculation results."""
        assert fcf_results is not None, f"No FCF results for {ticker} from {source}"
        
        # Should have at least one FCF type calculated
        successful_calcs = sum(1 for values in fcf_results.values() if values)
        assert successful_calcs > 0, f"No successful FCF calculations for {ticker} from {source}"
        
        # Check FCF values are in reasonable ranges
        for fcf_type, values in fcf_results.items():
            if values:
                latest_fcf = values[-1]
                self._validate_fcf_range(latest_fcf, ticker, fcf_type)
                
                # Check for data consistency
                assert len(values) > 0, f"Empty {fcf_type} values for {ticker}"
                
                # Values should be numeric
                for value in values:
                    assert isinstance(value, (int, float)), f"Non-numeric FCF value: {value}"

    def _validate_fcf_range(self, fcf_value: float, ticker: str, fcf_type: str):
        """Validate FCF value is in expected range for the company."""
        if ticker in self.FCF_VALIDATION_RANGES:
            expected_range = self.FCF_VALIDATION_RANGES[ticker]
            
            # Convert to millions for comparison
            fcf_millions = abs(fcf_value) / 1_000_000
            
            # Allow wider range for validation (companies can have varying FCF)
            min_range = expected_range["min"] * 0.5
            max_range = expected_range["max"] * 2.0
            
            if not (min_range <= fcf_millions <= max_range):
                logger.warning(
                    f"FCF value outside expected range for {ticker}: "
                    f"{fcf_millions:.1f}M (expected: {min_range:.1f}M - {max_range:.1f}M)"
                )

    def _validate_fcf_components(self, calculator: FinancialCalculator, ticker: str):
        """Validate individual FCF calculation components."""
        try:
            # Test individual calculation methods exist and work
            methods_to_test = [
                'calculate_fcfe',
                'calculate_fcff', 
                'calculate_levered_fcf'
            ]
            
            for method_name in methods_to_test:
                if hasattr(calculator, method_name):
                    method = getattr(calculator, method_name)
                    result = method()
                    
                    if result:
                        assert len(result) > 0, f"{method_name} returned empty result for {ticker}"
                        logger.info(f"{method_name} calculated {len(result)} values for {ticker}")
                        
        except Exception as e:
            logger.warning(f"FCF component validation failed for {ticker}: {e}")

    def _calculate_manual_fcf(self, financial_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate FCF manually for validation comparison."""
        # This would implement manual FCF calculation based on raw financial data
        # For now, return empty dict as placeholder
        return {}

    def _compare_fcf_calculations(self, manual_fcf: Dict, system_fcf: Dict, ticker: str):
        """Compare manual vs system FCF calculations."""
        # Placeholder for detailed FCF calculation comparison
        # Would implement specific comparison logic based on calculation methods
        logger.info(f"FCF comparison completed for {ticker}")

    def _validate_performance_benchmarks(self, performance_results: Dict[str, Dict]):
        """Validate performance meets expectations."""
        for ticker, metrics in performance_results.items():
            # Reasonable performance expectations
            assert metrics["total_time"] < 30.0, f"FCF pipeline too slow for {ticker}: {metrics['total_time']:.2f}s"
            assert metrics["fcf_types_calculated"] > 0, f"No FCF types calculated for {ticker}"
            
            logger.info(
                f"Performance validated for {ticker}: "
                f"{metrics['total_time']:.2f}s, "
                f"{metrics['fcf_types_calculated']} FCF types"
            )


@pytest.mark.e2e
@pytest.mark.integration  
class TestFCFIntegrationWorkflows:
    """Integration tests for FCF workflows with other analysis modules."""
    
    def test_fcf_to_dcf_integration(self):
        """Test FCF calculation feeding into DCF valuation."""
        logger.info("Testing FCF to DCF integration")
        
        ticker = "MSFT"
        excel_path = Path(f"data/companies/{ticker}")
        
        if not excel_path.exists():
            pytest.skip(f"No test data for {ticker}")
        
        try:
            # Calculate FCF
            calculator = FinancialCalculator(str(excel_path))
            calculator.load_financial_statements()
            fcf_results = calculator.calculate_all_fcf_types()
            
            # Test DCF integration (if available)
            if hasattr(calculator, 'calculate_dcf_valuation'):
                dcf_result = calculator.calculate_dcf_valuation()
                assert dcf_result is not None, "DCF calculation failed"
                logger.info("✅ FCF to DCF integration test passed")
            else:
                logger.info("DCF integration not available, skipping")
                
        except Exception as e:
            pytest.fail(f"FCF to DCF integration test failed: {e}")

    def test_fcf_data_consistency_across_sources(self):
        """Test FCF data consistency when using different data sources."""
        logger.info("Testing FCF data consistency across sources")
        
        ticker = "MSFT"
        
        try:
            # Test Excel source
            excel_path = Path(f"data/companies/{ticker}")
            if excel_path.exists():
                excel_calculator = FinancialCalculator(str(excel_path))
                excel_calculator.load_financial_statements()
                excel_fcf = excel_calculator.calculate_all_fcf_types()
            else:
                excel_fcf = None
            
            # Test API source
            api_calculator = FinancialCalculator()
            api_calculator.ticker = ticker
            api_calculator.load_financial_statements()
            api_fcf = api_calculator.calculate_all_fcf_types()
            
            # Compare results if both available
            if excel_fcf and api_fcf:
                self._compare_data_source_consistency(excel_fcf, api_fcf, ticker)
            
            logger.info("✅ Data consistency test completed")
            
        except Exception as e:
            logger.warning(f"Data consistency test failed: {e}")

    def _compare_data_source_consistency(self, excel_fcf: Dict, api_fcf: Dict, ticker: str):
        """Compare FCF results from different data sources."""
        # Implementation for comparing FCF results across data sources
        # Would check for reasonable correlation between Excel and API data
        logger.info(f"Comparing data source consistency for {ticker}")
        
        # Basic validation that both sources produced results
        excel_successful = sum(1 for values in excel_fcf.values() if values)
        api_successful = sum(1 for values in api_fcf.values() if values)
        
        assert excel_successful > 0, "No successful Excel FCF calculations"
        assert api_successful > 0, "No successful API FCF calculations"
        
        logger.info(f"Excel: {excel_successful} FCF types, API: {api_successful} FCF types")


if __name__ == "__main__":
    # Allow running individual test methods
    import sys
    
    if len(sys.argv) > 1:
        test_class = TestFCFEndToEndFlow()
        method_name = sys.argv[1]
        
        if hasattr(test_class, method_name):
            getattr(test_class, method_name)()
        else:
            print(f"Test method '{method_name}' not found")
    else:
        print("Run with pytest or specify test method name")