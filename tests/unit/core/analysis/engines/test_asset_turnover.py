"""
Unit Tests for Asset Turnover Calculation
==========================================

Comprehensive unit tests for the calculate_asset_turnover method covering:
- Standard calculations with different input combinations
- Average assets calculation (beginning + ending)
- Input validation and error handling
- Edge cases (zero assets, negative values, extreme ratios)
- Metadata and interpretation validation
"""

import pytest
from core.analysis.engines.financial_calculation_engine import (
    FinancialCalculationEngine,
    CalculationResult
)


class TestAssetTurnover:
    """Test suite for Asset Turnover calculations"""

    @pytest.fixture
    def engine(self):
        """Create a FinancialCalculationEngine instance for testing"""
        return FinancialCalculationEngine()

    # =============================================================================
    # STANDARD CALCULATIONS
    # =============================================================================

    def test_asset_turnover_with_average_assets(self, engine):
        """Test asset turnover calculation with pre-calculated average assets"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            average_assets=500000
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert result.error_message is None
        assert 'revenue' in result.metadata
        assert 'assets_denominator' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'provided average assets' in result.metadata['calculation_method']
        assert 'interpretation' in result.metadata

    def test_asset_turnover_with_beginning_ending_assets(self, engine):
        """Test asset turnover with beginning and ending assets to calculate average"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            beginning_assets=400000,
            ending_assets=600000
        )

        assert result.is_valid is True
        assert result.value == 2.0  # 1000000 / ((400000 + 600000) / 2)
        assert result.metadata['assets_denominator'] == 500000
        assert 'calculated average from beginning and ending assets' in result.metadata['calculation_method']

    def test_asset_turnover_with_total_assets(self, engine):
        """Test asset turnover with single period total assets"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            total_assets=500000
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert 'period-end assets' in result.metadata['calculation_method']

    def test_asset_turnover_priority_average_over_others(self, engine):
        """Test that average_assets takes priority over other inputs"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            average_assets=500000,
            beginning_assets=400000,
            ending_assets=600000,
            total_assets=550000
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert result.metadata['assets_denominator'] == 500000
        assert 'provided average assets' in result.metadata['calculation_method']

    def test_asset_turnover_priority_calculated_average_over_total(self, engine):
        """Test that calculated average takes priority over total_assets"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            beginning_assets=400000,
            ending_assets=600000,
            total_assets=550000
        )

        assert result.is_valid is True
        assert result.metadata['assets_denominator'] == 500000  # Average, not 550000
        assert 'calculated average from beginning and ending assets' in result.metadata['calculation_method']

    # =============================================================================
    # EDGE CASES
    # =============================================================================

    def test_asset_turnover_low_ratio(self, engine):
        """Test asset turnover with very low ratio (asset-intensive business)"""
        result = engine.calculate_asset_turnover(
            revenue=100000,
            average_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.1
        assert 'Very low asset efficiency' in result.metadata['interpretation']

    def test_asset_turnover_high_ratio(self, engine):
        """Test asset turnover with very high ratio (asset-light business)"""
        result = engine.calculate_asset_turnover(
            revenue=5000000,
            average_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 5.0
        assert 'Excellent asset efficiency' in result.metadata['interpretation']

    def test_asset_turnover_moderate_ratio(self, engine):
        """Test asset turnover with moderate ratio"""
        result = engine.calculate_asset_turnover(
            revenue=750000,
            average_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.75
        assert 'Moderate asset efficiency' in result.metadata['interpretation']

    def test_asset_turnover_with_zero_revenue(self, engine):
        """Test that zero revenue returns error"""
        result = engine.calculate_asset_turnover(
            revenue=0,
            average_assets=1000000
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Revenue cannot be zero" in result.error_message

    def test_asset_turnover_with_zero_assets(self, engine):
        """Test that zero assets returns error"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            average_assets=0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Assets denominator cannot be zero" in result.error_message

    def test_asset_turnover_with_negative_revenue(self, engine):
        """Test handling of negative revenue (unusual but possible)"""
        result = engine.calculate_asset_turnover(
            revenue=-100000,
            average_assets=1000000
        )

        # Should still calculate but warn
        assert result.is_valid is True
        assert result.value == -0.1

    def test_asset_turnover_with_negative_assets(self, engine):
        """Test handling of negative assets (distressed company)"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            average_assets=-500000
        )

        # Should still calculate but warn
        assert result.is_valid is True
        assert result.value == -2.0

    # =============================================================================
    # INPUT VALIDATION
    # =============================================================================

    def test_asset_turnover_none_revenue(self, engine):
        """Test that None revenue returns error"""
        result = engine.calculate_asset_turnover(
            revenue=None,
            average_assets=1000000
        )

        assert result.is_valid is False
        assert "Revenue cannot be None" in result.error_message

    def test_asset_turnover_no_asset_inputs(self, engine):
        """Test that missing all asset inputs returns error"""
        result = engine.calculate_asset_turnover(
            revenue=1000000
        )

        assert result.is_valid is False
        assert "must be provided" in result.error_message

    def test_asset_turnover_only_beginning_assets(self, engine):
        """Test that only beginning assets without ending returns error"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            beginning_assets=500000
        )

        assert result.is_valid is False
        assert "must be provided" in result.error_message

    def test_asset_turnover_only_ending_assets(self, engine):
        """Test that only ending assets without beginning returns error"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            ending_assets=500000
        )

        assert result.is_valid is False
        assert "must be provided" in result.error_message

    # =============================================================================
    # METADATA VALIDATION
    # =============================================================================

    def test_asset_turnover_metadata_completeness(self, engine):
        """Test that all expected metadata fields are present"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            beginning_assets=400000,
            ending_assets=600000
        )

        assert result.is_valid is True
        assert 'revenue' in result.metadata
        assert 'assets_denominator' in result.metadata
        assert 'total_assets' in result.metadata
        assert 'average_assets' in result.metadata
        assert 'beginning_assets' in result.metadata
        assert 'ending_assets' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata

    def test_asset_turnover_metadata_values(self, engine):
        """Test that metadata contains correct values"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            beginning_assets=400000,
            ending_assets=600000,
            total_assets=550000
        )

        assert result.metadata['revenue'] == 1000000
        assert result.metadata['assets_denominator'] == 500000
        assert result.metadata['beginning_assets'] == 400000
        assert result.metadata['ending_assets'] == 600000
        assert result.metadata['total_assets'] == 550000

    # =============================================================================
    # INTERPRETATION TESTS
    # =============================================================================

    def test_asset_turnover_interpretation_excellent(self, engine):
        """Test interpretation for excellent asset turnover (>= 2.0)"""
        result = engine.calculate_asset_turnover(
            revenue=2000000,
            average_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert 'Excellent asset efficiency' in result.metadata['interpretation']

    def test_asset_turnover_interpretation_strong(self, engine):
        """Test interpretation for strong asset turnover (>= 1.0)"""
        result = engine.calculate_asset_turnover(
            revenue=1500000,
            average_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 1.5
        assert 'Strong asset efficiency' in result.metadata['interpretation']

    def test_asset_turnover_interpretation_moderate(self, engine):
        """Test interpretation for moderate asset turnover (>= 0.5)"""
        result = engine.calculate_asset_turnover(
            revenue=750000,
            average_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.75
        assert 'Moderate asset efficiency' in result.metadata['interpretation']

    def test_asset_turnover_interpretation_low(self, engine):
        """Test interpretation for low asset turnover (>= 0.25)"""
        result = engine.calculate_asset_turnover(
            revenue=300000,
            average_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.3
        assert 'Low asset efficiency' in result.metadata['interpretation']

    def test_asset_turnover_interpretation_very_low(self, engine):
        """Test interpretation for very low asset turnover (< 0.25)"""
        result = engine.calculate_asset_turnover(
            revenue=100000,
            average_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.1
        assert 'Very low asset efficiency' in result.metadata['interpretation']

    # =============================================================================
    # REAL-WORLD SCENARIOS
    # =============================================================================

    def test_asset_turnover_retail_company(self, engine):
        """Test asset turnover for typical retail company (high turnover)"""
        result = engine.calculate_asset_turnover(
            revenue=50000000,
            beginning_assets=20000000,
            ending_assets=22000000
        )

        assert result.is_valid is True
        expected_turnover = 50000000 / 21000000
        assert abs(result.value - expected_turnover) < 0.01
        assert result.value > 2.0  # Retail typically has high asset turnover

    def test_asset_turnover_utility_company(self, engine):
        """Test asset turnover for typical utility company (low turnover)"""
        result = engine.calculate_asset_turnover(
            revenue=5000000,
            beginning_assets=50000000,
            ending_assets=52000000
        )

        assert result.is_valid is True
        expected_turnover = 5000000 / 51000000
        assert abs(result.value - expected_turnover) < 0.01
        assert result.value < 0.5  # Utilities typically have low asset turnover

    def test_asset_turnover_tech_company(self, engine):
        """Test asset turnover for typical tech company (moderate-high turnover)"""
        result = engine.calculate_asset_turnover(
            revenue=100000000,
            beginning_assets=60000000,
            ending_assets=70000000
        )

        assert result.is_valid is True
        expected_turnover = 100000000 / 65000000
        assert abs(result.value - expected_turnover) < 0.01
        assert 1.0 <= result.value <= 2.0  # Tech typically moderate to high

    # =============================================================================
    # CALCULATION RESULT STRUCTURE
    # =============================================================================

    def test_asset_turnover_calculation_result_type(self, engine):
        """Test that return type is CalculationResult"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            average_assets=500000
        )

        assert isinstance(result, CalculationResult)
        assert hasattr(result, 'value')
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'error_message')
        assert hasattr(result, 'metadata')

    def test_asset_turnover_success_result_structure(self, engine):
        """Test structure of successful calculation result"""
        result = engine.calculate_asset_turnover(
            revenue=1000000,
            average_assets=500000
        )

        assert isinstance(result.value, float)
        assert isinstance(result.is_valid, bool)
        assert result.error_message is None
        assert isinstance(result.metadata, dict)

    def test_asset_turnover_error_result_structure(self, engine):
        """Test structure of error calculation result"""
        result = engine.calculate_asset_turnover(
            revenue=0,
            average_assets=500000
        )

        assert result.value == 0.0
        assert result.is_valid is False
        assert isinstance(result.error_message, str)
        assert len(result.error_message) > 0
