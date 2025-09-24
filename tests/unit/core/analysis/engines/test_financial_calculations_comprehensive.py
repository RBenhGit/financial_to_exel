"""
Comprehensive Tests for Financial Calculations Engine
=====================================================

This module contains comprehensive unit tests for the core financial calculations engine,
covering all major calculation methods including FCF, DCF, DDM, and P/B valuations.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from typing import Dict, Any, List, Optional

# Import modules under test
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.data_processing.var_input_data import VarInputData
from tests.utils.common_test_utilities import create_mock_financial_data, TestDataGenerator


class TestFinancialCalculatorInitialization:
    """Test FinancialCalculator initialization and setup"""

    def test_calculator_initialization_with_company_folder(self):
        """Test calculator initializes correctly with company folder"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            calculator = FinancialCalculator("data/companies/MSFT")
            assert calculator.company_folder == "data/companies/MSFT"
            assert calculator.company_name == "MSFT"
            assert calculator.financial_data == {}

    def test_calculator_initialization_with_enhanced_data_manager(self):
        """Test calculator initializes with enhanced data manager"""
        mock_enhanced_manager = Mock()
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            calculator = FinancialCalculator("data/companies/TEST", enhanced_data_manager=mock_enhanced_manager)
            assert calculator.company_folder == "data/companies/TEST"
            assert calculator.enhanced_data_manager is mock_enhanced_manager

    def test_calculator_initialization_invalid_folder(self):
        """Test calculator handles invalid folder gracefully"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            calculator = FinancialCalculator(None)
            assert calculator.company_folder is None
            assert calculator.financial_data == {}

    def test_calculator_str_representation(self):
        """Test string representation of calculator"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            calculator = FinancialCalculator("data/companies/AAPL")
            str_repr = str(calculator)
            assert "FinancialCalculator" in str_repr or "AAPL" in str_repr


class TestFCFCalculations:
    """Test Free Cash Flow calculation methods"""

    def setup_method(self):
        """Set up test fixtures"""
        self.test_data = create_mock_financial_data("MSFT")
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            self.calculator = FinancialCalculator("data/companies/MSFT")

    def test_calculate_fcfe_basic(self):
        """Test Free Cash Flow to Equity calculation"""
        # Mock the data retrieval
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'total_cash_flow_from_operating_activities': 100000000000,
                'capital_expenditures': -15000000000,
                'dividends_paid': -5000000000,
                'net_debt_issued': 2000000000
            }

            fcfe = self.calculator.calculate_fcfe()
            expected = 100000000000 - 15000000000 - 5000000000 + 2000000000
            assert abs(fcfe - expected) < 1e6  # Allow for small floating point differences

    def test_calculate_fcff_basic(self):
        """Test Free Cash Flow to Firm calculation"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'total_cash_flow_from_operating_activities': 100000000000,
                'capital_expenditures': -15000000000,
                'interest_expense': 3000000000,
                'tax_rate': 0.21
            }

            fcff = self.calculator.calculate_fcff()
            after_tax_interest = 3000000000 * (1 - 0.21)
            expected = 100000000000 - 15000000000 + after_tax_interest
            assert abs(fcff - expected) < 1e6

    def test_calculate_levered_fcf_basic(self):
        """Test Levered Free Cash Flow calculation"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'total_cash_flow_from_operating_activities': 100000000000,
                'capital_expenditures': -15000000000
            }

            levered_fcf = self.calculator.calculate_levered_fcf()
            expected = 100000000000 - 15000000000
            assert abs(levered_fcf - expected) < 1e6

    def test_calculate_all_fcf_types(self):
        """Test calculation of all FCF types together"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'total_cash_flow_from_operating_activities': 100000000000,
                'capital_expenditures': -15000000000,
                'dividends_paid': -5000000000,
                'net_debt_issued': 2000000000,
                'interest_expense': 3000000000,
                'tax_rate': 0.21
            }

            all_fcf = self.calculator.calculate_all_fcf_types()

            assert 'FCFE' in all_fcf
            assert 'FCFF' in all_fcf
            assert 'Levered_FCF' in all_fcf
            assert all(isinstance(value, (int, float)) for value in all_fcf.values())

    def test_fcf_calculation_with_missing_data(self):
        """Test FCF calculations handle missing data gracefully"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {}

            fcfe = self.calculator.calculate_fcfe()
            fcff = self.calculator.calculate_fcff()
            levered_fcf = self.calculator.calculate_levered_fcf()

            # Should handle missing data gracefully (return None or 0)
            assert fcfe is None or fcfe == 0
            assert fcff is None or fcff == 0
            assert levered_fcf is None or levered_fcf == 0

    def test_fcf_calculation_with_invalid_data_types(self):
        """Test FCF calculations handle invalid data types"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'total_cash_flow_from_operating_activities': 'invalid',
                'capital_expenditures': None
            }

            fcfe = self.calculator.calculate_fcfe()
            assert fcfe is None or fcfe == 0


class TestDCFCalculations:
    """Test Discounted Cash Flow calculation methods"""

    def setup_method(self):
        """Set up test fixtures"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            self.calculator = FinancialCalculator("data/companies/MSFT")

    def test_dcf_valuation_basic(self):
        """Test basic DCF valuation calculation"""
        with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
            mock_fcf.return_value = {
                'FCFE': 50000000000,
                'FCFF': 60000000000,
                'Levered_FCF': 55000000000
            }

            with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
                mock_get_data.return_value = {
                    'shares_outstanding': 7500000000,
                    'market_cap': 2500000000000
                }

                dcf_result = self.calculator.calculate_dcf_valuation(
                    discount_rate=0.10,
                    terminal_growth_rate=0.03,
                    projection_years=5
                )

                assert dcf_result is not None
                assert 'fair_value_per_share' in dcf_result
                assert 'enterprise_value' in dcf_result
                assert isinstance(dcf_result['fair_value_per_share'], (int, float))

    def test_dcf_valuation_with_custom_growth_rates(self):
        """Test DCF valuation with custom growth rates"""
        with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
            mock_fcf.return_value = {'FCFF': 60000000000}

            with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
                mock_get_data.return_value = {
                    'shares_outstanding': 7500000000,
                    'market_cap': 2500000000000
                }

                growth_rates = [0.15, 0.12, 0.10, 0.08, 0.05]
                dcf_result = self.calculator.calculate_dcf_valuation(
                    discount_rate=0.10,
                    terminal_growth_rate=0.03,
                    projection_years=5,
                    growth_rates=growth_rates
                )

                assert dcf_result is not None
                assert len(dcf_result.get('projected_fcf', [])) == 5

    def test_dcf_valuation_error_handling(self):
        """Test DCF valuation error handling"""
        with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
            mock_fcf.return_value = {}  # No FCF data

            dcf_result = self.calculator.calculate_dcf_valuation(
                discount_rate=0.10,
                terminal_growth_rate=0.03,
                projection_years=5
            )

            assert dcf_result is None or 'error' in dcf_result


class TestDDMCalculations:
    """Test Dividend Discount Model calculation methods"""

    def setup_method(self):
        """Set up test fixtures"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            self.calculator = FinancialCalculator("data/companies/MSFT")

    def test_ddm_gordon_growth_basic(self):
        """Test Gordon Growth DDM calculation"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'dividend_per_share': 2.50,
                'dividend_history': [2.00, 2.10, 2.25, 2.40, 2.50]
            }

            ddm_result = self.calculator.calculate_ddm_valuation(
                model_type='gordon_growth',
                required_return=0.12,
                growth_rate=0.05
            )

            assert ddm_result is not None
            assert 'fair_value_per_share' in ddm_result
            expected_value = 2.50 * (1 + 0.05) / (0.12 - 0.05)
            assert abs(ddm_result['fair_value_per_share'] - expected_value) < 0.01

    def test_ddm_two_stage_growth(self):
        """Test Two-Stage DDM calculation"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'dividend_per_share': 2.50,
                'dividend_history': [2.00, 2.10, 2.25, 2.40, 2.50]
            }

            ddm_result = self.calculator.calculate_ddm_valuation(
                model_type='two_stage',
                required_return=0.12,
                growth_rate_stage1=0.10,
                growth_rate_stage2=0.04,
                stage1_years=5
            )

            assert ddm_result is not None
            assert 'fair_value_per_share' in ddm_result
            assert 'stage1_value' in ddm_result
            assert 'stage2_value' in ddm_result

    def test_ddm_multi_stage_growth(self):
        """Test Multi-Stage DDM calculation"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'dividend_per_share': 2.50,
                'dividend_history': [2.00, 2.10, 2.25, 2.40, 2.50]
            }

            growth_rates = [0.15, 0.12, 0.10, 0.08, 0.05]
            ddm_result = self.calculator.calculate_ddm_valuation(
                model_type='multi_stage',
                required_return=0.12,
                growth_rates=growth_rates,
                terminal_growth_rate=0.03
            )

            assert ddm_result is not None
            assert 'fair_value_per_share' in ddm_result
            assert len(ddm_result.get('projected_dividends', [])) == 5

    def test_ddm_with_no_dividend_history(self):
        """Test DDM calculation with no dividend history"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'dividend_per_share': 0,
                'dividend_history': []
            }

            ddm_result = self.calculator.calculate_ddm_valuation(
                model_type='gordon_growth',
                required_return=0.12,
                growth_rate=0.05
            )

            assert ddm_result is None or 'error' in ddm_result


class TestPBCalculations:
    """Test Price-to-Book ratio calculation methods"""

    def setup_method(self):
        """Set up test fixtures"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            self.calculator = FinancialCalculator("data/companies/MSFT")

    def test_pb_ratio_calculation_basic(self):
        """Test basic P/B ratio calculation"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'current_price': 300.00,
                'book_value_per_share': 25.00,
                'total_equity': 200000000000,
                'shares_outstanding': 7500000000
            }

            pb_result = self.calculator.calculate_pb_analysis()

            assert pb_result is not None
            assert 'current_pb_ratio' in pb_result
            assert abs(pb_result['current_pb_ratio'] - 12.0) < 0.1  # 300/25 = 12

    def test_pb_historical_analysis(self):
        """Test P/B historical analysis"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_data = {
                'current_price': 300.00,
                'historical_book_values': {
                    '2023': 200000000000,
                    '2022': 180000000000,
                    '2021': 160000000000,
                    '2020': 150000000000
                },
                'historical_prices': {
                    '2023': 300.00,
                    '2022': 250.00,
                    '2021': 200.00,
                    '2020': 180.00
                },
                'shares_outstanding': 7500000000
            }
            mock_get_data.return_value = mock_data

            pb_result = self.calculator.calculate_pb_analysis(include_historical=True)

            assert pb_result is not None
            assert 'historical_pb_ratios' in pb_result
            assert 'average_pb_ratio' in pb_result
            assert len(pb_result['historical_pb_ratios']) > 0

    def test_pb_fair_value_estimation(self):
        """Test P/B fair value estimation"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'current_price': 300.00,
                'book_value_per_share': 25.00,
                'total_equity': 200000000000,
                'shares_outstanding': 7500000000,
                'roe': 0.15,
                'industry_average_pb': 8.5
            }

            pb_result = self.calculator.calculate_pb_analysis(calculate_fair_value=True)

            assert pb_result is not None
            assert 'estimated_fair_value' in pb_result
            assert 'upside_downside' in pb_result

    def test_pb_with_missing_data(self):
        """Test P/B calculation with missing data"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'current_price': None,
                'book_value_per_share': None
            }

            pb_result = self.calculator.calculate_pb_analysis()

            assert pb_result is None or 'error' in pb_result


class TestUtilityMethods:
    """Test utility and helper methods"""

    def setup_method(self):
        """Set up test fixtures"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            self.calculator = FinancialCalculator("data/companies/TEST")

    def test_calculate_compound_annual_growth_rate(self):
        """Test CAGR calculation"""
        beginning_value = 1000000000
        ending_value = 1500000000
        years = 5

        cagr = self.calculator._calculate_cagr(beginning_value, ending_value, years)
        expected_cagr = ((ending_value / beginning_value) ** (1/years)) - 1

        assert abs(cagr - expected_cagr) < 0.0001

    def test_calculate_cagr_with_zero_beginning_value(self):
        """Test CAGR calculation with zero beginning value"""
        cagr = self.calculator._calculate_cagr(0, 1500000000, 5)
        assert cagr is None or np.isnan(cagr)

    def test_calculate_cagr_with_negative_years(self):
        """Test CAGR calculation with negative years"""
        cagr = self.calculator._calculate_cagr(1000000000, 1500000000, -5)
        assert cagr is None or np.isnan(cagr)

    def test_present_value_calculation(self):
        """Test present value calculation utility"""
        future_value = 1000000
        discount_rate = 0.10
        periods = 5

        pv = self.calculator._calculate_present_value(future_value, discount_rate, periods)
        expected_pv = future_value / ((1 + discount_rate) ** periods)

        assert abs(pv - expected_pv) < 0.01

    def test_format_large_numbers(self):
        """Test number formatting utility"""
        # Test various number formats
        test_cases = [
            (1000, "1.0K"),
            (1000000, "1.0M"),
            (1000000000, "1.0B"),
            (1500000000, "1.5B"),
            (2500000000000, "2.5T")
        ]

        for number, expected in test_cases:
            if hasattr(self.calculator, '_format_large_number'):
                formatted = self.calculator._format_large_number(number)
                assert formatted == expected

    def test_validate_numeric_inputs(self):
        """Test numeric input validation"""
        if hasattr(self.calculator, '_validate_numeric_input'):
            assert self.calculator._validate_numeric_input(10.5) is True
            assert self.calculator._validate_numeric_input(0) is True
            assert self.calculator._validate_numeric_input(-5.2) is True
            assert self.calculator._validate_numeric_input("not a number") is False
            assert self.calculator._validate_numeric_input(None) is False


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple calculations"""

    def setup_method(self):
        """Set up test fixtures"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            self.calculator = FinancialCalculator("data/companies/MSFT")

    def test_comprehensive_valuation_analysis(self):
        """Test comprehensive valuation using multiple methods"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                # FCF data
                'total_cash_flow_from_operating_activities': 100000000000,
                'capital_expenditures': -15000000000,
                'dividends_paid': -5000000000,

                # Market data
                'shares_outstanding': 7500000000,
                'current_price': 300.00,
                'market_cap': 2250000000000,

                # Dividend data
                'dividend_per_share': 2.50,
                'dividend_history': [2.00, 2.10, 2.25, 2.40, 2.50],

                # Book value data
                'book_value_per_share': 25.00,
                'total_equity': 187500000000,
                'roe': 0.15
            }

            # Calculate FCF
            fcf_results = self.calculator.calculate_all_fcf_types()
            assert fcf_results is not None

            # Calculate DCF
            dcf_results = self.calculator.calculate_dcf_valuation(
                discount_rate=0.10,
                terminal_growth_rate=0.03,
                projection_years=5
            )
            assert dcf_results is not None

            # Calculate DDM
            ddm_results = self.calculator.calculate_ddm_valuation(
                model_type='gordon_growth',
                required_return=0.12,
                growth_rate=0.05
            )
            assert ddm_results is not None

            # Calculate P/B
            pb_results = self.calculator.calculate_pb_analysis()
            assert pb_results is not None

    def test_edge_case_scenarios(self):
        """Test edge case scenarios"""
        test_cases = [
            # High growth company
            {
                'total_cash_flow_from_operating_activities': 10000000000,
                'capital_expenditures': -8000000000,
                'shares_outstanding': 1000000000,
                'current_price': 150.00
            },
            # Low margin company
            {
                'total_cash_flow_from_operating_activities': 50000000000,
                'capital_expenditures': -45000000000,
                'shares_outstanding': 10000000000,
                'current_price': 10.00
            }
        ]

        for case_data in test_cases:
            with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
                mock_get_data.return_value = case_data

                fcf_results = self.calculator.calculate_all_fcf_types()
                assert fcf_results is not None


class TestDataIntegration:
    """Test data integration with VarInputData system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.var_input_data = Mock(spec=VarInputData)
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            self.calculator = FinancialCalculator("data/companies/TEST", enhanced_data_manager=self.var_input_data)

    def test_var_input_data_integration(self):
        """Test integration with VarInputData system"""
        # Mock VarInputData methods
        self.var_input_data.get_variable.side_effect = lambda var: {
            'total_cash_flow_from_operating_activities': 100000000000,
            'capital_expenditures': -15000000000,
            'shares_outstanding': 7500000000
        }.get(var, None)

        # Test that calculator uses VarInputData
        if hasattr(self.calculator, '_get_from_var_input_data'):
            result = self.calculator._get_from_var_input_data('total_cash_flow_from_operating_activities')
            assert result == 100000000000

    def test_data_source_fallback(self):
        """Test fallback between data sources"""
        # Test that calculator handles missing data gracefully
        self.var_input_data.get_variable.return_value = None

        with patch.object(self.calculator, '_get_financial_data') as mock_fallback:
            mock_fallback.return_value = {'total_cash_flow_from_operating_activities': 50000000000}

            # Calculator should fall back to alternative data source
            fcf = self.calculator.calculate_levered_fcf()
            assert fcf is not None


class TestErrorHandlingAndValidation:
    """Test error handling and input validation"""

    def setup_method(self):
        """Set up test fixtures"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Prevent auto-loading
            self.calculator = FinancialCalculator("data/companies/TEST")

    def test_invalid_discount_rate(self):
        """Test DCF calculation with invalid discount rate"""
        with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
            mock_fcf.return_value = {'FCFF': 60000000000}

            # Test negative discount rate
            dcf_result = self.calculator.calculate_dcf_valuation(
                discount_rate=-0.05,
                terminal_growth_rate=0.03,
                projection_years=5
            )
            assert dcf_result is None or 'error' in dcf_result

            # Test discount rate <= terminal growth rate
            dcf_result = self.calculator.calculate_dcf_valuation(
                discount_rate=0.02,
                terminal_growth_rate=0.03,
                projection_years=5
            )
            assert dcf_result is None or 'error' in dcf_result

    def test_invalid_projection_years(self):
        """Test DCF calculation with invalid projection years"""
        with patch.object(self.calculator, 'calculate_all_fcf_types') as mock_fcf:
            mock_fcf.return_value = {'FCFF': 60000000000}

            # Test zero projection years
            dcf_result = self.calculator.calculate_dcf_valuation(
                discount_rate=0.10,
                terminal_growth_rate=0.03,
                projection_years=0
            )
            assert dcf_result is None or 'error' in dcf_result

            # Test negative projection years
            dcf_result = self.calculator.calculate_dcf_valuation(
                discount_rate=0.10,
                terminal_growth_rate=0.03,
                projection_years=-5
            )
            assert dcf_result is None or 'error' in dcf_result

    def test_division_by_zero_handling(self):
        """Test handling of division by zero scenarios"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'dividend_per_share': 2.50,
                'shares_outstanding': 0  # Division by zero scenario
            }

            # Should handle gracefully without crashing
            pb_result = self.calculator.calculate_pb_analysis()
            assert pb_result is None or 'error' in pb_result

    def test_data_type_validation(self):
        """Test data type validation"""
        with patch.object(self.calculator, '_get_financial_data') as mock_get_data:
            mock_get_data.return_value = {
                'total_cash_flow_from_operating_activities': "invalid_string",
                'capital_expenditures': None,
                'shares_outstanding': "7500000000"  # String instead of number
            }

            # Should handle invalid data types gracefully
            fcf_result = self.calculator.calculate_all_fcf_types()
            assert fcf_result is not None  # Should return something, even if error


if __name__ == "__main__":
    pytest.main([__file__])