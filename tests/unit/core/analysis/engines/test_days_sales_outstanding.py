"""
Unit tests for Days Sales Outstanding (DSO) calculation in FinancialCalculationEngine.

Tests cover:
- Basic DSO calculation using pre-calculated receivables turnover
- DSO calculation with automatic receivables turnover computation
- Different period lengths (annual, quarterly, monthly)
- Edge cases (zero turnover, infinite turnover, negative values)
- Cash-based business scenarios
- High and low DSO warnings
"""

import pytest
from core.analysis.engines.financial_calculation_engine import FinancialCalculationEngine


class TestDaysSalesOutstanding:
    """Test suite for Days Sales Outstanding (DSO) calculations"""

    @pytest.fixture
    def calculator(self):
        """Create a FinancialCalculationEngine instance for testing"""
        return FinancialCalculationEngine()

    # =====================
    # Basic DSO Calculations
    # =====================

    def test_dso_with_provided_turnover(self, calculator):
        """Test DSO calculation using pre-calculated receivables turnover"""
        # Receivables turnover of 12 means revenue is collected 12 times per year
        # DSO = 365 / 12 = 30.42 days
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=12.0,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(30.42, rel=0.01)
        assert result.metadata['receivables_turnover'] == 12.0
        assert result.metadata['days_in_period'] == 365
        assert 'collection efficiency' in result.metadata['interpretation']

    def test_dso_with_calculated_turnover(self, calculator):
        """Test DSO calculation with automatic receivables turnover computation"""
        # Revenue: 1,200,000, Receivables: 100,000
        # Receivables turnover = 1,200,000 / 100,000 = 12
        # DSO = 365 / 12 = 30.42 days
        result = calculator.calculate_days_sales_outstanding(
            revenue=1_200_000,
            accounts_receivable=100_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(30.42, rel=0.01)
        assert result.metadata['revenue'] == 1_200_000
        assert result.metadata['accounts_receivable'] == 100_000

    def test_dso_with_average_receivables(self, calculator):
        """Test DSO calculation using average receivables"""
        # Revenue: 1,200,000, Average Receivables: 150,000
        # Receivables turnover = 1,200,000 / 150,000 = 8
        # DSO = 365 / 8 = 45.625 days
        result = calculator.calculate_days_sales_outstanding(
            revenue=1_200_000,
            average_receivables=150_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(45.625, rel=0.01)
        assert result.metadata['average_receivables'] == 150_000
        assert 'collection efficiency' in result.metadata['interpretation']

    def test_dso_with_beginning_and_ending_receivables(self, calculator):
        """Test DSO calculation using beginning and ending receivables"""
        # Revenue: 1,200,000, Beginning: 120,000, Ending: 180,000
        # Average Receivables = (120,000 + 180,000) / 2 = 150,000
        # Receivables turnover = 1,200,000 / 150,000 = 8
        # DSO = 365 / 8 = 45.625 days
        result = calculator.calculate_days_sales_outstanding(
            revenue=1_200_000,
            beginning_receivables=120_000,
            ending_receivables=180_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(45.625, rel=0.01)

    # =====================
    # Different Period Lengths
    # =====================

    def test_dso_quarterly_period(self, calculator):
        """Test DSO calculation for quarterly period"""
        # Receivables turnover of 3 in a quarter (12 annualized)
        # DSO = 90 / 3 = 30 days
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=3.0,
            days_in_period=90
        )

        assert result.is_valid
        assert result.value == pytest.approx(30.0, rel=0.01)
        assert result.metadata['days_in_period'] == 90

    def test_dso_monthly_period(self, calculator):
        """Test DSO calculation for monthly period"""
        # Receivables turnover of 1 in a month (12 annualized)
        # DSO = 30 / 1 = 30 days
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=1.0,
            days_in_period=30
        )

        assert result.is_valid
        assert result.value == pytest.approx(30.0, rel=0.01)
        assert result.metadata['days_in_period'] == 30

    # =====================
    # Edge Cases
    # =====================

    def test_dso_zero_turnover(self, calculator):
        """Test DSO with zero receivables turnover"""
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=0.0,
            days_in_period=365
        )

        assert not result.is_valid
        assert "Receivables turnover cannot be zero" in result.error_message

    def test_dso_infinite_turnover_cash_business(self, calculator):
        """Test DSO with infinite turnover (cash-based business)"""
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=float('inf'),
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == 0.0
        assert 'cash' in result.metadata['interpretation'].lower()

    def test_dso_negative_turnover(self, calculator, caplog):
        """Test DSO with negative receivables turnover"""
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=-5.0,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value < 0
        # Check that warning was logged
        assert "Negative receivables turnover" in caplog.text

    def test_dso_invalid_days_period(self, calculator):
        """Test DSO with invalid days in period"""
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=12.0,
            days_in_period=0
        )

        assert not result.is_valid
        assert "Days in period must be positive" in result.error_message

    def test_dso_negative_days_period(self, calculator):
        """Test DSO with negative days in period"""
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=12.0,
            days_in_period=-365
        )

        assert not result.is_valid
        assert "Days in period must be positive" in result.error_message

    # =====================
    # Missing Input Cases
    # =====================

    def test_dso_missing_all_inputs(self, calculator):
        """Test DSO with missing all required inputs"""
        result = calculator.calculate_days_sales_outstanding(
            days_in_period=365
        )

        assert not result.is_valid
        assert "Failed to calculate receivables turnover" in result.error_message

    def test_dso_missing_revenue(self, calculator):
        """Test DSO with missing revenue"""
        result = calculator.calculate_days_sales_outstanding(
            accounts_receivable=100_000,
            days_in_period=365
        )

        assert not result.is_valid
        assert "Failed to calculate receivables turnover" in result.error_message

    # =====================
    # Warning Thresholds
    # =====================

    def test_dso_high_value_warning(self, calculator, caplog):
        """Test DSO with high value triggers warning"""
        # Very low turnover results in high DSO
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=3.0,  # 365 / 3 = 121.67 days
            days_in_period=365
        )

        assert result.is_valid
        assert result.value > 90
        assert "DSO" in caplog.text and "very high" in caplog.text
        assert 'Poor collection efficiency' in result.metadata['interpretation']

    def test_dso_moderate_high_value_warning(self, calculator, caplog):
        """Test DSO with moderately high value triggers warning"""
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=5.0,  # 365 / 5 = 73 days
            days_in_period=365
        )

        assert result.is_valid
        assert 60 < result.value <= 90
        assert "DSO" in caplog.text and "high" in caplog.text
        assert 'Below average collection efficiency' in result.metadata['interpretation']

    def test_dso_low_value_warning(self, calculator, caplog):
        """Test DSO with very low value triggers warning"""
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=30.0,  # 365 / 30 = 12.17 days
            days_in_period=365
        )

        assert result.is_valid
        assert result.value < 15
        assert "DSO" in caplog.text and "very low" in caplog.text

    # =====================
    # Industry Scenarios
    # =====================

    def test_dso_standard_net30_terms(self, calculator):
        """Test DSO for company with standard net-30 payment terms"""
        # Revenue: 3,650,000, Receivables: 300,000
        # Turnover = 3,650,000 / 300,000 = 12.17
        # DSO = 365 / 12.17 = 30 days
        result = calculator.calculate_days_sales_outstanding(
            revenue=3_650_000,
            accounts_receivable=300_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(30.0, rel=0.01)
        assert 'Excellent collection efficiency' in result.metadata['interpretation']

    def test_dso_extended_payment_terms(self, calculator):
        """Test DSO for company with extended payment terms (net-60)"""
        # Revenue: 3,650,000, Receivables: 600,000
        # Turnover = 3,650,000 / 600,000 = 6.08
        # DSO = 365 / 6.08 = 60 days
        result = calculator.calculate_days_sales_outstanding(
            revenue=3_650_000,
            accounts_receivable=600_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(60.0, rel=0.01)
        assert 'Moderate collection efficiency' in result.metadata['interpretation']

    def test_dso_retail_cash_business(self, calculator):
        """Test DSO for retail business with mostly cash sales"""
        # Revenue: 10,000,000, Receivables: 50,000 (minimal credit sales)
        # Turnover = 10,000,000 / 50,000 = 200
        # DSO = 365 / 200 = 1.83 days
        result = calculator.calculate_days_sales_outstanding(
            revenue=10_000_000,
            accounts_receivable=50_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value < 5
        # Very low DSO indicates mostly cash operations

    def test_dso_slow_collections(self, calculator):
        """Test DSO for company with slow collections"""
        # Revenue: 1,200,000, Receivables: 400,000
        # Turnover = 1,200,000 / 400,000 = 3
        # DSO = 365 / 3 = 121.67 days
        result = calculator.calculate_days_sales_outstanding(
            revenue=1_200_000,
            accounts_receivable=400_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value > 90
        assert 'Poor collection efficiency' in result.metadata['interpretation']

    # =====================
    # Metadata Validation
    # =====================

    def test_dso_metadata_completeness(self, calculator):
        """Test that DSO result includes complete metadata"""
        result = calculator.calculate_days_sales_outstanding(
            revenue=1_200_000,
            accounts_receivable=100_000,
            days_in_period=365
        )

        assert result.is_valid
        assert 'receivables_turnover' in result.metadata
        assert 'days_in_period' in result.metadata
        assert 'revenue' in result.metadata
        assert 'accounts_receivable' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata

    def test_dso_calculation_method_provided_turnover(self, calculator):
        """Test calculation method when turnover is provided"""
        result = calculator.calculate_days_sales_outstanding(
            receivables_turnover=12.0,
            days_in_period=365
        )

        assert result.is_valid
        assert 'provided receivables turnover' in result.metadata['calculation_method']

    def test_dso_calculation_method_calculated_turnover(self, calculator):
        """Test calculation method when turnover is calculated"""
        result = calculator.calculate_days_sales_outstanding(
            revenue=1_200_000,
            accounts_receivable=100_000,
            days_in_period=365
        )

        assert result.is_valid
        assert 'calculated from revenue and receivables' in result.metadata['calculation_method']
