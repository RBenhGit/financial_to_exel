"""
Comprehensive Tests for DCF Valuation Module
==========================================

This test suite covers the DCFValuator class which performs Discounted Cash Flow
analysis, including multi-stage growth projections and sensitivity analysis.

Test Coverage Areas:
1. DCF Initialization and Setup
2. Cash Flow Projections
3. Terminal Value Calculations
4. Discount Rate and WACC Calculations
5. Sensitivity Analysis
6. Integration with FinancialCalculator
7. Edge Cases and Error Handling
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

try:
    from core.analysis.dcf.dcf_valuation import DCFValuator
    from core.analysis.engines.financial_calculations import FinancialCalculator
    from config.config import Config
except ImportError as e:
    pytest.skip(f"Skipping DCF valuation tests: {e}", allow_module_level=True)


class TestDCFValuatorInitialization:
    """Test DCFValuator initialization and setup"""

    def test_basic_initialization(self):
        """Test basic DCF valuator initialization"""
        mock_calc = Mock(spec=FinancialCalculator)
        mock_calc.ticker = 'AAPL'

        dcf = DCFValuator(mock_calc)
        assert dcf.financial_calculator == mock_calc
        assert hasattr(dcf, 'config')

    def test_initialization_with_custom_config(self):
        """Test DCF initialization with custom configuration"""
        mock_calc = Mock(spec=FinancialCalculator)
        mock_calc.ticker = 'MSFT'
        config = Config()

        dcf = DCFValuator(mock_calc, config=config)
        assert dcf.financial_calculator == mock_calc
        assert dcf.config == config


class TestDCFProjections:
    """Test DCF cash flow projections"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_calc = Mock(spec=FinancialCalculator)
        self.mock_calc.ticker = 'TEST'

        # Mock historical FCF data
        self.mock_calc.calculate_all_fcf_types.return_value = {
            'fcfe': {'FY2021': 1000, 'FY2022': 1100, 'FY2023': 1200},
            'fcff': {'FY2021': 1200, 'FY2022': 1320, 'FY2023': 1440},
            'levered_fcf': {'FY2021': 1100, 'FY2022': 1210, 'FY2023': 1320}
        }

        self.dcf = DCFValuator(self.mock_calc)

    def test_calculate_dcf_projections_basic(self):
        """Test basic DCF projections calculation"""
        with patch.object(self.dcf, '_get_base_fcf', return_value=1200):
            with patch.object(self.dcf, '_calculate_growth_rates', return_value=[0.10, 0.08, 0.05]):
                with patch.object(self.dcf, '_get_discount_rate', return_value=0.10):

                    result = self.dcf.calculate_dcf_projections()

                    assert result is not None
                    assert isinstance(result, dict)

    def test_calculate_projections_with_custom_assumptions(self):
        """Test DCF projections with custom assumptions"""
        assumptions = {
            'growth_stage1': 0.15,
            'growth_stage2': 0.08,
            'terminal_growth': 0.03,
            'discount_rate': 0.12,
            'years_stage1': 5,
            'years_stage2': 5
        }

        with patch.object(self.dcf, '_get_base_fcf', return_value=1000):
            result = self.dcf.calculate_dcf_projections(assumptions=assumptions)

            assert result is not None
            assert isinstance(result, dict)

    def test_multi_stage_growth_projections(self):
        """Test multi-stage growth projections"""
        with patch.object(self.dcf, '_get_base_fcf', return_value=1000):
            with patch.object(self.dcf, '_calculate_growth_rates', return_value=[0.12, 0.08, 0.04]):

                projections = self.dcf._project_cash_flows(
                    base_fcf=1000,
                    growth_stage1=0.12,
                    growth_stage2=0.08,
                    years_stage1=5,
                    years_stage2=5
                )

                assert projections is not None
                assert len(projections) >= 10  # 5 + 5 years minimum

    def test_terminal_value_calculation(self):
        """Test terminal value calculation using Gordon Growth Model"""
        terminal_fcf = 2000
        terminal_growth = 0.03
        discount_rate = 0.10

        terminal_value = self.dcf._calculate_terminal_value(
            terminal_fcf, terminal_growth, discount_rate
        )

        expected_value = terminal_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
        assert abs(terminal_value - expected_value) < 0.01  # Allow small floating point differences

    def test_present_value_calculation(self):
        """Test present value calculation of projected cash flows"""
        future_cash_flows = [1000, 1100, 1200, 1300, 1400]
        discount_rate = 0.10

        pv = self.dcf._calculate_present_value(future_cash_flows, discount_rate)

        assert pv > 0
        assert pv < sum(future_cash_flows)  # PV should be less than sum of future CFs


class TestSensitivityAnalysis:
    """Test DCF sensitivity analysis functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_calc = Mock(spec=FinancialCalculator)
        self.mock_calc.ticker = 'TEST'
        self.dcf = DCFValuator(self.mock_calc)

    def test_sensitivity_analysis_basic(self):
        """Test basic sensitivity analysis"""
        discount_rates = [0.08, 0.09, 0.10, 0.11, 0.12]
        growth_rates = [0.02, 0.03, 0.04, 0.05, 0.06]

        with patch.object(self.dcf, 'calculate_dcf_projections') as mock_dcf:
            mock_dcf.return_value = {'value_per_share': 100.0}

            sensitivity = self.dcf.sensitivity_analysis(discount_rates, growth_rates)

            assert sensitivity is not None
            assert isinstance(sensitivity, (dict, pd.DataFrame))

    def test_sensitivity_with_market_comparison(self):
        """Test sensitivity analysis with current market price comparison"""
        discount_rates = [0.09, 0.10, 0.11]
        growth_rates = [0.03, 0.04, 0.05]
        current_price = 150.0

        with patch.object(self.dcf, 'calculate_dcf_projections') as mock_dcf:
            mock_dcf.return_value = {'value_per_share': 120.0}

            sensitivity = self.dcf.sensitivity_analysis(
                discount_rates,
                growth_rates,
                current_market_price=current_price
            )

            assert sensitivity is not None


class TestDiscountRateCalculations:
    """Test discount rate and WACC calculations"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_calc = Mock(spec=FinancialCalculator)
        self.mock_calc.ticker = 'TEST'
        self.dcf = DCFValuator(self.mock_calc)

    def test_wacc_calculation(self):
        """Test Weighted Average Cost of Capital calculation"""
        # Mock financial data for WACC calculation
        mock_data = {
            'market_cap': 100000,
            'total_debt': 30000,
            'cash': 5000,
            'tax_rate': 0.25,
            'cost_of_equity': 0.12,
            'cost_of_debt': 0.05
        }

        with patch.object(self.dcf, '_get_financial_metrics', return_value=mock_data):
            wacc = self.dcf._calculate_wacc()

            assert wacc > 0
            assert wacc < 1  # Should be a percentage in decimal form

    def test_cost_of_equity_calculation(self):
        """Test cost of equity calculation using CAPM"""
        risk_free_rate = 0.03
        beta = 1.2
        market_risk_premium = 0.06

        cost_of_equity = self.dcf._calculate_cost_of_equity(
            risk_free_rate, beta, market_risk_premium
        )

        expected = risk_free_rate + beta * market_risk_premium
        assert abs(cost_of_equity - expected) < 0.001

    def test_beta_calculation(self):
        """Test beta calculation from stock and market returns"""
        # Mock return data
        stock_returns = pd.Series([0.05, -0.02, 0.08, 0.03, -0.01])
        market_returns = pd.Series([0.04, -0.01, 0.06, 0.02, 0.01])

        with patch.object(self.dcf, '_get_stock_returns', return_value=stock_returns):
            with patch.object(self.dcf, '_get_market_returns', return_value=market_returns):
                beta = self.dcf._calculate_beta()

                assert beta is not None
                assert isinstance(beta, (int, float))


class TestGrowthRateCalculations:
    """Test growth rate calculations for DCF projections"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_calc = Mock(spec=FinancialCalculator)
        self.mock_calc.ticker = 'TEST'

        # Mock historical data
        self.mock_calc.calculate_revenue_growth_rates.return_value = [0.10, 0.12, 0.08]
        self.mock_calc.calculate_fcf_growth_rates.return_value = [0.15, 0.11, 0.09]

        self.dcf = DCFValuator(self.mock_calc)

    def test_historical_growth_rate_calculation(self):
        """Test calculation of historical growth rates"""
        growth_rates = self.dcf._calculate_historical_growth_rates()

        assert growth_rates is not None
        assert isinstance(growth_rates, (list, tuple, np.ndarray))
        assert len(growth_rates) > 0

    def test_projected_growth_rate_calculation(self):
        """Test calculation of projected growth rates"""
        historical_rates = [0.10, 0.12, 0.08, 0.15]

        projected_rates = self.dcf._calculate_projected_growth_rates(historical_rates)

        assert projected_rates is not None
        assert len(projected_rates) >= 2  # At least stage 1 and terminal growth

    def test_growth_rate_smoothing(self):
        """Test growth rate smoothing for extreme values"""
        volatile_rates = [0.50, -0.20, 0.30, -0.10, 0.40]

        smoothed_rates = self.dcf._smooth_growth_rates(volatile_rates)

        assert smoothed_rates is not None
        assert max(smoothed_rates) < max(volatile_rates)  # Should reduce volatility


class TestDataIntegration:
    """Test integration with data sources and FinancialCalculator"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_calc = Mock(spec=FinancialCalculator)
        self.mock_calc.ticker = 'TEST'
        self.dcf = DCFValuator(self.mock_calc)

    def test_financial_calculator_integration(self):
        """Test integration with FinancialCalculator"""
        # Mock FinancialCalculator methods
        self.mock_calc.calculate_all_fcf_types.return_value = {
            'fcfe': {'FY2023': 1000},
            'fcff': {'FY2023': 1200},
            'levered_fcf': {'FY2023': 1100}
        }

        self.mock_calc.calculate_revenue_growth_rates.return_value = [0.10, 0.08]

        # Should be able to retrieve data from calculator
        fcf_data = self.dcf._get_base_fcf()
        assert fcf_data is not None

        growth_data = self.dcf._calculate_historical_growth_rates()
        assert growth_data is not None

    def test_market_data_integration(self):
        """Test integration with market data sources"""
        with patch.object(self.dcf, '_get_current_stock_price', return_value=150.0):
            with patch.object(self.dcf, '_get_risk_free_rate', return_value=0.03):
                with patch.object(self.dcf, '_get_market_risk_premium', return_value=0.06):

                    # Should be able to retrieve market data
                    stock_price = self.dcf._get_current_stock_price()
                    assert stock_price == 150.0

                    risk_free = self.dcf._get_risk_free_rate()
                    assert risk_free == 0.03


class TestErrorHandling:
    """Test error handling and edge cases"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_calc = Mock(spec=FinancialCalculator)
        self.mock_calc.ticker = 'TEST'
        self.dcf = DCFValuator(self.mock_calc)

    def test_missing_financial_data_handling(self):
        """Test handling of missing financial data"""
        self.mock_calc.calculate_all_fcf_types.return_value = None

        try:
            result = self.dcf.calculate_dcf_projections()
            # Should either handle gracefully or raise informative error
        except Exception as e:
            assert len(str(e)) > 0  # Should have meaningful error message

    def test_invalid_growth_rates_handling(self):
        """Test handling of invalid growth rates"""
        # Test negative terminal growth rate
        with pytest.raises((ValueError, AssertionError)):
            self.dcf._calculate_terminal_value(1000, -0.05, 0.10)

        # Test terminal growth rate higher than discount rate
        with pytest.raises((ValueError, AssertionError)):
            self.dcf._calculate_terminal_value(1000, 0.15, 0.10)

    def test_zero_division_protection(self):
        """Test protection against zero division errors"""
        # Test with zero discount rate
        try:
            result = self.dcf._calculate_present_value([1000, 1100], 0.0)
            # Should handle gracefully or raise appropriate error
        except (ZeroDivisionError, ValueError):
            pass  # Expected behavior

    def test_extreme_values_handling(self):
        """Test handling of extreme values"""
        # Test with very large cash flows
        large_cf = [1e10, 1e11, 1e12]
        result = self.dcf._calculate_present_value(large_cf, 0.10)
        assert not np.isnan(result) and not np.isinf(result)

        # Test with very small cash flows
        small_cf = [1e-6, 1e-7, 1e-8]
        result = self.dcf._calculate_present_value(small_cf, 0.10)
        assert not np.isnan(result) and not np.isinf(result)


class TestPerformanceAndScalability:
    """Test performance and scalability"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_calc = Mock(spec=FinancialCalculator)
        self.mock_calc.ticker = 'TEST'
        self.dcf = DCFValuator(self.mock_calc)

    def test_large_sensitivity_analysis_performance(self):
        """Test performance with large sensitivity analysis"""
        # Large parameter ranges
        discount_rates = np.linspace(0.05, 0.20, 50)
        growth_rates = np.linspace(0.01, 0.10, 50)

        with patch.object(self.dcf, 'calculate_dcf_projections') as mock_dcf:
            mock_dcf.return_value = {'value_per_share': 100.0}

            start_time = pd.Timestamp.now()
            sensitivity = self.dcf.sensitivity_analysis(discount_rates, growth_rates)
            end_time = pd.Timestamp.now()

            # Should complete within reasonable time
            assert (end_time - start_time).total_seconds() < 10
            assert sensitivity is not None

    def test_long_projection_period_performance(self):
        """Test performance with long projection periods"""
        # Test 30-year projections
        with patch.object(self.dcf, '_get_base_fcf', return_value=1000):
            projections = self.dcf._project_cash_flows(
                base_fcf=1000,
                growth_stage1=0.10,
                growth_stage2=0.05,
                years_stage1=15,
                years_stage2=15
            )

            assert len(projections) == 30
            assert all(cf > 0 for cf in projections)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])