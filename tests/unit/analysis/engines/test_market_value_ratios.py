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
