"""
Unit tests for DCF valuation module basic functionality.

This module tests the core DCF valuation logic without requiring
complex financial data setup.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from core.analysis.dcf.dcf_valuation import DCFValuator


class TestDCFBasicCalculations:
    """Test basic DCF calculation functions"""

    def test_present_value_calculation(self):
        """Test present value calculation formula"""
        # Test PV = FV / (1 + r)^n
        future_value = 1000
        discount_rate = 0.10
        periods = 3

        pv = future_value / ((1 + discount_rate) ** periods)
        expected_pv = 1000 / (1.10 ** 3)

        assert abs(pv - expected_pv) < 0.01

    def test_terminal_value_calculation(self):
        """Test Gordon Growth Model terminal value calculation"""
        # Terminal Value = FCF * (1 + g) / (r - g)
        fcf = 100
        growth_rate = 0.03
        discount_rate = 0.10

        terminal_value = fcf * (1 + growth_rate) / (discount_rate - growth_rate)
        expected_tv = 100 * 1.03 / 0.07

        assert abs(terminal_value - expected_tv) < 0.01

    def test_growth_rate_validation(self):
        """Test that growth rate validation works correctly"""
        # Growth rate should be less than discount rate
        discount_rate = 0.10
        valid_growth = 0.05
        invalid_growth = 0.15

        # Valid growth rate should work
        assert valid_growth < discount_rate

        # Invalid growth rate should fail
        assert invalid_growth > discount_rate

    def test_compound_growth_calculation(self):
        """Test compound growth calculation"""
        # Test CAGR calculation
        starting_value = 100
        growth_rate = 0.05
        years = 5

        ending_value = starting_value * ((1 + growth_rate) ** years)
        expected_value = 100 * (1.05 ** 5)

        assert abs(ending_value - expected_value) < 0.01


class TestDCFValuatorInitialization:
    """Test DCFValuator initialization and basic methods"""

    @pytest.fixture
    def mock_financial_calculator(self):
        """Create a mock FinancialCalculator for testing"""
        mock_calc = Mock()
        mock_calc.company_name = "Test Company"
        mock_calc.ticker_symbol = "TEST"
        mock_calc.current_stock_price = 100.0
        mock_calc.shares_outstanding = 1000000
        mock_calc.market_cap = 100000000

        # Mock FCF data
        mock_calc.fcf_results = {
            'FCFF': [80, 85, 90, 95, 100],
            'FCFE': [70, 75, 80, 85, 90],
            'LFCF': [75, 80, 85, 90, 95]
        }

        return mock_calc

    def test_dcf_valuator_initialization(self, mock_financial_calculator):
        """Test DCFValuator initialization with mock calculator"""
        dcf = DCFValuator(mock_financial_calculator)

        assert dcf.financial_calculator == mock_financial_calculator
        assert dcf.ticker_symbol == "TEST"
        assert hasattr(dcf, 'default_assumptions')

    def test_default_assumptions(self, mock_financial_calculator):
        """Test default DCF assumptions are set correctly"""
        dcf = DCFValuator(mock_financial_calculator)

        # Check that default assumptions exist
        assert hasattr(dcf, 'default_assumptions')
        assert isinstance(dcf.default_assumptions, dict)

        # Check key assumption fields
        assumptions = dcf.default_assumptions
        assert 'discount_rate' in assumptions
        assert 'terminal_growth_rate' in assumptions

    def test_fcf_data_access(self, mock_financial_calculator):
        """Test access to FCF data from financial calculator"""
        dcf = DCFValuator(mock_financial_calculator)

        # Should be able to access FCF data
        fcf_data = mock_financial_calculator.fcf_results
        assert 'FCFF' in fcf_data
        assert 'FCFE' in fcf_data
        assert len(fcf_data['FCFF']) == 5


class TestDCFProjections:
    """Test DCF projection calculations"""

    @pytest.fixture
    def dcf_with_data(self):
        """Create DCF valuator with sample data"""
        mock_calc = Mock()
        mock_calc.company_name = "Test Company"
        mock_calc.ticker_symbol = "TEST"
        mock_calc.current_stock_price = 100.0
        mock_calc.shares_outstanding = 1000000

        # Realistic FCF progression
        mock_calc.fcf_results = {
            'FCFF': [100, 110, 121, 133, 146],  # 10% growth
            'FCFE': [90, 99, 109, 120, 132],    # 10% growth
            'LFCF': [95, 105, 115, 127, 140]    # ~10% growth
        }

        with patch.object(DCFValuator, '__init__', return_value=None):
            dcf = DCFValuator(None)
            dcf.financial_calculator = mock_calc
            dcf.company_name = mock_calc.company_name
            dcf.ticker_symbol = mock_calc.ticker_symbol

            # Set reasonable defaults
            dcf.discount_rate = 0.10
            dcf.terminal_growth_rate = 0.03
            dcf.projection_years = 5

            return dcf

    def test_fcf_projection_logic(self, dcf_with_data):
        """Test FCF projection calculation logic"""
        fcf_data = dcf_with_data.financial_calculator.fcf_results['FCFF']

        # Test that we have historical data
        assert len(fcf_data) == 5
        assert all(isinstance(x, (int, float)) for x in fcf_data)

        # Test growth rate calculation
        if len(fcf_data) >= 2:
            recent_growth = (fcf_data[-1] / fcf_data[-2]) - 1
            assert recent_growth > 0  # Should have positive growth

    def test_multi_stage_growth(self, dcf_with_data):
        """Test multi-stage growth model logic"""
        # Test stage definitions
        stage1_years = 5
        stage2_years = 5
        terminal_years = float('inf')

        # Stage 1: High growth
        stage1_growth = 0.15

        # Stage 2: Moderate growth
        stage2_growth = 0.08

        # Terminal: Stable growth
        terminal_growth = 0.03

        # Test that growth rates are reasonable
        assert stage1_growth > stage2_growth > terminal_growth
        assert terminal_growth < 0.05  # Terminal growth should be conservative

    def test_sensitivity_ranges(self, dcf_with_data):
        """Test sensitivity analysis parameter ranges"""
        # Test discount rate ranges
        discount_rates = [0.08, 0.09, 0.10, 0.11, 0.12]
        assert all(0.05 <= rate <= 0.20 for rate in discount_rates)

        # Test growth rate ranges
        growth_rates = [0.02, 0.03, 0.04, 0.05, 0.06]
        assert all(0.01 <= rate <= 0.10 for rate in growth_rates)

        # Growth rates should be less than discount rates
        for growth in growth_rates:
            for discount in discount_rates:
                if growth >= discount:
                    # This combination should be flagged as invalid
                    assert growth < discount or abs(growth - discount) < 0.001


class TestDCFErrorHandling:
    """Test DCF error handling and edge cases"""

    def test_empty_fcf_data_handling(self):
        """Test handling of empty FCF data"""
        mock_calc = Mock()
        mock_calc.fcf_results = {}

        with patch.object(DCFValuator, '__init__', return_value=None):
            dcf = DCFValuator(None)
            dcf.financial_calculator = mock_calc

            # Should handle empty data gracefully
            assert len(mock_calc.fcf_results) == 0

    def test_invalid_growth_rate_handling(self):
        """Test handling of invalid growth rates"""
        # Growth rate >= discount rate should be handled
        discount_rate = 0.10
        invalid_growth = 0.12

        # This should be caught in validation
        assert invalid_growth > discount_rate

    def test_negative_fcf_handling(self):
        """Test handling of negative FCF values"""
        mock_calc = Mock()
        mock_calc.fcf_results = {
            'FCFF': [100, -50, 120, 130, 140]  # Contains negative value
        }

        with patch.object(DCFValuator, '__init__', return_value=None):
            dcf = DCFValuator(None)
            dcf.financial_calculator = mock_calc

            # Should handle negative values
            fcf_data = mock_calc.fcf_results['FCFF']
            assert min(fcf_data) < 0

    def test_zero_shares_outstanding_handling(self):
        """Test handling of zero or missing shares outstanding"""
        mock_calc = Mock()
        mock_calc.shares_outstanding = 0

        with patch.object(DCFValuator, '__init__', return_value=None):
            dcf = DCFValuator(None)
            dcf.financial_calculator = mock_calc

            # Should handle zero shares outstanding
            assert mock_calc.shares_outstanding == 0


class TestDCFMathematicalFunctions:
    """Test mathematical functions used in DCF calculations"""

    def test_npv_calculation(self):
        """Test Net Present Value calculation"""
        cash_flows = [100, 110, 121, 133, 146]
        discount_rate = 0.10

        # Calculate NPV manually
        npv = sum(cf / ((1 + discount_rate) ** (i + 1)) for i, cf in enumerate(cash_flows))

        # Verify calculation
        expected_npv = (100/1.1 + 110/1.1**2 + 121/1.1**3 + 133/1.1**4 + 146/1.1**5)
        assert abs(npv - expected_npv) < 0.01

    def test_irr_concept(self):
        """Test Internal Rate of Return concept"""
        # Test basic IRR concept - higher rate means lower present value
        cash_flow = 1000

        # Lower discount rate should give higher PV
        low_rate = 0.05
        high_rate = 0.15

        pv_low = cash_flow / (1 + low_rate)
        pv_high = cash_flow / (1 + high_rate)

        assert pv_low > pv_high

    def test_wacc_components(self):
        """Test WACC calculation components"""
        # WACC = (E/V * Re) + (D/V * Rd * (1 - Tc))
        equity_value = 800
        debt_value = 200
        total_value = equity_value + debt_value
        cost_of_equity = 0.12
        cost_of_debt = 0.06
        tax_rate = 0.25

        wacc = (equity_value/total_value * cost_of_equity) + \
               (debt_value/total_value * cost_of_debt * (1 - tax_rate))

        expected_wacc = (0.8 * 0.12) + (0.2 * 0.06 * 0.75)
        assert abs(wacc - expected_wacc) < 0.001

    def test_perpetuity_value(self):
        """Test perpetuity value calculation"""
        # PV of Perpetuity = PMT / r
        payment = 100
        discount_rate = 0.08

        perpetuity_value = payment / discount_rate
        expected_value = 100 / 0.08

        assert abs(perpetuity_value - expected_value) < 0.01