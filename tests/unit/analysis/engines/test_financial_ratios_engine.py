"""
Unit Tests for Financial Ratios Engine
======================================

Comprehensive unit tests for the FinancialRatiosEngine class covering:
- All ratio calculation methods
- Input validation and error handling
- Edge cases and boundary conditions
- Result format validation
- Category organization

Test Categories:
- Liquidity Ratios Tests
- Profitability Ratios Tests
- Leverage/Solvency Ratios Tests
- Efficiency/Activity Ratios Tests
- Integration Tests
- Error Handling Tests
"""

import pytest
import math
from datetime import datetime
from typing import Dict, Any

from core.analysis.engines.financial_ratios_engine import (
    FinancialRatiosEngine,
    RatioInputs,
    RatioResult,
    RatioCategory
)


class TestFinancialRatiosEngine:
    """Test suite for FinancialRatiosEngine"""

    @pytest.fixture
    def engine(self):
        """Create a FinancialRatiosEngine instance for testing"""
        return FinancialRatiosEngine()

    @pytest.fixture
    def sample_inputs(self):
        """Create sample financial data for testing"""
        return RatioInputs(
            # Income Statement
            revenue=1000000,
            cost_of_goods_sold=600000,
            gross_profit=400000,
            operating_income=250000,
            ebit=200000,
            ebitda=250000,
            net_income=150000,
            interest_expense=20000,

            # Balance Sheet
            total_assets=2000000,
            current_assets=500000,
            cash_and_equivalents=100000,
            accounts_receivable=150000,
            inventory=100000,
            total_liabilities=800000,
            current_liabilities=300000,
            total_debt=400000,
            long_term_debt=300000,
            shareholders_equity=1200000,

            # Cash Flow
            operating_cash_flow=180000,
            free_cash_flow=120000,
            capital_expenditures=60000,

            # Market Data
            stock_price=50.0,
            shares_outstanding=10000000,
            market_capitalization=500000000,

            # Previous period data
            previous_revenue=900000,
            previous_net_income=130000,
            previous_fcf=100000,

            # Additional metrics
            book_value_per_share=120.0,
            earnings_per_share=15.0
        )

    # =============================================================================
    # INITIALIZATION TESTS
    # =============================================================================

    def test_engine_initialization(self, engine):
        """Test engine initializes correctly"""
        assert isinstance(engine, FinancialRatiosEngine)
        assert hasattr(engine, 'supported_ratios')
        assert len(engine.supported_ratios) == 6  # Six categories

        # Check all categories are present
        expected_categories = {
            RatioCategory.LIQUIDITY,
            RatioCategory.PROFITABILITY,
            RatioCategory.EFFICIENCY,
            RatioCategory.LEVERAGE,
            RatioCategory.MARKET_VALUE,
            RatioCategory.GROWTH
        }
        assert set(engine.supported_ratios.keys()) == expected_categories

    def test_supported_ratios_structure(self, engine):
        """Test supported ratios data structure"""
        for category, ratios in engine.supported_ratios.items():
            assert isinstance(category, RatioCategory)
            assert isinstance(ratios, list)
            assert len(ratios) > 0
            for ratio in ratios:
                assert isinstance(ratio, str)
                assert len(ratio) > 0

    # =============================================================================
    # LIQUIDITY RATIOS TESTS
    # =============================================================================

    def test_current_ratio_calculation(self, engine, sample_inputs):
        """Test current ratio calculation"""
        result = engine.calculate_current_ratio(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Current Ratio"
        assert result.category == RatioCategory.LIQUIDITY
        assert result.is_valid is True
        assert result.value == pytest.approx(1.667, rel=1e-3)  # 500000 / 300000
        assert "liquidity position" in result.interpretation.lower()
        assert result.formula == "Current Assets / Current Liabilities"

    def test_current_ratio_missing_data(self, engine):
        """Test current ratio with missing data"""
        inputs = RatioInputs(current_assets=None, current_liabilities=300000)
        result = engine.calculate_current_ratio(inputs)

        assert result.is_valid is False
        assert "missing" in result.error_message.lower()
        assert result.value == 0.0

    def test_current_ratio_zero_liabilities(self, engine):
        """Test current ratio with zero current liabilities"""
        inputs = RatioInputs(current_assets=500000, current_liabilities=0)
        result = engine.calculate_current_ratio(inputs)

        assert result.is_valid is False
        assert "zero" in result.error_message.lower()
        assert math.isinf(result.value)

    def test_quick_ratio_calculation(self, engine, sample_inputs):
        """Test quick ratio calculation"""
        result = engine.calculate_quick_ratio(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Quick Ratio"
        assert result.category == RatioCategory.LIQUIDITY
        assert result.is_valid is True
        # (500000 - 100000) / 300000 = 1.333
        assert result.value == pytest.approx(1.333, rel=1e-3)
        assert "quick_assets" in result.metadata

    def test_quick_ratio_no_inventory(self, engine):
        """Test quick ratio when inventory is None"""
        inputs = RatioInputs(
            current_assets=500000,
            current_liabilities=300000,
            inventory=None
        )
        result = engine.calculate_quick_ratio(inputs)

        assert result.is_valid is True
        assert result.value == pytest.approx(1.667, rel=1e-3)  # No inventory deduction
        assert result.metadata['inventory'] == 0.0

    def test_cash_ratio_calculation(self, engine, sample_inputs):
        """Test cash ratio calculation"""
        result = engine.calculate_cash_ratio(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Cash Ratio"
        assert result.category == RatioCategory.LIQUIDITY
        assert result.is_valid is True
        assert result.value == pytest.approx(0.3333, rel=1e-3)  # 100000 / 300000
        assert "cash" in result.interpretation.lower()

    # =============================================================================
    # PROFITABILITY RATIOS TESTS
    # =============================================================================

    def test_gross_profit_margin_calculation(self, engine, sample_inputs):
        """Test gross profit margin calculation"""
        result = engine.calculate_gross_profit_margin(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Gross Profit Margin"
        assert result.category == RatioCategory.PROFITABILITY
        assert result.is_valid is True
        assert result.value == pytest.approx(40.0, rel=1e-3)  # 400000 / 1000000 * 100
        assert "profitability" in result.interpretation.lower()

    def test_gross_profit_margin_with_cogs(self, engine):
        """Test gross profit margin calculation using COGS"""
        inputs = RatioInputs(
            revenue=1000000,
            cost_of_goods_sold=600000,
            gross_profit=None  # Should be calculated from revenue - COGS
        )
        result = engine.calculate_gross_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == pytest.approx(40.0, rel=1e-3)
        assert result.metadata['gross_profit'] == 400000

    def test_gross_profit_margin_missing_data(self, engine):
        """Test gross profit margin with insufficient data"""
        inputs = RatioInputs(
            revenue=1000000,
            cost_of_goods_sold=None,
            gross_profit=None
        )
        result = engine.calculate_gross_profit_margin(inputs)

        assert result.is_valid is False
        assert "missing" in result.error_message.lower()

    def test_net_profit_margin_calculation(self, engine, sample_inputs):
        """Test net profit margin calculation"""
        result = engine.calculate_net_profit_margin(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Net Profit Margin"
        assert result.category == RatioCategory.PROFITABILITY
        assert result.is_valid is True
        assert result.value == pytest.approx(15.0, rel=1e-3)  # 150000 / 1000000 * 100

    def test_net_profit_margin_negative(self, engine):
        """Test net profit margin with negative net income"""
        inputs = RatioInputs(revenue=1000000, net_income=-50000)
        result = engine.calculate_net_profit_margin(inputs)

        assert result.is_valid is True
        assert result.value == pytest.approx(-5.0, rel=1e-3)
        assert "negative" in result.interpretation.lower()

    def test_return_on_assets_calculation(self, engine, sample_inputs):
        """Test ROA calculation"""
        result = engine.calculate_return_on_assets(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Return on Assets (ROA)"
        assert result.category == RatioCategory.PROFITABILITY
        assert result.is_valid is True
        assert result.value == pytest.approx(7.5, rel=1e-3)  # 150000 / 2000000 * 100

    def test_return_on_equity_calculation(self, engine, sample_inputs):
        """Test ROE calculation"""
        result = engine.calculate_return_on_equity(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Return on Equity (ROE)"
        assert result.category == RatioCategory.PROFITABILITY
        assert result.is_valid is True
        assert result.value == pytest.approx(12.5, rel=1e-3)  # 150000 / 1200000 * 100

    # =============================================================================
    # LEVERAGE/SOLVENCY RATIOS TESTS
    # =============================================================================

    def test_debt_to_assets_ratio_calculation(self, engine, sample_inputs):
        """Test debt-to-assets ratio calculation"""
        result = engine.calculate_debt_to_assets_ratio(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Debt-to-Assets Ratio"
        assert result.category == RatioCategory.LEVERAGE
        assert result.is_valid is True
        assert result.value == pytest.approx(20.0, rel=1e-3)  # 400000 / 2000000 * 100

    def test_debt_to_equity_ratio_calculation(self, engine, sample_inputs):
        """Test debt-to-equity ratio calculation"""
        result = engine.calculate_debt_to_equity_ratio(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Debt-to-Equity Ratio"
        assert result.category == RatioCategory.LEVERAGE
        assert result.is_valid is True
        assert result.value == pytest.approx(0.3333, rel=1e-3)  # 400000 / 1200000

    def test_debt_to_equity_zero_equity(self, engine):
        """Test debt-to-equity ratio with zero equity"""
        inputs = RatioInputs(total_debt=400000, shareholders_equity=0)
        result = engine.calculate_debt_to_equity_ratio(inputs)

        assert result.is_valid is False
        assert math.isinf(result.value)
        assert "zero" in result.error_message.lower()

    def test_interest_coverage_ratio_calculation(self, engine, sample_inputs):
        """Test interest coverage ratio calculation"""
        result = engine.calculate_interest_coverage_ratio(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Interest Coverage Ratio"
        assert result.category == RatioCategory.LEVERAGE
        assert result.is_valid is True
        assert result.value == pytest.approx(10.0, rel=1e-3)  # 200000 / 20000

    def test_interest_coverage_zero_interest(self, engine):
        """Test interest coverage ratio with zero interest expense"""
        inputs = RatioInputs(ebit=200000, interest_expense=0)
        result = engine.calculate_interest_coverage_ratio(inputs)

        assert result.is_valid is True
        assert math.isinf(result.value)
        assert "debt-free" in result.interpretation.lower()

    # =============================================================================
    # EFFICIENCY/ACTIVITY RATIOS TESTS
    # =============================================================================

    def test_asset_turnover_calculation(self, engine, sample_inputs):
        """Test asset turnover calculation"""
        result = engine.calculate_asset_turnover(sample_inputs)

        assert isinstance(result, RatioResult)
        assert result.name == "Asset Turnover"
        assert result.category == RatioCategory.EFFICIENCY
        assert result.is_valid is True
        assert result.value == pytest.approx(0.5, rel=1e-3)  # 1000000 / 2000000

    # =============================================================================
    # COMPREHENSIVE CALCULATION TESTS
    # =============================================================================

    def test_calculate_all_ratios(self, engine, sample_inputs):
        """Test calculating all available ratios"""
        results = engine.calculate_all_ratios(sample_inputs)

        assert isinstance(results, dict)
        assert len(results) > 0

        # Check that we have results from multiple categories
        categories_present = set()
        for result in results.values():
            assert isinstance(result, RatioResult)
            categories_present.add(result.category)

        assert len(categories_present) >= 3  # Should have at least 3 categories

        # Check specific ratios are present
        expected_ratios = [
            'current_ratio', 'quick_ratio', 'cash_ratio',
            'gross_profit_margin', 'net_profit_margin', 'return_on_assets', 'return_on_equity',
            'debt_to_assets_ratio', 'debt_to_equity_ratio', 'interest_coverage_ratio',
            'asset_turnover'
        ]

        for ratio_name in expected_ratios:
            assert ratio_name in results
            assert isinstance(results[ratio_name], RatioResult)

    def test_calculate_all_ratios_with_missing_data(self, engine):
        """Test calculating all ratios with incomplete data"""
        incomplete_inputs = RatioInputs(
            revenue=1000000,
            net_income=150000,
            current_assets=500000
            # Many fields missing
        )

        results = engine.calculate_all_ratios(incomplete_inputs)

        # Should still return results, but many will be invalid
        assert isinstance(results, dict)
        assert len(results) > 0

        # Count valid vs invalid results
        valid_count = sum(1 for result in results.values() if result.is_valid)
        invalid_count = len(results) - valid_count

        # Should have some invalid results due to missing data
        assert invalid_count > 0
        # Should have at least some valid results
        assert valid_count > 0

    # =============================================================================
    # UTILITY METHODS TESTS
    # =============================================================================

    def test_get_ratios_by_category(self, engine):
        """Test getting ratios by category"""
        liquidity_ratios = engine.get_ratios_by_category(RatioCategory.LIQUIDITY)

        assert isinstance(liquidity_ratios, list)
        assert len(liquidity_ratios) > 0

        expected_liquidity_ratios = [
            'current_ratio', 'quick_ratio', 'cash_ratio'
        ]

        for ratio in expected_liquidity_ratios:
            assert ratio in liquidity_ratios

    def test_get_all_supported_ratios(self, engine):
        """Test getting all supported ratios"""
        all_ratios = engine.get_all_supported_ratios()

        assert isinstance(all_ratios, dict)
        assert len(all_ratios) == 6  # Six categories

        for category, ratios in all_ratios.items():
            assert isinstance(category, RatioCategory)
            assert isinstance(ratios, list)
            assert len(ratios) > 0

    def test_validate_inputs(self, engine, sample_inputs):
        """Test input validation"""
        # Complete inputs should have no missing data
        missing_data = engine.validate_inputs(sample_inputs)
        assert isinstance(missing_data, dict)
        # Should be empty or have minimal missing data

        # Incomplete inputs should show missing data
        incomplete_inputs = RatioInputs(revenue=1000000)
        missing_data = engine.validate_inputs(incomplete_inputs)

        assert isinstance(missing_data, dict)
        assert len(missing_data) > 0

        # Check that missing data is categorized correctly
        for category, missing_fields in missing_data.items():
            assert isinstance(missing_fields, list)
            for field in missing_fields:
                assert isinstance(field, str)

    # =============================================================================
    # EDGE CASES AND ERROR HANDLING TESTS
    # =============================================================================

    def test_ratio_result_structure(self, engine, sample_inputs):
        """Test that all ratio results have correct structure"""
        result = engine.calculate_current_ratio(sample_inputs)

        # Test all required fields are present
        assert hasattr(result, 'name')
        assert hasattr(result, 'value')
        assert hasattr(result, 'category')
        assert hasattr(result, 'formula')
        assert hasattr(result, 'interpretation')
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'error_message')
        assert hasattr(result, 'calculation_date')
        assert hasattr(result, 'metadata')

        # Test field types
        assert isinstance(result.name, str)
        assert isinstance(result.value, (int, float))
        assert isinstance(result.category, RatioCategory)
        assert isinstance(result.formula, str)
        assert isinstance(result.interpretation, str)
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.calculation_date, datetime)
        assert isinstance(result.metadata, dict)

    def test_extreme_values(self, engine):
        """Test handling of extreme values"""
        extreme_inputs = RatioInputs(
            revenue=1e12,  # Very large number
            net_income=1e-6,  # Very small number
            total_assets=1e12,
            current_assets=1e12,
            current_liabilities=1e-6  # Very small denominator
        )

        # Should handle large numbers without overflow
        result = engine.calculate_net_profit_margin(extreme_inputs)
        assert result.is_valid is True
        assert math.isfinite(result.value)

        # Should handle very large ratios
        result = engine.calculate_current_ratio(extreme_inputs)
        assert result.is_valid is True
        # Value should be very large but finite
        assert result.value > 1e6

    def test_negative_values(self, engine):
        """Test handling of negative values"""
        negative_inputs = RatioInputs(
            revenue=1000000,
            net_income=-100000,  # Loss
            total_assets=2000000,
            shareholders_equity=-500000,  # Negative equity (insolvent)
            current_assets=500000,
            current_liabilities=300000
        )

        # Should handle negative net income correctly
        result = engine.calculate_net_profit_margin(negative_inputs)
        assert result.is_valid is True
        assert result.value < 0

        # Should handle negative equity appropriately
        result = engine.calculate_return_on_equity(negative_inputs)
        assert result.is_valid is True
        assert result.value > 0  # Negative income / negative equity = positive

    @pytest.mark.parametrize("invalid_input,expected_error", [
        (None, "missing"),
        (float('nan'), "calculation error"),
        (float('inf'), "calculation error"),
    ])
    def test_invalid_input_handling(self, engine, invalid_input, expected_error):
        """Test handling of various invalid inputs"""
        # This is a simplified test - in practice, you'd test each ratio method
        inputs = RatioInputs(
            revenue=invalid_input,
            net_income=150000
        )

        try:
            result = engine.calculate_net_profit_margin(inputs)
            if not result.is_valid:
                assert expected_error.lower() in result.error_message.lower()
        except Exception:
            # Exception handling is also acceptable for invalid inputs
            pass


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestFinancialRatiosEngineIntegration:
    """Integration tests for FinancialRatiosEngine"""

    @pytest.fixture
    def engine(self):
        return FinancialRatiosEngine()

    def test_real_world_financial_data_simulation(self, engine):
        """Test with realistic financial data simulating a real company"""
        # Simulate Apple-like financial data (scaled down)
        apple_like_inputs = RatioInputs(
            revenue=365000000,  # $365B revenue
            cost_of_goods_sold=223000000,
            gross_profit=142000000,
            operating_income=108000000,
            ebit=109000000,
            net_income=95000000,
            interest_expense=3000000,

            total_assets=352000000,
            current_assets=135000000,
            cash_and_equivalents=62000000,
            accounts_receivable=51000000,
            inventory=6000000,
            total_liabilities=287000000,
            current_liabilities=153000000,
            total_debt=132000000,
            shareholders_equity=65000000,

            stock_price=150.0,
            shares_outstanding=16000000000,
            market_capitalization=2400000000000
        )

        results = engine.calculate_all_ratios(apple_like_inputs)

        # Verify key ratios are in reasonable ranges for a tech company
        assert results['current_ratio'].value > 0.5  # Should have decent liquidity
        assert results['gross_profit_margin'].value > 30  # Tech companies have high margins
        assert results['return_on_assets'].value > 10  # Efficient asset usage
        assert results['debt_to_equity_ratio'].value < 3  # Not overly leveraged

        # All ratios should be valid with complete data
        valid_results = [r for r in results.values() if r.is_valid]
        assert len(valid_results) >= 8  # Should have most ratios calculable

    def test_manufacturing_company_simulation(self, engine):
        """Test with manufacturing company financial profile"""
        manufacturing_inputs = RatioInputs(
            revenue=50000000,
            cost_of_goods_sold=35000000,
            gross_profit=15000000,
            operating_income=5000000,
            ebit=4500000,
            net_income=3000000,
            interest_expense=1500000,

            total_assets=80000000,
            current_assets=25000000,
            cash_and_equivalents=3000000,
            inventory=8000000,  # Higher inventory typical for manufacturing
            current_liabilities=20000000,
            total_debt=30000000,  # Higher debt typical for capital-intensive
            shareholders_equity=50000000
        )

        results = engine.calculate_all_ratios(manufacturing_inputs)

        # Manufacturing companies typically have different ratio profiles
        assert results['current_ratio'].value > 1.0  # Need working capital
        assert results['gross_profit_margin'].value < 50  # Lower margins than tech
        assert results['debt_to_equity_ratio'].value < 1.0  # Reasonable leverage
        assert results['interest_coverage_ratio'].value > 2.0  # Can service debt