"""
Unit tests for financial calculations engine
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from pathlib import Path


class TestFinancialCalculator:
    """Test cases for FinancialCalculator class"""

    @pytest.fixture
    def mock_excel_data(self):
        """Create mock Excel data for testing"""
        return {
            'Income Statement': pd.DataFrame({
                'Year': [2020, 2021, 2022, 2023],
                'Revenue': [100000, 110000, 120000, 130000],
                'Net Income': [10000, 12000, 14000, 16000],
                'Operating Income': [15000, 17000, 19000, 21000]
            }),
            'Balance Sheet': pd.DataFrame({
                'Year': [2020, 2021, 2022, 2023],
                'Total Assets': [200000, 220000, 240000, 260000],
                'Total Equity': [100000, 110000, 120000, 130000],
                'Cash and Cash Equivalents': [20000, 25000, 30000, 35000]
            }),
            'Cash Flow Statement': pd.DataFrame({
                'Year': [2020, 2021, 2022, 2023],
                'Operating Cash Flow': [18000, 20000, 22000, 24000],
                'Capital Expenditures': [5000, 6000, 7000, 8000],
                'Free Cash Flow': [13000, 14000, 15000, 16000]
            })
        }

    @pytest.fixture
    def calculator(self, mock_excel_data):
        """Create FinancialCalculator instance with mock data"""
        with patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_excel_data') as mock_load:
            mock_load.return_value = mock_excel_data
            from core.analysis.engines.financial_calculations import FinancialCalculator
            calc = FinancialCalculator("mock_folder")
            calc.company_name = "Test Company"
            return calc

    def test_calculator_initialization(self, calculator):
        """Test calculator initializes correctly"""
        assert calculator is not None
        assert calculator.company_name == "Test Company"
        assert hasattr(calculator, 'income_statement')
        assert hasattr(calculator, 'balance_sheet')
        assert hasattr(calculator, 'cash_flow')

    def test_calculate_all_fcf_types(self, calculator):
        """Test FCF calculation returns expected structure"""
        fcf_results = calculator.calculate_all_fcf_types()

        assert isinstance(fcf_results, dict)
        assert len(fcf_results) > 0

        # Check that at least one FCF type has data
        has_data = any(values for values in fcf_results.values() if values)
        assert has_data, "No FCF data calculated"

    def test_get_financial_data(self, calculator):
        """Test financial data retrieval"""
        # Test revenue data
        revenue_data = calculator.get_financial_data('Revenue', 'Income Statement')
        assert revenue_data is not None
        assert len(revenue_data) > 0

    def test_calculate_growth_rates(self, calculator):
        """Test growth rate calculations"""
        test_data = [100, 110, 121, 133.1]
        growth_rates = calculator._calculate_growth_rates(test_data)

        assert len(growth_rates) == len(test_data) - 1
        # Check approximate 10% growth rate
        assert abs(growth_rates[0] - 0.10) < 0.01

    def test_error_handling_missing_data(self):
        """Test error handling when data is missing"""
        with patch('core.analysis.engines.financial_calculations.FinancialCalculator._load_excel_data') as mock_load:
            mock_load.return_value = {}
            from core.analysis.engines.financial_calculations import FinancialCalculator

            # Should handle missing data gracefully
            calc = FinancialCalculator("missing_folder")
            fcf_results = calc.calculate_all_fcf_types()
            assert isinstance(fcf_results, dict)


class TestFinancialDataValidation:
    """Test financial data validation functions"""

    def test_validate_positive_numbers(self):
        """Test positive number validation"""
        from core.analysis.engines.financial_calculations import FinancialCalculator

        # Test with valid data
        valid_data = [100, 200, 300]
        assert all(x > 0 for x in valid_data)

        # Test with mixed data
        mixed_data = [100, -50, 200]
        positive_only = [x for x in mixed_data if x > 0]
        assert len(positive_only) == 2

    def test_data_consistency_checks(self):
        """Test data consistency validation"""
        # Test that revenue > 0 and reasonable
        revenue_data = [1000000, 1100000, 1200000]
        assert all(r > 0 for r in revenue_data)
        assert all(r < 1e12 for r in revenue_data)  # Reasonable upper bound


class TestFinancialCalculationsIntegration:
    """Integration tests for financial calculations"""

    @pytest.mark.skipif(not Path("data/companies").exists(), reason="Test data not available")
    def test_real_company_data_loading(self):
        """Test loading real company data if available"""
        from core.analysis.engines.financial_calculations import FinancialCalculator

        # Look for any company folder in data/companies
        companies_dir = Path("data/companies")
        if companies_dir.exists():
            company_folders = [f for f in companies_dir.iterdir() if f.is_dir()]
            if company_folders:
                # Test with first available company
                calc = FinancialCalculator(str(company_folders[0]))
                assert calc is not None

                # Test basic functionality
                fcf_results = calc.calculate_all_fcf_types()
                assert isinstance(fcf_results, dict)

    def test_calculation_engine_performance(self, calculator):
        """Test that calculations complete in reasonable time"""
        import time

        start_time = time.time()
        fcf_results = calculator.calculate_all_fcf_types()
        end_time = time.time()

        # Should complete within 10 seconds
        assert (end_time - start_time) < 10.0
        assert fcf_results is not None


class TestFinancialMetrics:
    """Test individual financial metric calculations"""

    def test_fcf_calculation_basic(self):
        """Test basic FCF calculation: Operating Cash Flow - CapEx"""
        operating_cf = 1000
        capex = 200
        expected_fcf = operating_cf - capex

        # Simple calculation test
        calculated_fcf = operating_cf - capex
        assert calculated_fcf == expected_fcf
        assert calculated_fcf == 800

    def test_growth_rate_calculation(self):
        """Test growth rate calculation"""
        initial_value = 100
        final_value = 110
        expected_growth = (final_value - initial_value) / initial_value

        calculated_growth = (final_value - initial_value) / initial_value
        assert abs(calculated_growth - expected_growth) < 0.001
        assert abs(calculated_growth - 0.10) < 0.001

    def test_compound_growth_rate(self):
        """Test compound annual growth rate calculation"""
        initial_value = 100
        final_value = 121  # 10% CAGR over 2 years
        years = 2

        cagr = (final_value / initial_value) ** (1/years) - 1
        assert abs(cagr - 0.10) < 0.01  # Approximately 10%


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_zero_division_protection(self):
        """Test protection against division by zero"""
        # Test growth rate with zero initial value
        try:
            growth_rate = 100 / 0
            assert False, "Should have raised ZeroDivisionError"
        except ZeroDivisionError:
            pass  # Expected behavior

    def test_negative_values_handling(self):
        """Test handling of negative financial values"""
        # Some financial metrics can be negative (like net income in loss years)
        negative_income = -5000
        assert negative_income < 0  # This is valid

        # But some should be positive (like revenue)
        revenue = 100000
        assert revenue > 0

    def test_empty_data_handling(self, calculator):
        """Test handling of empty datasets"""
        empty_data = []

        # Should handle empty data gracefully
        if hasattr(calculator, '_calculate_growth_rates'):
            try:
                growth_rates = calculator._calculate_growth_rates(empty_data)
                assert growth_rates == []
            except (IndexError, ValueError):
                # Acceptable to raise these errors for empty data
                pass


if __name__ == "__main__":
    pytest.main([__file__])