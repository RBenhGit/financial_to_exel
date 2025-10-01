"""
Unit Tests for Receivables Turnover Calculation
================================================

Comprehensive unit tests for the calculate_receivables_turnover method covering:
- Standard calculations with different input combinations
- Average receivables calculation (beginning + ending)
- Special cases: zero receivables (cash businesses)
- Input validation and error handling
- Edge cases (negative values, extreme ratios, seasonal patterns)
- Metadata and interpretation validation
"""

import pytest
import math
from core.analysis.engines.financial_calculation_engine import (
    FinancialCalculationEngine,
    CalculationResult
)


class TestReceivablesTurnover:
    """Test suite for Receivables Turnover calculations"""

    @pytest.fixture
    def engine(self):
        """Create a FinancialCalculationEngine instance for testing"""
        return FinancialCalculationEngine()

    # =============================================================================
    # STANDARD CALCULATIONS
    # =============================================================================

    def test_receivables_turnover_with_average_receivables(self, engine):
        """Test receivables turnover calculation with pre-calculated average receivables"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            average_receivables=100000
        )

        assert result.is_valid is True
        assert result.value == 10.0
        assert result.error_message is None
        assert 'revenue' in result.metadata
        assert 'receivables_denominator' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'provided average receivables' in result.metadata['calculation_method']
        assert 'interpretation' in result.metadata

    def test_receivables_turnover_with_beginning_ending_receivables(self, engine):
        """Test receivables turnover with beginning and ending receivables to calculate average"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            beginning_receivables=80000,
            ending_receivables=120000
        )

        assert result.is_valid is True
        assert result.value == 10.0  # 1000000 / ((80000 + 120000) / 2)
        assert result.metadata['receivables_denominator'] == 100000
        assert 'calculated average from beginning and ending receivables' in result.metadata['calculation_method']

    def test_receivables_turnover_with_period_end_receivables(self, engine):
        """Test receivables turnover with single period receivables"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            accounts_receivable=100000
        )

        assert result.is_valid is True
        assert result.value == 10.0
        assert 'period-end receivables' in result.metadata['calculation_method']

    def test_receivables_turnover_priority_average_over_others(self, engine):
        """Test that average_receivables takes priority over other inputs"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            average_receivables=100000,
            beginning_receivables=80000,
            ending_receivables=120000,
            accounts_receivable=110000
        )

        assert result.is_valid is True
        assert result.value == 10.0
        assert result.metadata['receivables_denominator'] == 100000
        assert 'provided average receivables' in result.metadata['calculation_method']

    def test_receivables_turnover_priority_calculated_average_over_period_end(self, engine):
        """Test that calculated average takes priority over period-end receivables"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            beginning_receivables=80000,
            ending_receivables=120000,
            accounts_receivable=110000
        )

        assert result.is_valid is True
        assert result.metadata['receivables_denominator'] == 100000  # Average, not 110000
        assert 'calculated average from beginning and ending receivables' in result.metadata['calculation_method']

    # =============================================================================
    # ZERO RECEIVABLES CASES (CASH BUSINESSES)
    # =============================================================================

    def test_receivables_turnover_zero_receivables_zero_revenue(self, engine):
        """Test zero receivables with zero revenue (unusual but possible)"""
        result = engine.calculate_receivables_turnover(
            revenue=0,
            average_receivables=0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Revenue cannot be zero" in result.error_message

    def test_receivables_turnover_zero_receivables_positive_revenue(self, engine):
        """Test zero receivables with positive revenue (all-cash business)"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            average_receivables=0
        )

        assert result.is_valid is True
        assert result.value == float('inf')
        assert 'Infinite turnover' in result.metadata['interpretation']

    def test_receivables_turnover_cash_business_with_zero_beginning_ending(self, engine):
        """Test cash business scenario with zero beginning and ending receivables"""
        result = engine.calculate_receivables_turnover(
            revenue=5000000,
            beginning_receivables=0,
            ending_receivables=0
        )

        assert result.is_valid is True
        assert result.value == float('inf')

    # =============================================================================
    # EDGE CASES
    # =============================================================================

    def test_receivables_turnover_very_low_ratio(self, engine):
        """Test receivables turnover with very low ratio (slow collections)"""
        result = engine.calculate_receivables_turnover(
            revenue=100000,
            average_receivables=50000
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert 'Very low receivables turnover' in result.metadata['interpretation']

    def test_receivables_turnover_very_high_ratio(self, engine):
        """Test receivables turnover with very high ratio (fast collections)"""
        result = engine.calculate_receivables_turnover(
            revenue=5000000,
            average_receivables=200000
        )

        assert result.is_valid is True
        assert result.value == 25.0
        assert 'Excellent receivables management' in result.metadata['interpretation']

    def test_receivables_turnover_negative_revenue(self, engine):
        """Test handling of negative revenue (returns/refunds)"""
        result = engine.calculate_receivables_turnover(
            revenue=-100000,
            average_receivables=100000
        )

        # Should still calculate but warn
        assert result.is_valid is True
        assert result.value == -1.0

    def test_receivables_turnover_negative_receivables(self, engine):
        """Test handling of negative receivables (credit balances or errors)"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            average_receivables=-100000
        )

        # Should still calculate but warn
        assert result.is_valid is True
        assert result.value == -10.0

    # =============================================================================
    # INPUT VALIDATION
    # =============================================================================

    def test_receivables_turnover_none_revenue(self, engine):
        """Test that None revenue returns error"""
        result = engine.calculate_receivables_turnover(
            revenue=None,
            average_receivables=100000
        )

        assert result.is_valid is False
        assert "Revenue cannot be None" in result.error_message

    def test_receivables_turnover_no_receivables_inputs(self, engine):
        """Test that missing all receivables inputs returns error"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000
        )

        assert result.is_valid is False
        assert "must be provided" in result.error_message

    def test_receivables_turnover_only_beginning_receivables(self, engine):
        """Test that only beginning receivables without ending returns error"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            beginning_receivables=100000
        )

        assert result.is_valid is False
        assert "must be provided" in result.error_message

    def test_receivables_turnover_only_ending_receivables(self, engine):
        """Test that only ending receivables without beginning returns error"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            ending_receivables=100000
        )

        assert result.is_valid is False
        assert "must be provided" in result.error_message

    # =============================================================================
    # METADATA VALIDATION
    # =============================================================================

    def test_receivables_turnover_metadata_completeness(self, engine):
        """Test that all expected metadata fields are present"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            beginning_receivables=80000,
            ending_receivables=120000
        )

        assert result.is_valid is True
        assert 'revenue' in result.metadata
        assert 'receivables_denominator' in result.metadata
        assert 'accounts_receivable' in result.metadata
        assert 'average_receivables' in result.metadata
        assert 'beginning_receivables' in result.metadata
        assert 'ending_receivables' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata

    def test_receivables_turnover_metadata_values(self, engine):
        """Test that metadata contains correct values"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            beginning_receivables=80000,
            ending_receivables=120000,
            accounts_receivable=110000
        )

        assert result.metadata['revenue'] == 1000000
        assert result.metadata['receivables_denominator'] == 100000
        assert result.metadata['beginning_receivables'] == 80000
        assert result.metadata['ending_receivables'] == 120000
        assert result.metadata['accounts_receivable'] == 110000

    # =============================================================================
    # INTERPRETATION TESTS
    # =============================================================================

    def test_receivables_turnover_interpretation_excellent(self, engine):
        """Test interpretation for excellent receivables turnover (>= 12.0)"""
        result = engine.calculate_receivables_turnover(
            revenue=1200000,
            average_receivables=100000
        )

        assert result.is_valid is True
        assert result.value == 12.0
        assert 'Excellent receivables management' in result.metadata['interpretation']

    def test_receivables_turnover_interpretation_strong(self, engine):
        """Test interpretation for strong receivables turnover (>= 8.0)"""
        result = engine.calculate_receivables_turnover(
            revenue=800000,
            average_receivables=100000
        )

        assert result.is_valid is True
        assert result.value == 8.0
        assert 'Strong receivables management' in result.metadata['interpretation']

    def test_receivables_turnover_interpretation_moderate(self, engine):
        """Test interpretation for moderate receivables turnover (>= 6.0)"""
        result = engine.calculate_receivables_turnover(
            revenue=600000,
            average_receivables=100000
        )

        assert result.is_valid is True
        assert result.value == 6.0
        assert 'Moderate receivables management' in result.metadata['interpretation']

    def test_receivables_turnover_interpretation_low(self, engine):
        """Test interpretation for low receivables turnover (>= 4.0)"""
        result = engine.calculate_receivables_turnover(
            revenue=400000,
            average_receivables=100000
        )

        assert result.is_valid is True
        assert result.value == 4.0
        assert 'Low receivables turnover' in result.metadata['interpretation']

    def test_receivables_turnover_interpretation_very_low(self, engine):
        """Test interpretation for very low receivables turnover (< 4.0)"""
        result = engine.calculate_receivables_turnover(
            revenue=200000,
            average_receivables=100000
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert 'Very low receivables turnover' in result.metadata['interpretation']

    # =============================================================================
    # REAL-WORLD SCENARIOS
    # =============================================================================

    def test_receivables_turnover_retail_store(self, engine):
        """Test receivables turnover for typical retail store (mostly cash, some credit)"""
        result = engine.calculate_receivables_turnover(
            revenue=10000000,
            beginning_receivables=500000,
            ending_receivables=600000
        )

        assert result.is_valid is True
        expected_turnover = 10000000 / 550000
        assert abs(result.value - expected_turnover) < 0.01
        assert result.value > 12.0  # Retail typically has high receivables turnover

    def test_receivables_turnover_b2b_manufacturer(self, engine):
        """Test receivables turnover for B2B manufacturer (longer payment terms)"""
        result = engine.calculate_receivables_turnover(
            revenue=20000000,
            beginning_receivables=4000000,
            ending_receivables=4500000
        )

        assert result.is_valid is True
        expected_turnover = 20000000 / 4250000
        assert abs(result.value - expected_turnover) < 0.01
        assert result.value < 6.0  # B2B typically has lower receivables turnover

    def test_receivables_turnover_professional_services(self, engine):
        """Test receivables turnover for professional services (moderate terms)"""
        result = engine.calculate_receivables_turnover(
            revenue=5000000,
            beginning_receivables=600000,
            ending_receivables=700000
        )

        assert result.is_valid is True
        expected_turnover = 5000000 / 650000
        assert abs(result.value - expected_turnover) < 0.01
        assert 6.0 <= result.value <= 10.0  # Professional services typically moderate

    def test_receivables_turnover_restaurant(self, engine):
        """Test receivables turnover for restaurant (all-cash business)"""
        result = engine.calculate_receivables_turnover(
            revenue=2000000,
            average_receivables=0
        )

        assert result.is_valid is True
        assert result.value == float('inf')
        assert 'Infinite turnover' in result.metadata['interpretation']

    def test_receivables_turnover_seasonal_business(self, engine):
        """Test receivables turnover with seasonal variation (holiday retail)"""
        result = engine.calculate_receivables_turnover(
            revenue=15000000,
            beginning_receivables=500000,  # Low after holiday collections
            ending_receivables=2000000     # High during peak season
        )

        assert result.is_valid is True
        expected_turnover = 15000000 / 1250000
        assert abs(result.value - expected_turnover) < 0.01
        assert result.value == 12.0  # Seasonal variation captured in average

    def test_receivables_turnover_construction_company(self, engine):
        """Test receivables turnover for construction company (very long payment terms)"""
        result = engine.calculate_receivables_turnover(
            revenue=30000000,
            beginning_receivables=10000000,
            ending_receivables=12000000
        )

        assert result.is_valid is True
        expected_turnover = 30000000 / 11000000
        assert abs(result.value - expected_turnover) < 0.01
        assert result.value < 4.0  # Construction typically has very low receivables turnover

    # =============================================================================
    # CALCULATION RESULT STRUCTURE
    # =============================================================================

    def test_receivables_turnover_calculation_result_type(self, engine):
        """Test that return type is CalculationResult"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            average_receivables=100000
        )

        assert isinstance(result, CalculationResult)
        assert hasattr(result, 'value')
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'error_message')
        assert hasattr(result, 'metadata')

    def test_receivables_turnover_success_result_structure(self, engine):
        """Test structure of successful calculation result"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            average_receivables=100000
        )

        assert isinstance(result.value, float)
        assert isinstance(result.is_valid, bool)
        assert result.error_message is None
        assert isinstance(result.metadata, dict)

    def test_receivables_turnover_error_result_structure(self, engine):
        """Test structure of error calculation result"""
        result = engine.calculate_receivables_turnover(
            revenue=None,
            average_receivables=100000
        )

        assert result.value == 0.0
        assert result.is_valid is False
        assert isinstance(result.error_message, str)
        assert len(result.error_message) > 0

    def test_receivables_turnover_infinite_result_structure(self, engine):
        """Test structure of infinite turnover result (cash business)"""
        result = engine.calculate_receivables_turnover(
            revenue=1000000,
            average_receivables=0
        )

        assert result.value == float('inf')
        assert result.is_valid is True
        assert result.error_message is None
        assert isinstance(result.metadata, dict)
        assert 'Infinite turnover' in result.metadata['interpretation']
