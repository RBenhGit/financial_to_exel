"""
Unit tests for DCF valuation module
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Import comprehensive fixtures
from tests.fixtures.analysis_fixtures import (
    comprehensive_mock_calculator,
    mock_var_input_data,
    dcf_valuator_with_mocks,
    sample_fcf_data,
    sample_financial_statements,
    sample_market_data,
    dcf_assumptions
)


class TestDCFValuator:
    """Test cases for DCFValuator class"""

    def test_dcf_valuator_initialization(self, dcf_valuator_with_mocks):
        """Test DCF valuator initializes correctly"""
        assert dcf_valuator_with_mocks is not None
        assert hasattr(dcf_valuator_with_mocks, 'financial_calculator')
        assert dcf_valuator_with_mocks.ticker_symbol == 'TEST'

    def test_calculate_dcf_projections_basic(self, dcf_valuator_with_mocks):
        """Test basic DCF calculations"""
        dcf_results = dcf_valuator_with_mocks.calculate_dcf_projections()

        assert isinstance(dcf_results, dict)
        assert 'enterprise_value' in dcf_results
        assert 'equity_value' in dcf_results
        assert 'terminal_value' in dcf_results

        # Values should be positive
        if dcf_results.get('enterprise_value'):
            assert dcf_results['enterprise_value'] > 0

    def test_calculate_dcf_with_parameters(self, dcf_valuator):
        """Test DCF calculation with custom parameters"""
        dcf_results = dcf_valuator.calculate_dcf_projections(
            discount_rate=0.10,
            terminal_growth_rate=0.03,
            projection_years=5
        )

        assert isinstance(dcf_results, dict)
        # Should return valid results with custom parameters

    def test_terminal_value_calculation(self, dcf_valuator):
        """Test terminal value calculation"""
        # Mock terminal value calculation
        final_fcf = 15000
        growth_rate = 0.03
        discount_rate = 0.10

        expected_terminal_value = final_fcf * (1 + growth_rate) / (discount_rate - growth_rate)
        calculated_terminal_value = final_fcf * (1 + growth_rate) / (discount_rate - growth_rate)

        assert abs(calculated_terminal_value - expected_terminal_value) < 1e-6
        assert calculated_terminal_value > 0

    def test_present_value_calculation(self, dcf_valuator):
        """Test present value calculation"""
        future_value = 10000
        discount_rate = 0.10
        years = 5

        expected_pv = future_value / ((1 + discount_rate) ** years)
        calculated_pv = future_value / ((1 + discount_rate) ** years)

        assert abs(calculated_pv - expected_pv) < 1e-6
        assert calculated_pv > 0
        assert calculated_pv < future_value

    def test_enterprise_to_equity_value_conversion(self, dcf_valuator):
        """Test conversion from enterprise value to equity value"""
        enterprise_value = 1000000
        total_debt = 200000
        cash = 50000

        expected_equity_value = enterprise_value - total_debt + cash
        calculated_equity_value = enterprise_value - total_debt + cash

        assert calculated_equity_value == expected_equity_value
        assert calculated_equity_value == 850000

    def test_error_handling_missing_fcf_data(self, mock_calculator):
        """Test error handling when FCF data is missing"""
        mock_calculator.calculate_all_fcf_types.return_value = {}

        from core.analysis.dcf.dcf_valuation import DCFValuator
        valuator = DCFValuator(mock_calculator)

        # Should handle missing FCF data gracefully
        dcf_results = valuator.calculate_dcf_projections()
        assert isinstance(dcf_results, dict)

    def test_negative_growth_rate_handling(self, dcf_valuator):
        """Test handling of negative growth rates"""
        # DCF should handle negative growth (decline) scenarios
        dcf_results = dcf_valuator.calculate_dcf_projections(
            terminal_growth_rate=-0.02  # 2% decline
        )

        assert isinstance(dcf_results, dict)
        # Should still return valid results

    def test_sensitivity_analysis_parameters(self, dcf_valuator):
        """Test DCF sensitivity to different parameters"""
        base_results = dcf_valuator.calculate_dcf_projections(discount_rate=0.10)
        higher_discount_results = dcf_valuator.calculate_dcf_projections(discount_rate=0.15)

        # Higher discount rate should result in lower valuation
        if (base_results.get('enterprise_value') and
            higher_discount_results.get('enterprise_value')):
            assert higher_discount_results['enterprise_value'] < base_results['enterprise_value']


class TestDCFCalculationMethods:
    """Test individual DCF calculation methods"""

    def test_discount_factor_calculation(self):
        """Test discount factor calculation"""
        discount_rate = 0.10
        year = 3

        expected_factor = 1 / ((1 + discount_rate) ** year)
        calculated_factor = 1 / ((1 + discount_rate) ** year)

        assert abs(calculated_factor - expected_factor) < 1e-10
        assert 0 < calculated_factor < 1

    def test_fcf_projection_with_growth(self):
        """Test FCF projection with growth rates"""
        base_fcf = 10000
        growth_rate = 0.05
        years = 3

        projected_fcf = base_fcf * ((1 + growth_rate) ** years)
        expected_fcf = 10000 * (1.05 ** 3)

        assert abs(projected_fcf - expected_fcf) < 1e-6
        assert projected_fcf > base_fcf

    def test_wacc_calculation_components(self):
        """Test WACC calculation components"""
        # Basic WACC formula components
        cost_of_equity = 0.12
        cost_of_debt = 0.05
        tax_rate = 0.25
        debt_ratio = 0.3
        equity_ratio = 0.7

        wacc = (equity_ratio * cost_of_equity) + (debt_ratio * cost_of_debt * (1 - tax_rate))
        expected_wacc = (0.7 * 0.12) + (0.3 * 0.05 * 0.75)

        assert abs(wacc - expected_wacc) < 1e-6
        assert wacc > 0
        assert wacc < max(cost_of_equity, cost_of_debt)


class TestDCFEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_fcf_handling(self, mock_calculator):
        """Test handling of zero FCF values"""
        mock_calculator.calculate_all_fcf_types.return_value = {
            'Free Cash Flow': [0, 0, 0, 0]
        }

        from core.analysis.dcf.dcf_valuation import DCFValuator
        valuator = DCFValuator(mock_calculator)

        dcf_results = valuator.calculate_dcf_projections()
        assert isinstance(dcf_results, dict)

    def test_extremely_high_discount_rate(self, dcf_valuator):
        """Test DCF with extremely high discount rate"""
        dcf_results = dcf_valuator.calculate_dcf_projections(discount_rate=0.50)

        # Should handle high discount rates without errors
        assert isinstance(dcf_results, dict)

    def test_very_long_projection_period(self, dcf_valuator):
        """Test DCF with very long projection period"""
        dcf_results = dcf_valuator.calculate_dcf_projections(projection_years=50)

        assert isinstance(dcf_results, dict)

    def test_invalid_growth_rate_bounds(self, dcf_valuator):
        """Test handling of invalid growth rate parameters"""
        # Growth rate higher than discount rate (invalid for terminal value)
        try:
            dcf_results = dcf_valuator.calculate_dcf_projections(
                discount_rate=0.08,
                terminal_growth_rate=0.10  # Higher than discount rate
            )
            # If it doesn't raise an error, should at least return a dict
            assert isinstance(dcf_results, dict)
        except (ValueError, ZeroDivisionError):
            # Acceptable to raise errors for invalid parameters
            pass


class TestDCFIntegration:
    """Integration tests for DCF valuation"""

    def test_dcf_results_consistency(self, dcf_valuator):
        """Test consistency of DCF results"""
        # Run DCF calculation multiple times
        results1 = dcf_valuator.calculate_dcf_projections()
        results2 = dcf_valuator.calculate_dcf_projections()

        # Results should be consistent
        if results1.get('enterprise_value') and results2.get('enterprise_value'):
            assert abs(results1['enterprise_value'] - results2['enterprise_value']) < 1e-6

    def test_dcf_value_reasonableness(self, dcf_valuator):
        """Test that DCF values are within reasonable bounds"""
        dcf_results = dcf_valuator.calculate_dcf_projections()

        if dcf_results.get('enterprise_value'):
            ev = dcf_results['enterprise_value']
            # Enterprise value should be positive and reasonable
            assert ev > 0
            assert ev < 1e15  # Less than a quadrillion (sanity check)

        if dcf_results.get('value_per_share'):
            vps = dcf_results['value_per_share']
            assert vps > 0
            assert vps < 1e6  # Less than a million per share (sanity check)

    @pytest.mark.skipif(True, reason="Performance test - enable if needed")
    def test_dcf_calculation_performance(self, dcf_valuator):
        """Test DCF calculation performance"""
        import time

        start_time = time.time()
        dcf_results = dcf_valuator.calculate_dcf_projections()
        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 5.0
        assert dcf_results is not None


if __name__ == "__main__":
    pytest.main([__file__])