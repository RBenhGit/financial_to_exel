"""
Unit Tests for Inventory Turnover Calculation
==============================================

Comprehensive unit tests for the calculate_inventory_turnover method covering:
- Standard calculations with different input combinations
- Average inventory calculation (beginning + ending)
- Special cases: zero inventory (service companies, JIT)
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


class TestInventoryTurnover:
    """Test suite for Inventory Turnover calculations"""

    @pytest.fixture
    def engine(self):
        """Create a FinancialCalculationEngine instance for testing"""
        return FinancialCalculationEngine()

    # =============================================================================
    # STANDARD CALCULATIONS
    # =============================================================================

    def test_inventory_turnover_with_average_inventory(self, engine):
        """Test inventory turnover calculation with pre-calculated average inventory"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            average_inventory=200000
        )

        assert result.is_valid is True
        assert result.value == 5.0
        assert result.error_message is None
        assert 'cogs' in result.metadata
        assert 'inventory_denominator' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'provided average inventory' in result.metadata['calculation_method']
        assert 'interpretation' in result.metadata

    def test_inventory_turnover_with_beginning_ending_inventory(self, engine):
        """Test inventory turnover with beginning and ending inventory to calculate average"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            beginning_inventory=150000,
            ending_inventory=250000
        )

        assert result.is_valid is True
        assert result.value == 5.0  # 1000000 / ((150000 + 250000) / 2)
        assert result.metadata['inventory_denominator'] == 200000
        assert 'calculated average from beginning and ending inventory' in result.metadata['calculation_method']

    def test_inventory_turnover_with_period_end_inventory(self, engine):
        """Test inventory turnover with single period inventory"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            inventory=200000
        )

        assert result.is_valid is True
        assert result.value == 5.0
        assert 'period-end inventory' in result.metadata['calculation_method']

    def test_inventory_turnover_priority_average_over_others(self, engine):
        """Test that average_inventory takes priority over other inputs"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            average_inventory=200000,
            beginning_inventory=150000,
            ending_inventory=250000,
            inventory=220000
        )

        assert result.is_valid is True
        assert result.value == 5.0
        assert result.metadata['inventory_denominator'] == 200000
        assert 'provided average inventory' in result.metadata['calculation_method']

    def test_inventory_turnover_priority_calculated_average_over_period_end(self, engine):
        """Test that calculated average takes priority over period-end inventory"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            beginning_inventory=150000,
            ending_inventory=250000,
            inventory=220000
        )

        assert result.is_valid is True
        assert result.metadata['inventory_denominator'] == 200000  # Average, not 220000
        assert 'calculated average from beginning and ending inventory' in result.metadata['calculation_method']

    # =============================================================================
    # ZERO INVENTORY CASES (SERVICE COMPANIES / JIT)
    # =============================================================================

    def test_inventory_turnover_zero_inventory_zero_cogs(self, engine):
        """Test zero inventory with zero COGS (service company)"""
        result = engine.calculate_inventory_turnover(
            cogs=0,
            average_inventory=0
        )

        assert result.is_valid is True
        assert result.value == 0.0
        assert 'Service company or no inventory model' in result.metadata['interpretation']

    def test_inventory_turnover_zero_inventory_positive_cogs(self, engine):
        """Test zero inventory with positive COGS (JIT or service business)"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            average_inventory=0
        )

        assert result.is_valid is True
        assert result.value == float('inf')
        assert 'Infinite turnover' in result.metadata['interpretation']

    def test_inventory_turnover_service_company_with_zero_beginning_ending(self, engine):
        """Test service company scenario with zero beginning and ending inventory"""
        result = engine.calculate_inventory_turnover(
            cogs=5000000,
            beginning_inventory=0,
            ending_inventory=0
        )

        assert result.is_valid is True
        assert result.value == float('inf')

    # =============================================================================
    # EDGE CASES
    # =============================================================================

    def test_inventory_turnover_very_low_ratio(self, engine):
        """Test inventory turnover with very low ratio (slow-moving inventory)"""
        result = engine.calculate_inventory_turnover(
            cogs=100000,
            average_inventory=200000
        )

        assert result.is_valid is True
        assert result.value == 0.5
        assert 'Very low inventory turnover' in result.metadata['interpretation']

    def test_inventory_turnover_very_high_ratio(self, engine):
        """Test inventory turnover with very high ratio (fast-moving/JIT)"""
        result = engine.calculate_inventory_turnover(
            cogs=5000000,
            average_inventory=200000
        )

        assert result.is_valid is True
        assert result.value == 25.0
        assert 'Excellent inventory management' in result.metadata['interpretation']

    def test_inventory_turnover_negative_cogs(self, engine):
        """Test handling of negative COGS (unusual but possible with returns)"""
        result = engine.calculate_inventory_turnover(
            cogs=-100000,
            average_inventory=200000
        )

        # Should still calculate but warn
        assert result.is_valid is True
        assert result.value == -0.5

    def test_inventory_turnover_negative_inventory(self, engine):
        """Test handling of negative inventory (write-downs or errors)"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            average_inventory=-200000
        )

        # Should still calculate but warn
        assert result.is_valid is True
        assert result.value == -5.0

    # =============================================================================
    # INPUT VALIDATION
    # =============================================================================

    def test_inventory_turnover_none_cogs(self, engine):
        """Test that None COGS returns error"""
        result = engine.calculate_inventory_turnover(
            cogs=None,
            average_inventory=200000
        )

        assert result.is_valid is False
        assert "COGS cannot be None" in result.error_message

    def test_inventory_turnover_no_inventory_inputs(self, engine):
        """Test that missing all inventory inputs returns error"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000
        )

        assert result.is_valid is False
        assert "must be provided" in result.error_message

    def test_inventory_turnover_only_beginning_inventory(self, engine):
        """Test that only beginning inventory without ending returns error"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            beginning_inventory=200000
        )

        assert result.is_valid is False
        assert "must be provided" in result.error_message

    def test_inventory_turnover_only_ending_inventory(self, engine):
        """Test that only ending inventory without beginning returns error"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            ending_inventory=200000
        )

        assert result.is_valid is False
        assert "must be provided" in result.error_message

    # =============================================================================
    # METADATA VALIDATION
    # =============================================================================

    def test_inventory_turnover_metadata_completeness(self, engine):
        """Test that all expected metadata fields are present"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            beginning_inventory=150000,
            ending_inventory=250000
        )

        assert result.is_valid is True
        assert 'cogs' in result.metadata
        assert 'inventory_denominator' in result.metadata
        assert 'inventory' in result.metadata
        assert 'average_inventory' in result.metadata
        assert 'beginning_inventory' in result.metadata
        assert 'ending_inventory' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata

    def test_inventory_turnover_metadata_values(self, engine):
        """Test that metadata contains correct values"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            beginning_inventory=150000,
            ending_inventory=250000,
            inventory=220000
        )

        assert result.metadata['cogs'] == 1000000
        assert result.metadata['inventory_denominator'] == 200000
        assert result.metadata['beginning_inventory'] == 150000
        assert result.metadata['ending_inventory'] == 250000
        assert result.metadata['inventory'] == 220000

    # =============================================================================
    # INTERPRETATION TESTS
    # =============================================================================

    def test_inventory_turnover_interpretation_excellent(self, engine):
        """Test interpretation for excellent inventory turnover (>= 12.0)"""
        result = engine.calculate_inventory_turnover(
            cogs=2400000,
            average_inventory=200000
        )

        assert result.is_valid is True
        assert result.value == 12.0
        assert 'Excellent inventory management' in result.metadata['interpretation']

    def test_inventory_turnover_interpretation_strong(self, engine):
        """Test interpretation for strong inventory turnover (>= 6.0)"""
        result = engine.calculate_inventory_turnover(
            cogs=1200000,
            average_inventory=200000
        )

        assert result.is_valid is True
        assert result.value == 6.0
        assert 'Strong inventory management' in result.metadata['interpretation']

    def test_inventory_turnover_interpretation_moderate(self, engine):
        """Test interpretation for moderate inventory turnover (>= 4.0)"""
        result = engine.calculate_inventory_turnover(
            cogs=800000,
            average_inventory=200000
        )

        assert result.is_valid is True
        assert result.value == 4.0
        assert 'Moderate inventory management' in result.metadata['interpretation']

    def test_inventory_turnover_interpretation_low(self, engine):
        """Test interpretation for low inventory turnover (>= 2.0)"""
        result = engine.calculate_inventory_turnover(
            cogs=400000,
            average_inventory=200000
        )

        assert result.is_valid is True
        assert result.value == 2.0
        assert 'Low inventory turnover' in result.metadata['interpretation']

    def test_inventory_turnover_interpretation_very_low(self, engine):
        """Test interpretation for very low inventory turnover (< 2.0)"""
        result = engine.calculate_inventory_turnover(
            cogs=200000,
            average_inventory=200000
        )

        assert result.is_valid is True
        assert result.value == 1.0
        assert 'Very low inventory turnover' in result.metadata['interpretation']

    # =============================================================================
    # REAL-WORLD SCENARIOS
    # =============================================================================

    def test_inventory_turnover_grocery_store(self, engine):
        """Test inventory turnover for typical grocery store (very high turnover)"""
        result = engine.calculate_inventory_turnover(
            cogs=50000000,
            beginning_inventory=2000000,
            ending_inventory=2200000
        )

        assert result.is_valid is True
        expected_turnover = 50000000 / 2100000
        assert abs(result.value - expected_turnover) < 0.01
        assert result.value > 12.0  # Groceries typically have very high turnover

    def test_inventory_turnover_jewelry_store(self, engine):
        """Test inventory turnover for typical jewelry store (low turnover)"""
        result = engine.calculate_inventory_turnover(
            cogs=2000000,
            beginning_inventory=5000000,
            ending_inventory=5500000
        )

        assert result.is_valid is True
        expected_turnover = 2000000 / 5250000
        assert abs(result.value - expected_turnover) < 0.01
        assert result.value < 1.0  # Jewelry typically has low turnover

    def test_inventory_turnover_auto_parts_retailer(self, engine):
        """Test inventory turnover for auto parts retailer (moderate turnover)"""
        result = engine.calculate_inventory_turnover(
            cogs=10000000,
            beginning_inventory=2000000,
            ending_inventory=2400000
        )

        assert result.is_valid is True
        expected_turnover = 10000000 / 2200000
        assert abs(result.value - expected_turnover) < 0.01
        assert 4.0 <= result.value <= 6.0  # Auto parts typically moderate

    def test_inventory_turnover_consulting_firm(self, engine):
        """Test inventory turnover for consulting firm (no inventory)"""
        result = engine.calculate_inventory_turnover(
            cogs=0,
            average_inventory=0
        )

        assert result.is_valid is True
        assert result.value == 0.0
        assert 'Service company' in result.metadata['interpretation']

    def test_inventory_turnover_seasonal_business(self, engine):
        """Test inventory turnover with seasonal variation (toy store)"""
        result = engine.calculate_inventory_turnover(
            cogs=12000000,
            beginning_inventory=1000000,  # Low after holiday season
            ending_inventory=5000000      # High before holiday season
        )

        assert result.is_valid is True
        expected_turnover = 12000000 / 3000000
        assert abs(result.value - expected_turnover) < 0.01
        assert result.value == 4.0  # Seasonal variation captured in average

    # =============================================================================
    # CALCULATION RESULT STRUCTURE
    # =============================================================================

    def test_inventory_turnover_calculation_result_type(self, engine):
        """Test that return type is CalculationResult"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            average_inventory=200000
        )

        assert isinstance(result, CalculationResult)
        assert hasattr(result, 'value')
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'error_message')
        assert hasattr(result, 'metadata')

    def test_inventory_turnover_success_result_structure(self, engine):
        """Test structure of successful calculation result"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            average_inventory=200000
        )

        assert isinstance(result.value, float)
        assert isinstance(result.is_valid, bool)
        assert result.error_message is None
        assert isinstance(result.metadata, dict)

    def test_inventory_turnover_error_result_structure(self, engine):
        """Test structure of error calculation result"""
        result = engine.calculate_inventory_turnover(
            cogs=None,
            average_inventory=200000
        )

        assert result.value == 0.0
        assert result.is_valid is False
        assert isinstance(result.error_message, str)
        assert len(result.error_message) > 0

    def test_inventory_turnover_infinite_result_structure(self, engine):
        """Test structure of infinite turnover result (JIT/service)"""
        result = engine.calculate_inventory_turnover(
            cogs=1000000,
            average_inventory=0
        )

        assert result.value == float('inf')
        assert result.is_valid is True
        assert result.error_message is None
        assert isinstance(result.metadata, dict)
        assert 'Infinite turnover' in result.metadata['interpretation']
