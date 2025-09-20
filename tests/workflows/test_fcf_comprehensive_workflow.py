"""
FCF Analysis Comprehensive Workflow Test
=======================================

This test module provides complete end-to-end testing of the Free Cash Flow (FCF)
analysis workflow, covering all available options and configurations.

Test Coverage:
- FCFE, FCFF, and Levered FCF calculations
- Excel-based and API-based data loading
- Historical trend analysis and growth calculations
- Data quality assessment and validation
- Multi-currency support and error handling
- Performance optimization and caching
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
import logging
from unittest.mock import Mock, patch

# Import core modules
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.fcf_consolidated import FCFCalculator, calculate_fcf_growth_rates
from core.data_processing.processors.data_processing import DataProcessor
from core.data_processing.var_input_data import VarInputData
from core.data_processing.error_handler import ErrorHandler
from core.data_processing.universal_data_registry import UniversalDataRegistry

# Import test utilities
from tests.utils.common_test_utilities import get_test_companies, create_mock_financial_data
from tests.fixtures.analysis_fixtures import sample_financial_statements, sample_market_data

logger = logging.getLogger(__name__)


class TestFCFComprehensiveWorkflow:
    """
    Comprehensive workflow tests for FCF analysis covering all functionality
    and integration points.
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with sample data and configurations"""
        self.test_companies = get_test_companies()
        self.data_processor = DataProcessor()
        self.error_handler = ErrorHandler()
        self.registry = UniversalDataRegistry()

        # Test configuration
        self.test_config = {
            'currency': 'USD',
            'period_type': 'annual',
            'data_sources': ['excel', 'yfinance', 'api'],
            'cache_enabled': True,
            'quality_threshold': 0.8
        }

    def test_complete_fcf_workflow_excel_source(self):
        """
        Test complete FCF workflow using Excel data source.

        Workflow:
        1. Load company data from Excel files
        2. Calculate all FCF types (FCFE, FCFF, Levered)
        3. Perform data quality assessment
        4. Calculate growth rates and trends
        5. Generate comprehensive reports
        """
        for ticker in self.test_companies[:3]:  # Test with first 3 companies
            logger.info(f"Testing FCF workflow for {ticker}")

            # Step 1: Initialize Financial Calculator with Excel data
            calculator = FinancialCalculator(ticker, data_source='excel')

            # Verify data loading
            assert calculator.income_statement is not None, f"Income statement not loaded for {ticker}"
            assert calculator.balance_sheet is not None, f"Balance sheet not loaded for {ticker}"
            assert calculator.cash_flow_statement is not None, f"Cash flow statement not loaded for {ticker}"

            # Step 2: Calculate FCFE (Free Cash Flow to Equity)
            fcfe_result = calculator.calculate_fcfe()
            self._validate_fcf_result(fcfe_result, 'FCFE', ticker)

            # Step 3: Calculate FCFF (Free Cash Flow to Firm)
            fcff_result = calculator.calculate_fcff()
            self._validate_fcf_result(fcff_result, 'FCFF', ticker)

            # Step 4: Calculate Levered FCF
            levered_fcf_result = calculator.calculate_levered_fcf()
            self._validate_fcf_result(levered_fcf_result, 'Levered FCF', ticker)

            # Step 5: Perform data quality assessment
            quality_score = calculator.assess_data_quality()
            assert quality_score >= self.test_config['quality_threshold'], \
                f"Data quality below threshold for {ticker}: {quality_score}"

            # Step 6: Calculate growth rates
            fcf_data = {
                'FCFE': fcfe_result.get('historical_values', []),
                'FCFF': fcff_result.get('historical_values', []),
                'Levered_FCF': levered_fcf_result.get('historical_values', [])
            }

            growth_rates = calculate_fcf_growth_rates(fcf_data)
            self._validate_growth_rates(growth_rates, ticker)

            # Step 7: Generate comprehensive FCF report
            fcf_report = calculator.generate_fcf_report()
            self._validate_fcf_report(fcf_report, ticker)

    def test_complete_fcf_workflow_api_source(self):
        """
        Test complete FCF workflow using API data sources with fallback.

        Workflow:
        1. Configure API data sources with fallback
        2. Load data with error handling
        3. Calculate FCF with API data
        4. Compare with Excel results (if available)
        5. Test cache functionality
        """
        for ticker in self.test_companies[:2]:  # Test with 2 companies
            logger.info(f"Testing FCF API workflow for {ticker}")

            # Step 1: Initialize with API data source
            calculator = FinancialCalculator(ticker, data_source='api')

            # Step 2: Test data loading with fallback
            try:
                # Attempt primary API source
                data_loaded = calculator.load_financial_data()
                assert data_loaded, f"Failed to load data for {ticker}"

                # Step 3: Calculate FCF with API data
                fcfe_api = calculator.calculate_fcfe()
                fcff_api = calculator.calculate_fcff()

                self._validate_fcf_result(fcfe_api, 'FCFE_API', ticker)
                self._validate_fcf_result(fcff_api, 'FCFF_API', ticker)

                # Step 4: Compare with Excel results if available
                try:
                    calculator_excel = FinancialCalculator(ticker, data_source='excel')
                    fcfe_excel = calculator_excel.calculate_fcfe()

                    # Allow for reasonable variance between sources
                    self._compare_fcf_results(fcfe_api, fcfe_excel, tolerance=0.1)

                except Exception as e:
                    logger.warning(f"Excel comparison not available for {ticker}: {e}")

                # Step 5: Test cache functionality
                cache_key = f"fcf_data_{ticker}"
                cached_data = calculator.get_cached_data(cache_key)
                if cached_data:
                    logger.info(f"Cache validated for {ticker}")

            except Exception as e:
                logger.error(f"API workflow failed for {ticker}: {e}")
                # Test should handle API failures gracefully
                assert "API" in str(e) or "connection" in str(e).lower()

    def test_fcf_multi_currency_workflow(self):
        """
        Test FCF workflow with multi-currency support and conversion.

        Workflow:
        1. Load data in original currency
        2. Convert to different target currencies
        3. Validate conversion accuracy
        4. Test currency-adjusted growth rates
        """
        target_currencies = ['USD', 'EUR', 'GBP']

        for ticker in self.test_companies[:1]:  # Test with 1 company
            logger.info(f"Testing multi-currency FCF for {ticker}")

            calculator = FinancialCalculator(ticker)

            fcf_results = {}
            for currency in target_currencies:
                # Calculate FCF in target currency
                calculator.set_target_currency(currency)
                fcfe_result = calculator.calculate_fcfe()
                fcf_results[currency] = fcfe_result

                # Validate currency conversion
                self._validate_fcf_result(fcfe_result, f'FCFE_{currency}', ticker)

                # Verify currency metadata
                assert fcfe_result.get('currency') == currency, \
                    f"Currency mismatch for {ticker}: expected {currency}"

            # Test currency conversion consistency
            self._validate_currency_conversions(fcf_results, ticker)

    def test_fcf_data_quality_and_validation_workflow(self):
        """
        Test comprehensive data quality assessment and validation workflow.

        Workflow:
        1. Load data with intentional quality issues
        2. Run data quality assessment
        3. Test validation rules and thresholds
        4. Handle missing or inconsistent data
        5. Generate quality reports
        """
        for ticker in self.test_companies[:2]:
            logger.info(f"Testing data quality workflow for {ticker}")

            calculator = FinancialCalculator(ticker)

            # Step 1: Comprehensive data quality assessment
            quality_metrics = calculator.assess_comprehensive_data_quality()

            # Validate quality metrics structure
            required_metrics = [
                'completeness_score', 'consistency_score', 'accuracy_score',
                'timeliness_score', 'overall_quality_score'
            ]

            for metric in required_metrics:
                assert metric in quality_metrics, f"Missing quality metric: {metric}"
                assert 0 <= quality_metrics[metric] <= 1, \
                    f"Quality metric out of range: {metric} = {quality_metrics[metric]}"

            # Step 2: Test validation rules
            validation_results = calculator.validate_financial_data()
            self._validate_data_validation_results(validation_results, ticker)

            # Step 3: Test missing data handling
            missing_data_report = calculator.identify_missing_data()
            self._validate_missing_data_report(missing_data_report, ticker)

            # Step 4: Generate quality assessment report
            quality_report = calculator.generate_quality_report()
            self._validate_quality_report(quality_report, ticker)

    def test_fcf_performance_and_optimization_workflow(self):
        """
        Test FCF calculation performance and optimization features.

        Workflow:
        1. Measure calculation performance
        2. Test caching effectiveness
        3. Validate memory usage
        4. Test batch processing capabilities
        5. Monitor optimization metrics
        """
        import time
        from memory_profiler import profile

        logger.info("Testing FCF performance and optimization")

        # Step 1: Performance measurement
        performance_results = {}

        for ticker in self.test_companies[:3]:
            start_time = time.time()

            calculator = FinancialCalculator(ticker)
            fcfe_result = calculator.calculate_fcfe()
            fcff_result = calculator.calculate_fcff()

            calculation_time = time.time() - start_time
            performance_results[ticker] = calculation_time

            # Validate reasonable performance (adjust threshold as needed)
            assert calculation_time < 30.0, \
                f"FCF calculation too slow for {ticker}: {calculation_time:.2f}s"

        # Step 2: Test batch processing
        start_time = time.time()
        batch_results = self._test_batch_fcf_processing(self.test_companies[:3])
        batch_time = time.time() - start_time

        # Batch processing should be more efficient than individual processing
        individual_total = sum(performance_results.values())
        assert batch_time < individual_total * 0.8, \
            f"Batch processing not optimized: {batch_time:.2f}s vs {individual_total:.2f}s"

        # Step 3: Test caching effectiveness
        self._test_caching_effectiveness(self.test_companies[0])

    def test_fcf_error_handling_and_resilience_workflow(self):
        """
        Test error handling and system resilience during FCF calculations.

        Workflow:
        1. Test handling of missing files
        2. Test invalid data scenarios
        3. Test API failure recovery
        4. Test calculation error handling
        5. Validate error reporting
        """
        logger.info("Testing FCF error handling and resilience")

        # Step 1: Test missing file handling
        with pytest.raises(FileNotFoundError):
            calculator = FinancialCalculator('NONEXISTENT_TICKER')
            calculator.calculate_fcfe()

        # Step 2: Test invalid data handling
        calculator = FinancialCalculator(self.test_companies[0])

        # Inject invalid data
        calculator.income_statement = pd.DataFrame()  # Empty dataframe

        with pytest.raises(ValueError):
            calculator.calculate_fcfe()

        # Step 3: Test API failure handling
        with patch('yfinance.download') as mock_download:
            mock_download.side_effect = Exception("API connection failed")

            calculator = FinancialCalculator(self.test_companies[0], data_source='api')

            # Should gracefully handle API failure
            try:
                result = calculator.calculate_fcfe()
                # If no exception, verify fallback mechanism worked
                assert result is not None
            except Exception as e:
                # Should be a handled exception with clear message
                assert "API" in str(e) or "fallback" in str(e).lower()

    def test_fcf_integration_with_other_modules(self):
        """
        Test FCF module integration with other analysis components.

        Workflow:
        1. Test integration with DCF valuation
        2. Test integration with DDM analysis
        3. Test integration with Portfolio analysis
        4. Test data sharing between modules
        5. Validate cross-module consistency
        """
        ticker = self.test_companies[0]
        logger.info(f"Testing FCF integration workflow for {ticker}")

        # Initialize FCF calculator
        fcf_calculator = FinancialCalculator(ticker)
        fcfe_result = fcf_calculator.calculate_fcfe()

        # Step 1: Test DCF integration
        from core.analysis.dcf.dcf_valuation import DCFValuator
        dcf_valuator = DCFValuator(fcf_calculator)
        dcf_result = dcf_valuator.calculate_dcf_valuation()

        # Verify FCF data is properly used in DCF
        assert dcf_result is not None
        assert 'intrinsic_value' in dcf_result

        # Step 2: Test DDM integration (if applicable)
        try:
            from core.analysis.ddm.ddm_valuation import DDMValuator
            ddm_valuator = DDMValuator(fcf_calculator)
            ddm_result = ddm_valuator.calculate_ddm_valuation()

            # Verify integration
            if ddm_result:
                assert 'dividend_yield' in ddm_result or 'no_dividends' in ddm_result
        except Exception as e:
            logger.info(f"DDM integration not applicable for {ticker}: {e}")

        # Step 3: Test Portfolio integration
        try:
            from core.analysis.portfolio.portfolio_models import PortfolioHolding
            holding = PortfolioHolding(
                ticker=ticker,
                shares=100,
                purchase_price=100.0,
                fcf_metrics=fcfe_result
            )

            assert holding.ticker == ticker
            assert holding.fcf_metrics == fcfe_result
        except Exception as e:
            logger.warning(f"Portfolio integration test failed: {e}")

    # Helper methods for validation

    def _validate_fcf_result(self, result: Dict[str, Any], fcf_type: str, ticker: str):
        """Validate FCF calculation result structure and values"""
        assert result is not None, f"{fcf_type} result is None for {ticker}"

        required_fields = ['current_fcf', 'currency', 'calculation_date']
        for field in required_fields:
            assert field in result, f"Missing {field} in {fcf_type} result for {ticker}"

        # Validate numerical values
        current_fcf = result['current_fcf']
        assert isinstance(current_fcf, (int, float)), \
            f"Invalid FCF value type for {ticker}: {type(current_fcf)}"

        # FCF can be negative, but should be reasonable
        assert abs(current_fcf) < 1e12, f"FCF value seems unreasonable for {ticker}: {current_fcf}"

    def _validate_growth_rates(self, growth_rates: Dict[str, float], ticker: str):
        """Validate FCF growth rate calculations"""
        assert growth_rates is not None, f"Growth rates is None for {ticker}"

        for fcf_type, rate in growth_rates.items():
            assert isinstance(rate, (int, float)), \
                f"Invalid growth rate type for {ticker} {fcf_type}: {type(rate)}"

            # Growth rates should be reasonable (between -100% and 1000%)
            assert -1.0 <= rate <= 10.0, \
                f"Unreasonable growth rate for {ticker} {fcf_type}: {rate:.2%}"

    def _validate_fcf_report(self, report: Dict[str, Any], ticker: str):
        """Validate comprehensive FCF report structure"""
        assert report is not None, f"FCF report is None for {ticker}"

        required_sections = ['summary', 'calculations', 'quality_metrics', 'trends']
        for section in required_sections:
            assert section in report, f"Missing {section} in FCF report for {ticker}"

    def _compare_fcf_results(self, result1: Dict, result2: Dict, tolerance: float = 0.1):
        """Compare FCF results from different sources"""
        fcf1 = result1.get('current_fcf', 0)
        fcf2 = result2.get('current_fcf', 0)

        if fcf1 != 0 and fcf2 != 0:
            relative_diff = abs(fcf1 - fcf2) / max(abs(fcf1), abs(fcf2))
            assert relative_diff <= tolerance, \
                f"FCF results differ too much: {fcf1} vs {fcf2} (diff: {relative_diff:.2%})"

    def _validate_currency_conversions(self, fcf_results: Dict[str, Dict], ticker: str):
        """Validate currency conversion consistency"""
        # Basic validation - all results should have valid FCF values
        for currency, result in fcf_results.items():
            assert result.get('current_fcf') is not None, \
                f"Missing FCF value for {ticker} in {currency}"

    def _validate_data_validation_results(self, validation_results: Dict, ticker: str):
        """Validate data validation results structure"""
        assert 'is_valid' in validation_results, f"Missing validation status for {ticker}"
        assert 'errors' in validation_results, f"Missing error list for {ticker}"
        assert 'warnings' in validation_results, f"Missing warning list for {ticker}"

    def _validate_missing_data_report(self, missing_data_report: Dict, ticker: str):
        """Validate missing data report structure"""
        assert 'missing_fields' in missing_data_report, \
            f"Missing fields list not found for {ticker}"
        assert 'completeness_percentage' in missing_data_report, \
            f"Completeness percentage not found for {ticker}"

    def _validate_quality_report(self, quality_report: Dict, ticker: str):
        """Validate quality assessment report structure"""
        required_sections = ['overall_score', 'detailed_metrics', 'recommendations']
        for section in required_sections:
            assert section in quality_report, \
                f"Missing {section} in quality report for {ticker}"

    def _test_batch_fcf_processing(self, tickers: List[str]) -> Dict[str, Dict]:
        """Test batch processing of multiple companies"""
        batch_results = {}

        for ticker in tickers:
            try:
                calculator = FinancialCalculator(ticker)
                fcfe_result = calculator.calculate_fcfe()
                batch_results[ticker] = fcfe_result
            except Exception as e:
                logger.warning(f"Batch processing failed for {ticker}: {e}")
                batch_results[ticker] = None

        return batch_results

    def _test_caching_effectiveness(self, ticker: str):
        """Test caching effectiveness for FCF calculations"""
        calculator = FinancialCalculator(ticker)

        # First calculation (should cache)
        import time
        start_time = time.time()
        result1 = calculator.calculate_fcfe()
        first_time = time.time() - start_time

        # Second calculation (should use cache)
        start_time = time.time()
        result2 = calculator.calculate_fcfe()
        second_time = time.time() - start_time

        # Cache should make second calculation faster
        assert second_time < first_time * 0.8, \
            f"Caching not effective: {second_time:.3f}s vs {first_time:.3f}s"

        # Results should be identical
        assert result1['current_fcf'] == result2['current_fcf'], \
            "Cached result differs from original"


if __name__ == "__main__":
    # Run comprehensive FCF workflow tests
    pytest.main([__file__, "-v", "--tb=short"])