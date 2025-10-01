"""
Unit tests for market value ratio calculations in FinancialCalculationEngine.

Tests comprehensive market value ratio calculations including:
- Earnings Per Share (EPS) - Basic and Diluted
- Price-to-Earnings Ratio (P/E)
- Price-to-Sales Ratio (P/S)
- Price-to-Cash Flow Ratio (P/CF)
- Enterprise Value-to-EBITDA Ratio (EV/EBITDA)

Each test covers normal operations, edge cases, error handling, and validation.
"""

import pytest
import math
from core.analysis.engines.financial_calculation_engine import FinancialCalculationEngine, CalculationResult


class TestEarningsPerShare:
    """Test suite for EPS calculations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialCalculationEngine()

    # =====================
    # Basic EPS Tests
    # =====================

    def test_calculate_eps_basic_positive_earnings(self):
        """Test basic EPS calculation with positive earnings"""
        result = self.engine.calculate_earnings_per_share(
            net_income=10000000,  # $10M
            shares_outstanding=5000000  # 5M shares
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert result.metadata['basic_eps'] == 2.0
        assert result.metadata['net_income'] == 10000000
        assert result.metadata['shares_outstanding'] == 5000000
        assert 'Basic EPS' in result.metadata['calculation_method']
        assert 'diluted_eps' not in result.metadata

    def test_calculate_eps_basic_negative_earnings(self):
        """Test basic EPS calculation with negative earnings (loss)"""
        result = self.engine.calculate_earnings_per_share(
            net_income=-5000000,  # -$5M loss
            shares_outstanding=2000000  # 2M shares
        )

        assert result.is_valid is True
        assert result.value == -2.5
        assert result.metadata['basic_eps'] == -2.5

    def test_calculate_eps_fractional_result(self):
        """Test EPS calculation resulting in fractional value"""
        result = self.engine.calculate_earnings_per_share(
            net_income=7500000,  # $7.5M
            shares_outstanding=3000000  # 3M shares
        )

        assert result.is_valid is True
        assert result.value == 2.5

    def test_calculate_eps_zero_net_income(self):
        """Test EPS calculation with zero net income"""
        result = self.engine.calculate_earnings_per_share(
            net_income=0,
            shares_outstanding=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.0

    def test_calculate_eps_large_values(self):
        """Test EPS calculation with large realistic values"""
        result = self.engine.calculate_earnings_per_share(
            net_income=95000000000,  # $95B (Apple-like)
            shares_outstanding=15500000000  # 15.5B shares
        )

        assert result.is_valid is True
        assert abs(result.value - 6.129) < 0.001  # Approximately $6.13

    # =====================
    # Diluted EPS Tests
    # =====================

    def test_calculate_eps_diluted_with_options(self):
        """Test diluted EPS calculation with stock options"""
        result = self.engine.calculate_earnings_per_share(
            net_income=10000000,  # $10M
            shares_outstanding=5000000,  # 5M basic shares
            diluted_shares_outstanding=5500000  # 5.5M diluted shares
        )

        assert result.is_valid is True
        assert result.value == pytest.approx(10000000 / 5500000, rel=1e-6)
        assert result.metadata['basic_eps'] == 2.0
        assert result.metadata['diluted_eps'] == pytest.approx(1.818182, rel=1e-5)
        assert result.metadata['diluted_shares_outstanding'] == 5500000
        assert 'Diluted EPS' in result.metadata['calculation_method']

    def test_calculate_eps_diluted_equals_basic(self):
        """Test diluted EPS when diluted shares equal basic shares"""
        result = self.engine.calculate_earnings_per_share(
            net_income=8000000,
            shares_outstanding=4000000,
            diluted_shares_outstanding=4000000  # Same as basic
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert result.metadata['basic_eps'] == result.metadata['diluted_eps']

    def test_calculate_eps_diluted_less_than_basic_invalid(self):
        """Test that diluted shares less than basic shares is handled"""
        result = self.engine.calculate_earnings_per_share(
            net_income=10000000,
            shares_outstanding=5000000,
            diluted_shares_outstanding=4000000  # Invalid: less than basic
        )

        # Should use basic shares and log warning
        assert result.is_valid is True
        assert result.value == 2.0  # Using basic shares
        assert result.metadata['basic_eps'] == 2.0

    def test_calculate_eps_diluted_with_zero_diluted_shares(self):
        """Test diluted EPS with zero diluted shares"""
        result = self.engine.calculate_earnings_per_share(
            net_income=10000000,
            shares_outstanding=5000000,
            diluted_shares_outstanding=0  # Invalid
        )

        # Should fall back to basic EPS
        assert result.is_valid is True
        assert result.value == 2.0

    def test_calculate_eps_diluted_with_none_diluted_shares(self):
        """Test that None diluted shares uses basic EPS"""
        result = self.engine.calculate_earnings_per_share(
            net_income=10000000,
            shares_outstanding=5000000,
            diluted_shares_outstanding=None
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert 'diluted_eps' not in result.metadata

    # =====================
    # Edge Cases and Error Handling
    # =====================

    def test_calculate_eps_none_net_income(self):
        """Test EPS calculation with None net income"""
        result = self.engine.calculate_earnings_per_share(
            net_income=None,
            shares_outstanding=1000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Input values cannot be None" in result.error_message

    def test_calculate_eps_none_shares_outstanding(self):
        """Test EPS calculation with None shares outstanding"""
        result = self.engine.calculate_earnings_per_share(
            net_income=10000000,
            shares_outstanding=None
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Input values cannot be None" in result.error_message

    def test_calculate_eps_zero_shares_outstanding(self):
        """Test EPS calculation with zero shares outstanding"""
        result = self.engine.calculate_earnings_per_share(
            net_income=10000000,
            shares_outstanding=0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Shares outstanding must be positive" in result.error_message

    def test_calculate_eps_negative_shares_outstanding(self):
        """Test EPS calculation with negative shares outstanding"""
        result = self.engine.calculate_earnings_per_share(
            net_income=10000000,
            shares_outstanding=-1000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Shares outstanding must be positive" in result.error_message

    # =====================
    # Real-world Scenarios
    # =====================

    def test_calculate_eps_tech_company_scenario(self):
        """Test EPS calculation for typical tech company"""
        # Similar to Microsoft: $72B net income, 7.5B shares
        result = self.engine.calculate_earnings_per_share(
            net_income=72000000000,
            shares_outstanding=7500000000,
            diluted_shares_outstanding=7650000000
        )

        assert result.is_valid is True
        assert result.value == pytest.approx(72000000000 / 7650000000, rel=1e-6)
        assert abs(result.value - 9.41) < 0.01

    def test_calculate_eps_small_cap_company(self):
        """Test EPS calculation for small cap company"""
        result = self.engine.calculate_earnings_per_share(
            net_income=5000000,  # $5M
            shares_outstanding=10000000  # 10M shares
        )

        assert result.is_valid is True
        assert result.value == 0.5

    def test_calculate_eps_startup_with_losses(self):
        """Test EPS calculation for startup with losses"""
        result = self.engine.calculate_earnings_per_share(
            net_income=-20000000,  # -$20M loss
            shares_outstanding=50000000  # 50M shares
        )

        assert result.is_valid is True
        assert result.value == -0.4

    def test_calculate_eps_high_dilution_scenario(self):
        """Test EPS with significant dilution from options/convertibles"""
        result = self.engine.calculate_earnings_per_share(
            net_income=100000000,
            shares_outstanding=50000000,  # 50M basic
            diluted_shares_outstanding=65000000  # 65M diluted (30% dilution)
        )

        assert result.is_valid is True
        basic_eps = 100000000 / 50000000  # $2.00
        diluted_eps = 100000000 / 65000000  # ~$1.54
        assert result.metadata['basic_eps'] == basic_eps
        assert result.metadata['diluted_eps'] == pytest.approx(diluted_eps, rel=1e-6)
        # Dilution impact
        dilution_impact = (basic_eps - diluted_eps) / basic_eps
        assert dilution_impact == pytest.approx(0.23, rel=0.01)  # ~23% dilution

    # =====================
    # Metadata Validation
    # =====================

    def test_calculate_eps_metadata_completeness(self):
        """Test that all expected metadata is present"""
        result = self.engine.calculate_earnings_per_share(
            net_income=15000000,
            shares_outstanding=6000000,
            diluted_shares_outstanding=6300000
        )

        assert result.is_valid is True
        assert 'net_income' in result.metadata
        assert 'shares_outstanding' in result.metadata
        assert 'basic_eps' in result.metadata
        assert 'diluted_eps' in result.metadata
        assert 'diluted_shares_outstanding' in result.metadata
        assert 'calculation_method' in result.metadata

    def test_calculate_eps_basic_metadata_without_dilution(self):
        """Test metadata when only basic EPS is calculated"""
        result = self.engine.calculate_earnings_per_share(
            net_income=12000000,
            shares_outstanding=4000000
        )

        assert result.is_valid is True
        assert 'net_income' in result.metadata
        assert 'shares_outstanding' in result.metadata
        assert 'basic_eps' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'diluted_eps' not in result.metadata
        assert 'diluted_shares_outstanding' not in result.metadata


class TestPriceToEarningsRatio:
    """Test suite for P/E ratio calculations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialCalculationEngine()

    # =====================
    # Basic P/E Ratio Tests
    # =====================

    def test_calculate_pe_ratio_normal_case(self):
        """Test P/E ratio calculation with typical values"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=150.0,
            eps=10.0
        )

        assert result.is_valid is True
        assert result.value == 15.0
        assert result.metadata['stock_price'] == 150.0
        assert result.metadata['eps'] == 10.0
        assert 'P/E Ratio = Stock Price / EPS' in result.metadata['calculation_method']
        assert 'Moderate P/E' in result.metadata['interpretation']

    def test_calculate_pe_ratio_low_valuation(self):
        """Test P/E ratio indicating low valuation"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=50.0,
            eps=8.0
        )

        assert result.is_valid is True
        assert result.value == 6.25
        assert 'Low P/E' in result.metadata['interpretation']

    def test_calculate_pe_ratio_high_valuation(self):
        """Test P/E ratio indicating high valuation"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=500.0,
            eps=10.0
        )

        assert result.is_valid is True
        assert result.value == 50.0
        assert 'Very high P/E' in result.metadata['interpretation']

    def test_calculate_pe_ratio_growth_stock(self):
        """Test P/E ratio for growth stock (high P/E)"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=800.0,
            eps=10.0
        )

        assert result.is_valid is True
        assert result.value == 80.0
        assert 'Very high P/E' in result.metadata['interpretation']

    def test_calculate_pe_ratio_value_stock(self):
        """Test P/E ratio for value stock (low P/E)"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=40.0,
            eps=5.0
        )

        assert result.is_valid is True
        assert result.value == 8.0
        assert 'Low P/E' in result.metadata['interpretation']

    def test_calculate_pe_ratio_fractional_values(self):
        """Test P/E ratio with fractional stock price and EPS"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=123.45,
            eps=6.78
        )

        assert result.is_valid is True
        assert result.value == pytest.approx(18.204, rel=1e-3)

    # =====================
    # Edge Cases - Negative/Zero EPS
    # =====================

    def test_calculate_pe_ratio_zero_eps(self):
        """Test P/E ratio with zero EPS (undefined)"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=100.0,
            eps=0.0
        )

        assert result.is_valid is False
        assert result.value == float('inf')
        assert "undefined for zero EPS" in result.error_message

    def test_calculate_pe_ratio_negative_eps(self):
        """Test P/E ratio with negative EPS (unprofitable company)"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=80.0,
            eps=-5.0
        )

        assert result.is_valid is False
        assert result.value == float('-inf')
        assert "company is unprofitable" in result.error_message

    def test_calculate_pe_ratio_small_positive_eps(self):
        """Test P/E ratio with very small positive EPS"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=100.0,
            eps=0.5
        )

        assert result.is_valid is True
        assert result.value == 200.0
        assert 'Very high P/E' in result.metadata['interpretation']

    # =====================
    # Input Validation Tests
    # =====================

    def test_calculate_pe_ratio_none_stock_price(self):
        """Test P/E ratio with None stock price"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=None,
            eps=10.0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Input values cannot be None" in result.error_message

    def test_calculate_pe_ratio_none_eps(self):
        """Test P/E ratio with None EPS"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=150.0,
            eps=None
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Input values cannot be None" in result.error_message

    def test_calculate_pe_ratio_zero_stock_price(self):
        """Test P/E ratio with zero stock price"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=0.0,
            eps=10.0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Stock price must be positive" in result.error_message

    def test_calculate_pe_ratio_negative_stock_price(self):
        """Test P/E ratio with negative stock price"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=-50.0,
            eps=10.0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Stock price must be positive" in result.error_message

    # =====================
    # Real-world Scenarios
    # =====================

    def test_calculate_pe_ratio_tech_company(self):
        """Test P/E ratio for typical tech company"""
        # Similar to Apple: ~$170 stock price, ~$6 EPS
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=170.0,
            eps=6.0
        )

        assert result.is_valid is True
        assert abs(result.value - 28.33) < 0.1
        assert 'Elevated P/E' in result.metadata['interpretation']

    def test_calculate_pe_ratio_mature_company(self):
        """Test P/E ratio for mature, stable company"""
        # Similar to utility or consumer staples
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=60.0,
            eps=4.0
        )

        assert result.is_valid is True
        assert result.value == 15.0
        assert 'Moderate P/E' in result.metadata['interpretation']

    def test_calculate_pe_ratio_financial_sector(self):
        """Test P/E ratio for financial sector company"""
        # Banks typically have lower P/E ratios
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=45.0,
            eps=5.0
        )

        assert result.is_valid is True
        assert result.value == 9.0
        assert 'Low P/E' in result.metadata['interpretation']

    def test_calculate_pe_ratio_high_growth_startup(self):
        """Test P/E ratio for high-growth startup"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=300.0,
            eps=2.0
        )

        assert result.is_valid is True
        assert result.value == 150.0
        assert 'Very high P/E' in result.metadata['interpretation']

    def test_calculate_pe_ratio_distressed_company(self):
        """Test P/E ratio for distressed company with losses"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=15.0,
            eps=-2.0
        )

        assert result.is_valid is False
        assert result.value == float('-inf')

    # =====================
    # P/E Interpretation Tests
    # =====================

    def test_pe_interpretation_ranges(self):
        """Test P/E ratio interpretation across different ranges"""
        test_cases = [
            (5.0, 'Low P/E'),
            (15.0, 'Moderate P/E'),
            (25.0, 'Elevated P/E'),
            (40.0, 'High P/E'),
            (100.0, 'Very high P/E')
        ]

        for stock_price, expected_interpretation in test_cases:
            result = self.engine.calculate_price_to_earnings_ratio(
                stock_price=stock_price,
                eps=1.0
            )
            assert result.is_valid is True
            assert expected_interpretation in result.metadata['interpretation']

    # =====================
    # Metadata Validation
    # =====================

    def test_calculate_pe_ratio_metadata_completeness(self):
        """Test that all expected metadata is present"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=180.0,
            eps=12.0
        )

        assert result.is_valid is True
        assert 'stock_price' in result.metadata
        assert 'eps' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata

    def test_calculate_pe_ratio_metadata_on_error(self):
        """Test that metadata is present even on negative EPS error"""
        result = self.engine.calculate_price_to_earnings_ratio(
            stock_price=100.0,
            eps=-5.0
        )

        assert result.is_valid is False
        assert 'stock_price' in result.metadata
        assert 'eps' in result.metadata
        assert 'calculation_method' in result.metadata


class TestPriceToSalesRatio:
    """Test suite for P/S ratio calculations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialCalculationEngine()

    # =====================
    # Basic P/S Ratio Tests - Market Cap Method
    # =====================

    def test_calculate_ps_ratio_market_cap_method(self):
        """Test P/S ratio using market cap method"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,  # $1B revenue
            shares_outstanding=100000000,  # 100M shares
            market_cap=2000000000  # $2B market cap
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert result.metadata['market_cap'] == 2000000000
        assert result.metadata['revenue'] == 1000000000
        assert 'Market Cap Method' in result.metadata['method_used']
        assert 'P/S Ratio = Market Cap / Revenue' in result.metadata['calculation_method']

    def test_calculate_ps_ratio_low_valuation(self):
        """Test P/S ratio indicating low valuation"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=5000000000,  # $5B revenue
            shares_outstanding=200000000,
            market_cap=3000000000  # $3B market cap (P/S = 0.6)
        )

        assert result.is_valid is True
        assert result.value == 0.6
        assert 'Very low P/S' in result.metadata['interpretation']

    def test_calculate_ps_ratio_high_valuation(self):
        """Test P/S ratio indicating high valuation"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=500000000,  # $500M revenue
            shares_outstanding=50000000,
            market_cap=6000000000  # $6B market cap (P/S = 12.0)
        )

        assert result.is_valid is True
        assert result.value == 12.0
        assert 'High P/S' in result.metadata['interpretation']

    def test_calculate_ps_ratio_moderate_valuation(self):
        """Test P/S ratio with moderate valuation"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=2000000000,  # $2B revenue
            shares_outstanding=100000000,
            market_cap=6000000000  # $6B market cap (P/S = 3.0)
        )

        assert result.is_valid is True
        assert result.value == 3.0
        assert 'Moderate P/S' in result.metadata['interpretation']

    # =====================
    # P/S Ratio Tests - Per Share Method
    # =====================

    def test_calculate_ps_ratio_per_share_method(self):
        """Test P/S ratio using per-share method"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,  # $1B revenue
            shares_outstanding=100000000,  # 100M shares
            stock_price=20.0  # $20 per share
        )

        # Revenue per share = $1B / 100M = $10
        # P/S = $20 / $10 = 2.0
        assert result.is_valid is True
        assert result.value == 2.0
        assert result.metadata['stock_price'] == 20.0
        assert result.metadata['revenue_per_share'] == 10.0
        assert 'Per Share Method' in result.metadata['method_used']
        assert 'P/S Ratio = Stock Price / (Revenue / Shares)' in result.metadata['calculation_method']

    def test_calculate_ps_ratio_per_share_fractional_values(self):
        """Test P/S ratio with fractional per-share values"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=750000000,  # $750M revenue
            shares_outstanding=125000000,  # 125M shares
            stock_price=18.0  # $18 per share
        )

        # Revenue per share = $750M / 125M = $6
        # P/S = $18 / $6 = 3.0
        assert result.is_valid is True
        assert result.value == 3.0
        assert result.metadata['revenue_per_share'] == 6.0

    def test_calculate_ps_ratio_high_revenue_per_share(self):
        """Test P/S ratio with high revenue per share (low P/S)"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=5000000000,  # $5B revenue
            shares_outstanding=100000000,  # 100M shares
            stock_price=40.0  # $40 per share
        )

        # Revenue per share = $5B / 100M = $50
        # P/S = $40 / $50 = 0.8
        assert result.is_valid is True
        assert result.value == 0.8
        assert 'Very low P/S' in result.metadata['interpretation']

    # =====================
    # Method Precedence Tests
    # =====================

    def test_calculate_ps_ratio_both_methods_provided(self):
        """Test that market cap method takes precedence when both are provided"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=100000000,
            stock_price=25.0,  # Would give different result
            market_cap=2000000000  # This should be used
        )

        assert result.is_valid is True
        assert result.value == 2.0  # Using market cap method
        assert 'Market Cap Method' in result.metadata['method_used']
        assert 'market_cap' in result.metadata
        assert 'stock_price' not in result.metadata

    # =====================
    # Input Validation Tests
    # =====================

    def test_calculate_ps_ratio_none_revenue(self):
        """Test P/S ratio with None revenue"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=None,
            shares_outstanding=100000000,
            market_cap=2000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Revenue and shares outstanding cannot be None" in result.error_message

    def test_calculate_ps_ratio_none_shares_outstanding(self):
        """Test P/S ratio with None shares outstanding"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=None,
            market_cap=2000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Revenue and shares outstanding cannot be None" in result.error_message

    def test_calculate_ps_ratio_zero_revenue(self):
        """Test P/S ratio with zero revenue"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=0,
            shares_outstanding=100000000,
            market_cap=2000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Revenue must be positive" in result.error_message

    def test_calculate_ps_ratio_negative_revenue(self):
        """Test P/S ratio with negative revenue"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=-1000000000,
            shares_outstanding=100000000,
            market_cap=2000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Revenue must be positive" in result.error_message

    def test_calculate_ps_ratio_zero_shares_outstanding(self):
        """Test P/S ratio with zero shares outstanding"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=0,
            market_cap=2000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Shares outstanding must be positive" in result.error_message

    def test_calculate_ps_ratio_negative_shares_outstanding(self):
        """Test P/S ratio with negative shares outstanding"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=-100000000,
            market_cap=2000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Shares outstanding must be positive" in result.error_message

    def test_calculate_ps_ratio_no_price_or_market_cap(self):
        """Test P/S ratio when neither stock_price nor market_cap is provided"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=100000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Either stock_price or market_cap must be provided" in result.error_message

    def test_calculate_ps_ratio_zero_market_cap(self):
        """Test P/S ratio with zero market cap"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=100000000,
            market_cap=0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Market cap must be positive" in result.error_message

    def test_calculate_ps_ratio_negative_market_cap(self):
        """Test P/S ratio with negative market cap"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=100000000,
            market_cap=-2000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Market cap must be positive" in result.error_message

    def test_calculate_ps_ratio_zero_stock_price(self):
        """Test P/S ratio with zero stock price"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=100000000,
            stock_price=0.0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Stock price must be positive" in result.error_message

    def test_calculate_ps_ratio_negative_stock_price(self):
        """Test P/S ratio with negative stock price"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=100000000,
            stock_price=-20.0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Stock price must be positive" in result.error_message

    # =====================
    # Real-world Scenarios
    # =====================

    def test_calculate_ps_ratio_tech_company(self):
        """Test P/S ratio for typical SaaS/tech company"""
        # Similar to high-growth SaaS: $500M revenue, $5B market cap
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=500000000,
            shares_outstanding=100000000,
            market_cap=5000000000
        )

        assert result.is_valid is True
        assert result.value == 10.0
        assert 'High P/S' in result.metadata['interpretation']

    def test_calculate_ps_ratio_retail_company(self):
        """Test P/S ratio for retail company (typically low P/S)"""
        # Similar to traditional retail: $10B revenue, $8B market cap
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=10000000000,
            shares_outstanding=200000000,
            market_cap=8000000000
        )

        assert result.is_valid is True
        assert result.value == 0.8
        assert 'Very low P/S' in result.metadata['interpretation']

    def test_calculate_ps_ratio_mature_tech_company(self):
        """Test P/S ratio for mature tech company"""
        # Similar to Microsoft: $200B revenue, $3T market cap
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=200000000000,
            shares_outstanding=7500000000,
            market_cap=3000000000000
        )

        assert result.is_valid is True
        assert result.value == 15.0
        assert 'High P/S' in result.metadata['interpretation']

    def test_calculate_ps_ratio_industrial_company(self):
        """Test P/S ratio for industrial/manufacturing company"""
        # Typically low-margin, low P/S
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=5000000000,
            shares_outstanding=250000000,
            stock_price=30.0
        )

        # Revenue per share = $5B / 250M = $20
        # P/S = $30 / $20 = 1.5
        assert result.is_valid is True
        assert result.value == 1.5
        assert 'Low P/S' in result.metadata['interpretation']

    def test_calculate_ps_ratio_startup_pre_revenue(self):
        """Test P/S ratio for early-stage startup with minimal revenue"""
        # Very high P/S for pre-profit companies
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=10000000,  # $10M revenue
            shares_outstanding=50000000,
            market_cap=500000000  # $500M market cap
        )

        assert result.is_valid is True
        assert result.value == 50.0
        assert 'High P/S' in result.metadata['interpretation']

    def test_calculate_ps_ratio_value_stock(self):
        """Test P/S ratio for undervalued stock"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=20000000000,  # $20B revenue
            shares_outstanding=1000000000,
            market_cap=25000000000  # $25B market cap (P/S = 1.25)
        )

        assert result.is_valid is True
        assert result.value == 1.25
        assert 'Low P/S' in result.metadata['interpretation']

    # =====================
    # P/S Interpretation Tests
    # =====================

    def test_ps_interpretation_ranges(self):
        """Test P/S ratio interpretation across different ranges"""
        test_cases = [
            (0.5, 'Very low P/S'),
            (1.5, 'Low P/S'),
            (3.0, 'Moderate P/S'),
            (7.0, 'Elevated P/S'),
            (15.0, 'High P/S')
        ]

        for market_cap_multiplier, expected_interpretation in test_cases:
            result = self.engine.calculate_price_to_sales_ratio(
                revenue=1000000000,
                shares_outstanding=100000000,
                market_cap=market_cap_multiplier * 1000000000
            )
            assert result.is_valid is True
            assert expected_interpretation in result.metadata['interpretation']

    # =====================
    # Edge Cases
    # =====================

    def test_calculate_ps_ratio_very_small_revenue(self):
        """Test P/S ratio with very small revenue"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=100000,  # $100K revenue (early startup)
            shares_outstanding=10000000,
            market_cap=10000000  # $10M market cap
        )

        assert result.is_valid is True
        assert result.value == 100.0
        assert 'High P/S' in result.metadata['interpretation']

    def test_calculate_ps_ratio_very_large_values(self):
        """Test P/S ratio with very large values"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=500000000000,  # $500B revenue (mega-cap)
            shares_outstanding=10000000000,
            market_cap=3000000000000  # $3T market cap
        )

        assert result.is_valid is True
        assert result.value == 6.0

    def test_calculate_ps_ratio_precision(self):
        """Test P/S ratio calculation precision"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=123456789,
            shares_outstanding=234567890,
            stock_price=12.34
        )

        revenue_per_share = 123456789 / 234567890
        expected_ps = 12.34 / revenue_per_share
        assert result.is_valid is True
        assert result.value == pytest.approx(expected_ps, rel=1e-9)

    # =====================
    # Metadata Validation
    # =====================

    def test_calculate_ps_ratio_metadata_completeness_market_cap(self):
        """Test that all expected metadata is present for market cap method"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=100000000,
            market_cap=2000000000
        )

        assert result.is_valid is True
        assert 'market_cap' in result.metadata
        assert 'revenue' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata
        assert 'method_used' in result.metadata

    def test_calculate_ps_ratio_metadata_completeness_per_share(self):
        """Test that all expected metadata is present for per-share method"""
        result = self.engine.calculate_price_to_sales_ratio(
            revenue=1000000000,
            shares_outstanding=100000000,
            stock_price=20.0
        )

        assert result.is_valid is True
        assert 'stock_price' in result.metadata
        assert 'revenue' in result.metadata
        assert 'shares_outstanding' in result.metadata
        assert 'revenue_per_share' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata
        assert 'method_used' in result.metadata


class TestPriceToCashFlowRatio:
    """Test suite for P/CF ratio calculations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialCalculationEngine()

    # =====================
    # Basic P/CF Ratio Tests - Market Cap Method
    # =====================

    def test_calculate_pcf_ratio_market_cap_method(self):
        """Test P/CF ratio using market cap method"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,  # $500M operating cash flow
            shares_outstanding=100000000,  # 100M shares
            market_cap=5000000000  # $5B market cap
        )

        assert result.is_valid is True
        assert result.value == 10.0
        assert result.metadata['market_cap'] == 5000000000
        assert result.metadata['operating_cash_flow'] == 500000000
        assert 'Market Cap Method' in result.metadata['method_used']
        assert 'P/CF Ratio = Market Cap / Operating Cash Flow' in result.metadata['calculation_method']

    def test_calculate_pcf_ratio_low_valuation(self):
        """Test P/CF ratio indicating low valuation"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=2000000000,  # $2B operating cash flow
            shares_outstanding=200000000,
            market_cap=6000000000  # $6B market cap (P/CF = 3.0)
        )

        assert result.is_valid is True
        assert result.value == 3.0
        assert 'Very low P/CF' in result.metadata['interpretation']

    def test_calculate_pcf_ratio_high_valuation(self):
        """Test P/CF ratio indicating high valuation"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=200000000,  # $200M operating cash flow
            shares_outstanding=50000000,
            market_cap=6000000000  # $6B market cap (P/CF = 30.0)
        )

        assert result.is_valid is True
        assert result.value == 30.0
        assert 'High P/CF' in result.metadata['interpretation']

    def test_calculate_pcf_ratio_moderate_valuation(self):
        """Test P/CF ratio with moderate valuation"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=1000000000,  # $1B operating cash flow
            shares_outstanding=100000000,
            market_cap=12000000000  # $12B market cap (P/CF = 12.0)
        )

        assert result.is_valid is True
        assert result.value == 12.0
        assert 'Moderate P/CF' in result.metadata['interpretation']

    # =====================
    # P/CF Ratio Tests - Per Share Method
    # =====================

    def test_calculate_pcf_ratio_per_share_method(self):
        """Test P/CF ratio using per-share method"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,  # $500M operating cash flow
            shares_outstanding=100000000,  # 100M shares
            stock_price=50.0  # $50 per share
        )

        # Cash flow per share = $500M / 100M = $5
        # P/CF = $50 / $5 = 10.0
        assert result.is_valid is True
        assert result.value == 10.0
        assert result.metadata['stock_price'] == 50.0
        assert result.metadata['cash_flow_per_share'] == 5.0
        assert 'Per Share Method' in result.metadata['method_used']
        assert 'P/CF Ratio = Stock Price / (Operating Cash Flow / Shares)' in result.metadata['calculation_method']

    def test_calculate_pcf_ratio_per_share_fractional_values(self):
        """Test P/CF ratio with fractional per-share values"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=750000000,  # $750M operating cash flow
            shares_outstanding=125000000,  # 125M shares
            stock_price=60.0  # $60 per share
        )

        # Cash flow per share = $750M / 125M = $6
        # P/CF = $60 / $6 = 10.0
        assert result.is_valid is True
        assert result.value == 10.0
        assert result.metadata['cash_flow_per_share'] == 6.0

    def test_calculate_pcf_ratio_high_cash_flow_per_share(self):
        """Test P/CF ratio with high cash flow per share (low P/CF)"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=5000000000,  # $5B operating cash flow
            shares_outstanding=100000000,  # 100M shares
            stock_price=200.0  # $200 per share
        )

        # Cash flow per share = $5B / 100M = $50
        # P/CF = $200 / $50 = 4.0
        assert result.is_valid is True
        assert result.value == 4.0
        assert 'Very low P/CF' in result.metadata['interpretation']

    # =====================
    # Method Precedence Tests
    # =====================

    def test_calculate_pcf_ratio_both_methods_provided(self):
        """Test that market cap method takes precedence when both are provided"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=100000000,
            stock_price=60.0,  # Would give different result
            market_cap=5000000000  # This should be used
        )

        assert result.is_valid is True
        assert result.value == 10.0  # Using market cap method
        assert 'Market Cap Method' in result.metadata['method_used']
        assert 'market_cap' in result.metadata
        assert 'stock_price' not in result.metadata

    # =====================
    # Input Validation Tests
    # =====================

    def test_calculate_pcf_ratio_none_operating_cash_flow(self):
        """Test P/CF ratio with None operating cash flow"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=None,
            shares_outstanding=100000000,
            market_cap=5000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Operating cash flow and shares outstanding cannot be None" in result.error_message

    def test_calculate_pcf_ratio_none_shares_outstanding(self):
        """Test P/CF ratio with None shares outstanding"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=None,
            market_cap=5000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Operating cash flow and shares outstanding cannot be None" in result.error_message

    def test_calculate_pcf_ratio_zero_operating_cash_flow(self):
        """Test P/CF ratio with zero operating cash flow"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=0,
            shares_outstanding=100000000,
            market_cap=5000000000
        )

        assert result.is_valid is False
        assert result.value == float('inf')
        assert "undefined for zero operating cash flow" in result.error_message

    def test_calculate_pcf_ratio_negative_operating_cash_flow(self):
        """Test P/CF ratio with negative operating cash flow (cash burning)"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=-500000000,
            shares_outstanding=100000000,
            market_cap=5000000000
        )

        assert result.is_valid is False
        assert result.value == float('-inf')
        assert "company is burning cash" in result.error_message

    def test_calculate_pcf_ratio_zero_shares_outstanding(self):
        """Test P/CF ratio with zero shares outstanding"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=0,
            market_cap=5000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Shares outstanding must be positive" in result.error_message

    def test_calculate_pcf_ratio_negative_shares_outstanding(self):
        """Test P/CF ratio with negative shares outstanding"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=-100000000,
            market_cap=5000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Shares outstanding must be positive" in result.error_message

    def test_calculate_pcf_ratio_no_price_or_market_cap(self):
        """Test P/CF ratio when neither stock_price nor market_cap is provided"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=100000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Either stock_price or market_cap must be provided" in result.error_message

    def test_calculate_pcf_ratio_zero_market_cap(self):
        """Test P/CF ratio with zero market cap"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=100000000,
            market_cap=0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Market cap must be positive" in result.error_message

    def test_calculate_pcf_ratio_negative_market_cap(self):
        """Test P/CF ratio with negative market cap"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=100000000,
            market_cap=-5000000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Market cap must be positive" in result.error_message

    def test_calculate_pcf_ratio_zero_stock_price(self):
        """Test P/CF ratio with zero stock price"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=100000000,
            stock_price=0.0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Stock price must be positive" in result.error_message

    def test_calculate_pcf_ratio_negative_stock_price(self):
        """Test P/CF ratio with negative stock price"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=100000000,
            stock_price=-50.0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Stock price must be positive" in result.error_message

    # =====================
    # Real-world Scenarios
    # =====================

    def test_calculate_pcf_ratio_tech_company(self):
        """Test P/CF ratio for typical tech company with strong cash generation"""
        # Similar to Apple: Strong operating cash flow
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=100000000000,  # $100B operating cash flow
            shares_outstanding=15500000000,
            market_cap=3000000000000  # $3T market cap
        )

        assert result.is_valid is True
        assert result.value == 30.0
        assert 'High P/CF' in result.metadata['interpretation']

    def test_calculate_pcf_ratio_mature_company(self):
        """Test P/CF ratio for mature company with steady cash flow"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=5000000000,  # $5B operating cash flow
            shares_outstanding=500000000,
            market_cap=50000000000  # $50B market cap
        )

        assert result.is_valid is True
        assert result.value == 10.0
        assert 'Moderate P/CF' in result.metadata['interpretation']

    def test_calculate_pcf_ratio_value_stock(self):
        """Test P/CF ratio for undervalued stock with strong cash generation"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=10000000000,  # $10B operating cash flow
            shares_outstanding=1000000000,
            market_cap=30000000000  # $30B market cap (P/CF = 3.0)
        )

        assert result.is_valid is True
        assert result.value == 3.0
        assert 'Very low P/CF' in result.metadata['interpretation']

    def test_calculate_pcf_ratio_growth_company(self):
        """Test P/CF ratio for growth company with limited cash generation"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=100000000,  # $100M operating cash flow
            shares_outstanding=50000000,
            stock_price=80.0
        )

        # Cash flow per share = $100M / 50M = $2
        # P/CF = $80 / $2 = 40.0
        assert result.is_valid is True
        assert result.value == 40.0
        assert 'High P/CF' in result.metadata['interpretation']

    def test_calculate_pcf_ratio_industrial_company(self):
        """Test P/CF ratio for industrial company with moderate cash flow"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=2000000000,  # $2B operating cash flow
            shares_outstanding=200000000,
            stock_price=100.0
        )

        # Cash flow per share = $2B / 200M = $10
        # P/CF = $100 / $10 = 10.0
        assert result.is_valid is True
        assert result.value == 10.0
        assert 'Moderate P/CF' in result.metadata['interpretation']

    def test_calculate_pcf_ratio_startup_burning_cash(self):
        """Test P/CF ratio for startup burning cash (negative operating cash flow)"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=-50000000,  # -$50M (burning cash)
            shares_outstanding=100000000,
            market_cap=1000000000
        )

        assert result.is_valid is False
        assert result.value == float('-inf')
        assert 'burning cash' in result.error_message

    # =====================
    # P/CF Interpretation Tests
    # =====================

    def test_pcf_interpretation_ranges(self):
        """Test P/CF ratio interpretation across different ranges"""
        test_cases = [
            (3.0, 'Very low P/CF'),
            (7.0, 'Low P/CF'),
            (12.0, 'Moderate P/CF'),
            (20.0, 'Elevated P/CF'),
            (30.0, 'High P/CF')
        ]

        for market_cap_multiplier, expected_interpretation in test_cases:
            result = self.engine.calculate_price_to_cash_flow_ratio(
                operating_cash_flow=1000000000,
                shares_outstanding=100000000,
                market_cap=market_cap_multiplier * 1000000000
            )
            assert result.is_valid is True
            assert expected_interpretation in result.metadata['interpretation']

    # =====================
    # Edge Cases
    # =====================

    def test_calculate_pcf_ratio_very_small_cash_flow(self):
        """Test P/CF ratio with very small operating cash flow"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=1000000,  # $1M operating cash flow (early stage)
            shares_outstanding=10000000,
            market_cap=100000000  # $100M market cap
        )

        assert result.is_valid is True
        assert result.value == 100.0
        assert 'High P/CF' in result.metadata['interpretation']

    def test_calculate_pcf_ratio_very_large_values(self):
        """Test P/CF ratio with very large values"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=200000000000,  # $200B operating cash flow
            shares_outstanding=10000000000,
            market_cap=3000000000000  # $3T market cap
        )

        assert result.is_valid is True
        assert result.value == 15.0

    def test_calculate_pcf_ratio_precision(self):
        """Test P/CF ratio calculation precision"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=123456789,
            shares_outstanding=234567890,
            stock_price=12.34
        )

        cash_flow_per_share = 123456789 / 234567890
        expected_pcf = 12.34 / cash_flow_per_share
        assert result.is_valid is True
        assert result.value == pytest.approx(expected_pcf, rel=1e-9)

    # =====================
    # Metadata Validation
    # =====================

    def test_calculate_pcf_ratio_metadata_completeness_market_cap(self):
        """Test that all expected metadata is present for market cap method"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=100000000,
            market_cap=5000000000
        )

        assert result.is_valid is True
        assert 'market_cap' in result.metadata
        assert 'operating_cash_flow' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata
        assert 'method_used' in result.metadata

    def test_calculate_pcf_ratio_metadata_completeness_per_share(self):
        """Test that all expected metadata is present for per-share method"""
        result = self.engine.calculate_price_to_cash_flow_ratio(
            operating_cash_flow=500000000,
            shares_outstanding=100000000,
            stock_price=50.0
        )

        assert result.is_valid is True
        assert 'stock_price' in result.metadata
        assert 'operating_cash_flow' in result.metadata
        assert 'shares_outstanding' in result.metadata
        assert 'cash_flow_per_share' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata
        assert 'method_used' in result.metadata


class TestEnterpriseValueToEBITDA:
    """Test suite for EV/EBITDA ratio calculations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialCalculationEngine()

    # =====================
    # Basic EV/EBITDA Tests
    # =====================

    def test_calculate_ev_ebitda_normal_case(self):
        """Test EV/EBITDA calculation with typical values"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=1000000000,  # $1B EBITDA
            market_cap=10000000000,  # $10B market cap
            total_debt=2000000000,  # $2B debt
            cash_and_equivalents=500000000  # $500M cash
        )

        # EV = $10B + $2B - $500M = $11.5B
        # EV/EBITDA = $11.5B / $1B = 11.5
        assert result.is_valid is True
        assert result.value == 11.5
        assert result.metadata['enterprise_value'] == 11500000000
        assert result.metadata['ebitda'] == 1000000000
        assert result.metadata['market_cap'] == 10000000000
        assert result.metadata['total_debt'] == 2000000000
        assert result.metadata['cash_and_equivalents'] == 500000000
        assert 'EV/EBITDA' in result.metadata['calculation_method']
        assert 'Moderate EV/EBITDA' in result.metadata['interpretation']

    def test_calculate_ev_ebitda_low_valuation(self):
        """Test EV/EBITDA indicating low valuation"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=2000000000,  # $2B EBITDA
            market_cap=6000000000,  # $6B market cap
            total_debt=1000000000,  # $1B debt
            cash_and_equivalents=500000000  # $500M cash
        )

        # EV = $6B + $1B - $500M = $6.5B
        # EV/EBITDA = $6.5B / $2B = 3.25
        assert result.is_valid is True
        assert result.value == 3.25
        assert 'Very low EV/EBITDA' in result.metadata['interpretation']

    def test_calculate_ev_ebitda_high_valuation(self):
        """Test EV/EBITDA indicating high valuation"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=500000000,  # $500M EBITDA
            market_cap=15000000000,  # $15B market cap
            total_debt=5000000000,  # $5B debt
            cash_and_equivalents=1000000000  # $1B cash
        )

        # EV = $15B + $5B - $1B = $19B
        # EV/EBITDA = $19B / $500M = 38
        assert result.is_valid is True
        assert result.value == 38.0
        assert 'High EV/EBITDA' in result.metadata['interpretation']

    def test_calculate_ev_ebitda_no_debt(self):
        """Test EV/EBITDA with debt-free company"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=1000000000,  # $1B EBITDA
            market_cap=8000000000,  # $8B market cap
            total_debt=0,  # No debt
            cash_and_equivalents=2000000000  # $2B cash
        )

        # EV = $8B + $0 - $2B = $6B
        # EV/EBITDA = $6B / $1B = 6.0
        assert result.is_valid is True
        assert result.value == 6.0
        assert result.metadata['total_debt'] == 0
        assert 'Low EV/EBITDA' in result.metadata['interpretation']

    def test_calculate_ev_ebitda_high_debt(self):
        """Test EV/EBITDA with highly leveraged company"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=1000000000,  # $1B EBITDA
            market_cap=5000000000,  # $5B market cap
            total_debt=10000000000,  # $10B debt (2x market cap)
            cash_and_equivalents=500000000  # $500M cash
        )

        # EV = $5B + $10B - $500M = $14.5B
        # EV/EBITDA = $14.5B / $1B = 14.5
        assert result.is_valid is True
        assert result.value == 14.5
        assert result.metadata['total_debt'] == 10000000000

    def test_calculate_ev_ebitda_cash_rich_company(self):
        """Test EV/EBITDA with cash-rich company"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=2000000000,  # $2B EBITDA
            market_cap=10000000000,  # $10B market cap
            total_debt=1000000000,  # $1B debt
            cash_and_equivalents=5000000000  # $5B cash
        )

        # EV = $10B + $1B - $5B = $6B
        # EV/EBITDA = $6B / $2B = 3.0
        assert result.is_valid is True
        assert result.value == 3.0
        assert 'Very low EV/EBITDA' in result.metadata['interpretation']

    # =====================
    # Edge Cases - Negative/Zero EBITDA
    # =====================

    def test_calculate_ev_ebitda_zero_ebitda(self):
        """Test EV/EBITDA with zero EBITDA (undefined)"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=0,
            market_cap=5000000000,
            total_debt=1000000000,
            cash_and_equivalents=500000000
        )

        assert result.is_valid is False
        assert result.value == float('inf')
        assert "undefined for zero EBITDA" in result.error_message

    def test_calculate_ev_ebitda_negative_ebitda(self):
        """Test EV/EBITDA with negative EBITDA (operating losses)"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=-500000000,  # -$500M EBITDA (losses)
            market_cap=5000000000,
            total_debt=1000000000,
            cash_and_equivalents=500000000
        )

        assert result.is_valid is False
        assert result.value == float('-inf')
        assert "operating losses" in result.error_message

    # =====================
    # Input Validation Tests
    # =====================

    def test_calculate_ev_ebitda_none_ebitda(self):
        """Test EV/EBITDA with None EBITDA"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=None,
            market_cap=5000000000,
            total_debt=1000000000,
            cash_and_equivalents=500000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "cannot be None" in result.error_message

    def test_calculate_ev_ebitda_none_market_cap(self):
        """Test EV/EBITDA with None market cap"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=1000000000,
            market_cap=None,
            total_debt=1000000000,
            cash_and_equivalents=500000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "cannot be None" in result.error_message

    def test_calculate_ev_ebitda_none_total_debt(self):
        """Test EV/EBITDA with None total debt"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=1000000000,
            market_cap=5000000000,
            total_debt=None,
            cash_and_equivalents=500000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "cannot be None" in result.error_message

    def test_calculate_ev_ebitda_none_cash(self):
        """Test EV/EBITDA with None cash"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=1000000000,
            market_cap=5000000000,
            total_debt=1000000000,
            cash_and_equivalents=None
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "cannot be None" in result.error_message

    def test_calculate_ev_ebitda_zero_market_cap(self):
        """Test EV/EBITDA with zero market cap"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=1000000000,
            market_cap=0,
            total_debt=1000000000,
            cash_and_equivalents=500000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Market cap must be positive" in result.error_message

    def test_calculate_ev_ebitda_negative_market_cap(self):
        """Test EV/EBITDA with negative market cap"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=1000000000,
            market_cap=-5000000000,
            total_debt=1000000000,
            cash_and_equivalents=500000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Market cap must be positive" in result.error_message

    # =====================
    # Real-world Scenarios
    # =====================

    def test_calculate_ev_ebitda_tech_company(self):
        """Test EV/EBITDA for typical tech company"""
        # Similar to Apple-like: Strong cash position
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=120000000000,  # $120B EBITDA
            market_cap=3000000000000,  # $3T market cap
            total_debt=120000000000,  # $120B debt
            cash_and_equivalents=160000000000  # $160B cash
        )

        # EV = $3T + $120B - $160B = $2.96T
        # EV/EBITDA = $2.96T / $120B ≈ 24.67
        assert result.is_valid is True
        assert abs(result.value - 24.67) < 0.1
        assert 'High EV/EBITDA' in result.metadata['interpretation']

    def test_calculate_ev_ebitda_mature_industrial(self):
        """Test EV/EBITDA for mature industrial company"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=5000000000,  # $5B EBITDA
            market_cap=40000000000,  # $40B market cap
            total_debt=15000000000,  # $15B debt
            cash_and_equivalents=3000000000  # $3B cash
        )

        # EV = $40B + $15B - $3B = $52B
        # EV/EBITDA = $52B / $5B = 10.4
        assert result.is_valid is True
        assert result.value == 10.4
        assert 'Moderate EV/EBITDA' in result.metadata['interpretation']

    def test_calculate_ev_ebitda_utility_company(self):
        """Test EV/EBITDA for utility company (typically high debt)"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=3000000000,  # $3B EBITDA
            market_cap=20000000000,  # $20B market cap
            total_debt=30000000000,  # $30B debt (high leverage)
            cash_and_equivalents=1000000000  # $1B cash
        )

        # EV = $20B + $30B - $1B = $49B
        # EV/EBITDA = $49B / $3B ≈ 16.33
        assert result.is_valid is True
        assert abs(result.value - 16.33) < 0.1
        assert 'Elevated EV/EBITDA' in result.metadata['interpretation']

    def test_calculate_ev_ebitda_value_stock(self):
        """Test EV/EBITDA for undervalued stock"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=10000000000,  # $10B EBITDA
            market_cap=50000000000,  # $50B market cap
            total_debt=20000000000,  # $20B debt
            cash_and_equivalents=10000000000  # $10B cash
        )

        # EV = $50B + $20B - $10B = $60B
        # EV/EBITDA = $60B / $10B = 6.0
        assert result.is_valid is True
        assert result.value == 6.0
        assert 'Low EV/EBITDA' in result.metadata['interpretation']

    def test_calculate_ev_ebitda_growth_company(self):
        """Test EV/EBITDA for high-growth company"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=200000000,  # $200M EBITDA
            market_cap=10000000000,  # $10B market cap
            total_debt=500000000,  # $500M debt
            cash_and_equivalents=1000000000  # $1B cash
        )

        # EV = $10B + $500M - $1B = $9.5B
        # EV/EBITDA = $9.5B / $200M = 47.5
        assert result.is_valid is True
        assert result.value == 47.5
        assert 'High EV/EBITDA' in result.metadata['interpretation']

    def test_calculate_ev_ebitda_distressed_company(self):
        """Test EV/EBITDA for distressed company with negative EBITDA"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=-1000000000,  # -$1B EBITDA (losses)
            market_cap=2000000000,  # $2B market cap
            total_debt=5000000000,  # $5B debt
            cash_and_equivalents=500000000  # $500M cash
        )

        assert result.is_valid is False
        assert result.value == float('-inf')

    # =====================
    # Enterprise Value Edge Cases
    # =====================

    def test_calculate_ev_ebitda_negative_enterprise_value(self):
        """Test EV/EBITDA when cash exceeds market cap plus debt"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=1000000000,  # $1B EBITDA
            market_cap=5000000000,  # $5B market cap
            total_debt=1000000000,  # $1B debt
            cash_and_equivalents=10000000000  # $10B cash (exceeds EV)
        )

        # EV = $5B + $1B - $10B = -$4B
        # EV/EBITDA = -$4B / $1B = -4.0
        assert result.is_valid is True
        assert result.value == -4.0
        assert result.metadata['enterprise_value'] == -4000000000

    def test_calculate_ev_ebitda_precision(self):
        """Test EV/EBITDA calculation precision"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=123456789,
            market_cap=2345678901,
            total_debt=345678901,
            cash_and_equivalents=123456789
        )

        expected_ev = 2345678901 + 345678901 - 123456789
        expected_ev_ebitda = expected_ev / 123456789
        assert result.is_valid is True
        assert result.value == pytest.approx(expected_ev_ebitda, rel=1e-9)
        assert result.metadata['enterprise_value'] == expected_ev

    # =====================
    # EV/EBITDA Interpretation Tests
    # =====================

    def test_ev_ebitda_interpretation_ranges(self):
        """Test EV/EBITDA interpretation across different ranges"""
        test_cases = [
            (4.0, 'Very low EV/EBITDA'),
            (8.0, 'Low EV/EBITDA'),
            (12.0, 'Moderate EV/EBITDA'),
            (18.0, 'Elevated EV/EBITDA'),
            (25.0, 'High EV/EBITDA')
        ]

        ebitda = 1000000000  # $1B
        total_debt = 2000000000  # $2B
        cash = 500000000  # $500M

        for ev_multiple, expected_interpretation in test_cases:
            # Calculate required market cap to achieve target EV/EBITDA
            # EV = market_cap + debt - cash
            # ev_multiple = EV / ebitda
            # market_cap = (ev_multiple * ebitda) - debt + cash
            target_ev = ev_multiple * ebitda
            market_cap = target_ev - total_debt + cash

            result = self.engine.calculate_enterprise_value_to_ebitda(
                ebitda=ebitda,
                market_cap=market_cap,
                total_debt=total_debt,
                cash_and_equivalents=cash
            )
            assert result.is_valid is True
            assert expected_interpretation in result.metadata['interpretation']

    # =====================
    # Metadata Validation
    # =====================

    def test_calculate_ev_ebitda_metadata_completeness(self):
        """Test that all expected metadata is present"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=1000000000,
            market_cap=10000000000,
            total_debt=2000000000,
            cash_and_equivalents=500000000
        )

        assert result.is_valid is True
        assert 'ebitda' in result.metadata
        assert 'market_cap' in result.metadata
        assert 'total_debt' in result.metadata
        assert 'cash_and_equivalents' in result.metadata
        assert 'enterprise_value' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata

    def test_calculate_ev_ebitda_metadata_on_error(self):
        """Test that metadata is present even on negative EBITDA error"""
        result = self.engine.calculate_enterprise_value_to_ebitda(
            ebitda=-500000000,
            market_cap=5000000000,
            total_debt=1000000000,
            cash_and_equivalents=500000000
        )

        assert result.is_valid is False
        assert 'ebitda' in result.metadata
        assert 'market_cap' in result.metadata
        assert 'total_debt' in result.metadata
        assert 'cash_and_equivalents' in result.metadata
        assert 'enterprise_value' in result.metadata
        assert 'calculation_method' in result.metadata
